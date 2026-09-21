"""Exercise installer filesystem transitions with only external commands faked."""
import json
from pathlib import Path
import runpy
import shutil
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
NAME = "chatgpt-codex-bridge"


@pytest.fixture
def installation(tmp_path, monkeypatch):
    task_home = tmp_path / "user with spaces"
    helpers = task_home / ".codex/skills/.system/plugin-creator/scripts"
    helpers.mkdir(parents=True)
    for script in ("create_basic_plugin.py", "read_marketplace_name.py", "update_plugin_cachebuster.py"):
        (helpers / script).write_text("# External helper fixture\n")
    dest = task_home / "plugins" / NAME
    dest.mkdir(parents=True)
    (dest / "GENERATED.txt").write_text("managed old installation\n")
    (dest / "old-file.txt").write_text("keep this working version\n")
    built = dest / "vendor/codex-with-chatgpt/dist/cli/index.js"
    built.parent.mkdir(parents=True)
    built.write_text("old full executable\n")
    market = task_home / ".agents/plugins/marketplace.json"
    market.parent.mkdir(parents=True)
    market.write_text(json.dumps({"name": "test-market", "plugins": [
        {"name": NAME, "source": {"source": "local", "path": "./plugins/" + NAME}},
        {"name": "unrelated", "source": {"source": "local", "path": "./plugins/unrelated"}},
    ]}))
    original_market = market.read_bytes()
    calls = []
    failures = {"setup": False, "register": 0, "helper": False, "cli": False}
    monkeypatch.setattr(Path, "home", lambda: task_home)
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    monkeypatch.setattr("shutil.which", lambda name: "/fixture-bin/" + name)

    def run(cmd, **kwargs):
        calls.append([str(x) for x in cmd])
        if cmd[0] == "/fixture-bin/codex":
            if "--help" in cmd:
                if failures["cli"]:
                    raise subprocess.CalledProcessError(2, cmd)
            elif cmd[1:3] == ["plugin", "add"] and failures["register"]:
                failures["register"] -= 1
                raise subprocess.CalledProcessError(1, cmd)
        elif len(cmd) > 1 and Path(cmd[1]).name == "setup.py":
            if failures["setup"]:
                raise subprocess.CalledProcessError(1, cmd)
            if cmd[-1] == "full":
                artifact = Path(cmd[1]).parent.parent / "vendor/codex-with-chatgpt/dist/cli/index.js"
                artifact.parent.mkdir(parents=True, exist_ok=True)
                artifact.write_text("new full executable\n")
        elif len(cmd) > 1 and Path(cmd[1]).name == "update_plugin_cachebuster.py":
            if failures["helper"]:
                raise subprocess.CalledProcessError(1, cmd)
        elif len(cmd) > 1 and Path(cmd[1]).name == "create_basic_plugin.py":
            path = Path(cmd[cmd.index("--marketplace-path") + 1])
            data = json.loads(path.read_text()) if path.exists() else {"name": "test-market", "plugins": []}
            data["plugins"].append({"name": NAME, "source": {"source": "local", "path": "./plugins/" + NAME}})
            path.write_text(json.dumps(data))
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    def output(cmd, **kwargs):
        calls.append([str(x) for x in cmd])
        return "test-market\n"

    monkeypatch.setattr(subprocess, "run", run)
    monkeypatch.setattr(subprocess, "check_output", output)

    def invoke(*args):
        monkeypatch.setattr(sys, "argv", ["install_plugin.py", *args])
        runpy.run_path(str(ROOT / "scripts/install_plugin.py"), run_name="__main__")

    return {
        "dest": dest, "market": market, "original_market": original_market,
        "helpers": helpers, "calls": calls, "failures": failures, "invoke": invoke,
    }


def assert_old_intact(case):
    assert (case["dest"] / "old-file.txt").read_text() == "keep this working version\n"
    assert (case["dest"] / "vendor/codex-with-chatgpt/dist/cli/index.js").read_text() == "old full executable\n"
    assert case["market"].read_bytes() == case["original_market"]


@pytest.mark.parametrize("failure", ["setup", "helper", "cli"])
def test_failure_before_switch_preserves_existing_full(installation, failure):
    installation["failures"][failure] = True
    with pytest.raises((SystemExit, subprocess.CalledProcessError, RuntimeError)):
        installation["invoke"]()
    assert_old_intact(installation)


def test_registration_failure_restores_and_reregisters_old_full(installation):
    installation["failures"]["register"] = 1
    with pytest.raises((SystemExit, subprocess.CalledProcessError, RuntimeError)):
        installation["invoke"]()
    assert_old_intact(installation)
    registrations = [c for c in installation["calls"] if c[1:3] == ["plugin", "add"] and "--help" not in c]
    assert len(registrations) == 2


def test_retry_auto_after_setup_failure_does_not_downgrade(installation):
    installation["failures"]["setup"] = True
    with pytest.raises((SystemExit, subprocess.CalledProcessError, RuntimeError)):
        installation["invoke"]()
    installation["failures"]["setup"] = False
    installation["invoke"]()
    assert (installation["dest"] / "vendor/codex-with-chatgpt/dist/cli/index.js").read_text() == "new full executable\n"


def test_missing_late_helper_fails_before_replacing_installation(installation):
    (installation["helpers"] / "update_plugin_cachebuster.py").unlink()
    with pytest.raises((SystemExit, subprocess.CalledProcessError, RuntimeError)):
        installation["invoke"]()
    assert_old_intact(installation)


def test_success_preserves_full_and_keeps_recoverable_backup(installation, capsys):
    installation["invoke"]()
    assert not (installation["dest"] / "old-file.txt").exists()
    assert (installation["dest"] / "vendor/codex-with-chatgpt/dist/cli/index.js").exists()
    assert installation["market"].read_bytes() == installation["original_market"]
    assert 'backup' in capsys.readouterr().out.lower()


def test_explicit_lite_is_the_only_requested_downgrade(installation):
    installation["invoke"]("--mode", "lite")
    assert not (installation["dest"] / "vendor/codex-with-chatgpt/dist").exists()


def test_fresh_install_stages_marketplace_then_registers(installation):
    shutil.rmtree(installation["dest"])
    installation["market"].unlink()
    installation["invoke"]()
    assert json.loads((installation["dest"] / "INSTALLATION.json").read_text())["mode"] == "lite"
    assert json.loads(installation["market"].read_text())["plugins"][0]["name"] == NAME


def test_fresh_registration_failure_restores_absent_marketplace(installation):
    shutil.rmtree(installation["dest"])
    installation["market"].unlink()
    installation["failures"]["register"] = 1
    with pytest.raises(SystemExit, match="partial host registration"):
        installation["invoke"]()
    assert not installation["dest"].exists()
    assert not installation["market"].exists()


def test_failed_reregistration_reports_incomplete_recovery(installation):
    installation["failures"]["register"] = 2
    with pytest.raises(SystemExit, match="recovery incomplete"):
        installation["invoke"]()
    assert_old_intact(installation)


def test_saved_full_mode_survives_missing_build(installation):
    (installation["dest"] / "INSTALLATION.json").write_text('{"mode":"full"}')
    shutil.rmtree(installation["dest"] / "vendor/codex-with-chatgpt/dist")
    installation["invoke"]()
    assert (installation["dest"] / "vendor/codex-with-chatgpt/dist/cli/index.js").exists()


def test_unmanaged_directory_is_not_replaced(installation):
    (installation["dest"] / "GENERATED.txt").unlink()
    with pytest.raises(SystemExit, match="unmanaged"):
        installation["invoke"]()
    assert_old_intact(installation)

"""Project-bound passthrough to the pinned, unmodified upstream live backend."""
from __future__ import annotations
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from bridge import Store, DEFAULT_STATE
ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "vendor/codex-with-chatgpt"
ALLOWED = {
    "doctor", "help", "logs", "pair", "prefs", "record", "restart",
    "sandbox-allow", "session", "setup", "start", "status", "stop",
    "tunnel", "unpair", "update-check", "workspace",
}

def command(store, project, args):
    args = list(args)
    if not args or args[0] not in ALLOWED:
        raise ValueError("unsupported backend command")
    if any(x in {"-w", "--workspace"} or x.startswith("--workspace=") or (x.startswith("-w") and not x.startswith("--")) for x in args):
        raise ValueError("workspace is fixed by the bridge project registration")
    root = Path(store.config()["projects"][project]["root"]).resolve(strict=True)
    node = shutil.which("node")
    if not node or not (BACKEND / "dist/cli/index.js").is_file():
        raise ValueError("Full backend is not installed; run python3 scripts/setup.py --mode full")
    env = os.environ.copy()
    env["C2C_STATE_DIR"] = str(store.state / "full")
    env["PATH"] = str(store.state / "runtime/bin") + os.pathsep + env.get("PATH", "")
    return [node, str(BACKEND / "bin/c2c.js"), *args, "--workspace", str(root)], root, env

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--state", default=str(DEFAULT_STATE));p.add_argument("--project",required=True)
    p.add_argument("args", nargs=argparse.REMAINDER)
    a=p.parse_args();args=a.args[1:] if a.args[:1]==["--"] else a.args
    try:
        store=Store(a.state)
        cmd,cwd,env=command(store,a.project,args)
        raise SystemExit(subprocess.run(cmd,cwd=cwd,env=env).returncode)
    except (ValueError, KeyError, OSError) as exc:
        p.exit(1, f"full: {exc}\n")
if __name__=="__main__":main()

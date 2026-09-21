import json
from pathlib import Path
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("suffix", [".zip", ".sha256"])
def test_release_refuses_existing_versioned_artifact(tmp_path, suffix):
    version = json.loads((ROOT / "plugin.json").read_text())["version"]
    existing = tmp_path / ("chatgpt-codex-bridge-" + version + suffix)
    existing.write_bytes(b"immutable published artifact\n")
    result = subprocess.run([sys.executable, str(ROOT / "scripts/release.py"),
                             "--output", str(tmp_path)], capture_output=True, text=True)
    assert result.returncode != 0
    assert "refusing to overwrite" in result.stderr.lower()
    assert existing.read_bytes() == b"immutable published artifact\n"

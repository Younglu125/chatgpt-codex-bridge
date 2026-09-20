"""Install only the dependencies for the selected mode; no login or public server."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import platform
import shutil
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--mode",choices=["lite","snapshot-mcp","full"],default="lite")
    a=p.parse_args()
    if sys.version_info < (3,12): p.error("Python 3.12+ required; install it before setup")
    if platform.system() not in {"Darwin","Linux"}: p.error("Supported: macOS / Linux / Windows through WSL2. Native Windows is not yet supported.")
    if a.mode=="snapshot-mcp":
        env=ROOT/".venv"
        if not (env/"bin/python").exists():subprocess.run([sys.executable,"-m","venv",str(env)],check=True)
        subprocess.run([str(env/"bin/python"),"-m","pip","install","mcp==1.30.0"],check=True)
    if a.mode=="full":
        node,npm=shutil.which("node"),shutil.which("npm")
        if not node or not npm:p.error("Full requires Node.js >=20 and npm")
        version=subprocess.check_output([node,"--version"],text=True).strip()
        if int(version.lstrip("v").split(".")[0])<20:p.error("Node.js >=20 required")
        backend=ROOT/"vendor/codex-with-chatgpt"
        subprocess.run([npm,"ci","--ignore-scripts","--no-audit","--no-fund"],cwd=backend,check=True)
        subprocess.run([npm,"run","build"],cwd=backend,check=True)
    print(json.dumps({"mode":a.mode,"local_setup":"ready","native_tools":"verify in current task", "chatgpt_connection":"not tested by installer","public_server_started":False},indent=2))
if __name__=="__main__":main()

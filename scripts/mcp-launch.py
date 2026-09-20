"""Optional portable stdio launcher; Lite never starts this process."""
import os
from pathlib import Path
import sys
root=Path(__file__).resolve().parents[1]
python=root/".venv/bin/python"
if not python.exists():
    raise SystemExit("Run python3 scripts/setup.py --mode snapshot-mcp in the installed plugin first")
os.execv(str(python),[str(python),str(root/"server.py"),*sys.argv[1:]])

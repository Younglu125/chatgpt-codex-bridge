"""Read-only readiness report. Local readiness does not prove ChatGPT access."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import platform
import shutil
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from bridge import Store, DEFAULT_STATE
p=argparse.ArgumentParser(description=__doc__);p.add_argument("--state",default=str(DEFAULT_STATE));a=p.parse_args()
s=Store(a.state);root=Path(__file__).resolve().parents[1]
print(json.dumps({
 "python_supported":sys.version_info >= (3,12),
 "platform_supported":platform.system() in {"Darwin","Linux"},
 "platform":platform.system(),
 "lite_dependencies":"Python standard library only",
 "snapshot_mcp_installed":importlib.util.find_spec("mcp") is not None,
 "full_built":(root/"vendor/codex-with-chatgpt/dist/cli/index.js").is_file(),
 "node":bool(shutil.which("node")), "cloudflared":bool(shutil.which("cloudflared") or (s.state/"runtime/bin/cloudflared").is_file()),
 "projects":{k:{"exists":Path(v["root"]).is_dir(),"target_bound":bool(v.get("target",s.config().get("target")))} for k,v in s.config()["projects"].items()},
 "pending_jobs":[{"id":j["id"],"project":j["project"],"state":j["state"]} for j in s.pending()],
 "native_tools":"unknown: discover list/read/send in current task; wait may not support ChatGPT",
 "browser":"unknown: inspect available browser tools and signed-in ordinary chat",
 "remote_mcp":"unknown: require real ChatGPT tool invocation returning correct workspace identity",
 "quota_attribution":"unmeasured"
},ensure_ascii=False,indent=2))

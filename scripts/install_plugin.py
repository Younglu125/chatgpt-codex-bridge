"""Install in the default personal marketplace using official local helpers."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from package_plugin import build

name='chatgpt-codex-bridge'
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--mode',choices=['auto','lite','full'],default='auto',
               help='auto preserves a previously built Full installation; full installs it now')
a=p.parse_args()
codex_home=Path(os.environ.get('CODEX_HOME',str(Path.home()/'.codex')))
helper=codex_home/'skills/.system/plugin-creator/scripts'
market=Path.home()/'.agents/plugins/marketplace.json'
dest=Path.home()/'plugins'/name
codex=shutil.which('codex')
if not codex:raise SystemExit('Codex CLI is required for installation; use your supported plugin UI otherwise.')
if not (helper/'create_basic_plugin.py').is_file():raise SystemExit('Official plugin-creator helper unavailable. Use the release marketplace following README; do not invent a successful install.')
market_name=None
if market.exists():
    market_name=subprocess.check_output([sys.executable,str(helper/'read_marketplace_name.py')],text=True).strip()
    existing=next((x for x in json.loads(market.read_text())['plugins'] if x['name']==name),None)
    if existing and existing.get('source',{}).get('path') != './plugins/'+name:
        raise SystemExit('Existing marketplace entry points elsewhere; resolve it before replacing any package.')
else:existing=None
if not existing:
    # Scaffold uses the supported official helper; preserve it for a reversible generated replacement.
    if dest.exists():raise SystemExit('Unregistered destination already exists; choose the release marketplace instead.')
    subprocess.run([sys.executable,str(helper/'create_basic_plugin.py'),name,'--with-marketplace'],check=True)
    (dest/'GENERATED.txt').write_text('Generated scaffold, replace with complete bridge package.\n')
had_full=(dest/'vendor/codex-with-chatgpt/dist/cli/index.js').is_file()
install_full=a.mode=='full' or (a.mode=='auto' and had_full)
print(json.dumps(build(dest),indent=2))
if install_full:
    subprocess.run([sys.executable,str(dest/'scripts/setup.py'),'--mode','full'],check=True)
subprocess.run([sys.executable,str(helper/'update_plugin_cachebuster.py'),str(dest)],check=True)
market_name=subprocess.check_output([sys.executable,str(helper/'read_marketplace_name.py')],text=True).strip()
subprocess.run([codex,'plugin','add',name+'@'+market_name],check=True)
print('Installed '+('Full' if install_full else 'Lite')+' package. Open a new task to load the updated skill.')

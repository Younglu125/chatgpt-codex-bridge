"""Make a ZIP plus checksums and a repository marketplace; never publish remotely."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import tempfile
from package_plugin import ROOT, build

p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
a.output.mkdir(parents=True,exist_ok=True)
version=json.loads((ROOT/'plugin.json').read_text())['version']
with tempfile.TemporaryDirectory(prefix='bridge-release-') as temp:
    stage=Path(temp)/'chatgpt-codex-bridge'
    plugin=stage/'plugins/chatgpt-codex-bridge';build(plugin)
    # Block personal paths/IDs, not ordinary names of upstream authors or URL links.
    forbidden=[re.escape((str(Path.home())+'/').encode())]
    for file in plugin.rglob('*'):
        if file.is_file() and any(re.search(x,file.read_bytes()) for x in forbidden):
            raise SystemExit(f'personal data found in {file.relative_to(plugin)}')
    manifest={'name':'chatgpt-bridge','interface':{'displayName':'ChatGPT Codex Bridge'},'plugins':[{'name':'chatgpt-codex-bridge','source':{'source':'local','path':'./plugins/chatgpt-codex-bridge'},'policy':{'installation':'AVAILABLE','authentication':'ON_INSTALL'},'category':'Productivity'}]}
    m=stage/'.agents/plugins/marketplace.json';m.parent.mkdir(parents=True);m.write_text(json.dumps(manifest,indent=2)+'\n')
    (stage/'INSTALL.md').write_text('Add this extracted directory using `codex plugin marketplace add <directory>`, then install chatgpt-codex-bridge from that marketplace. Open a new task. See plugins/chatgpt-codex-bridge/README.md for prerequisites and setup.\n')
    zip_path=Path(shutil.make_archive(str(a.output/f'chatgpt-codex-bridge-{version}'),'zip',temp,stage.name))
sha=hashlib.sha256(zip_path.read_bytes()).hexdigest()
zip_path.with_suffix('.sha256').write_text(f'{sha}  {zip_path.name}\n')
print(json.dumps({'zip':str(zip_path.resolve()),'sha256':sha,'published':False},indent=2))

"""Build an allowlisted, self-contained package without personal runtime state."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import uuid

ROOT=Path(__file__).resolve().parents[1]
FILES=['plugin.json','.codex-plugin/plugin.json','.mcp.json','bridge.py','server.py','oauth_provider.py','pyproject.toml','README.md','README.zh-CN.md','WORKFLOW.md','RELEASE.md','VALIDATION.md','LICENSE','THIRD_PARTY_NOTICES.md','UPSTREAM.json','USAGE.zh-CN.md']
FILES += ['SHARING_REVIEW.md']
DIRS=['.github','skills','scripts','tests','examples','vendor','marketing']
EXCLUDED={'.git','.venv','.tooling','node_modules','__pycache__','.pytest_cache','dist','validation','release'}

def build(output):
    output=Path(output).expanduser().absolute()
    if output.resolve()==ROOT or ROOT.is_relative_to(output.resolve()):
        raise ValueError('output must not replace source or its parent')
    for name in DIRS:
        if output.resolve().is_relative_to((ROOT/name).resolve()):
            raise ValueError('output cannot be inside a packaged input directory')
    output.parent.mkdir(parents=True,exist_ok=True)
    if output.exists() and not (output/'GENERATED.txt').is_file():
        raise ValueError('refusing to replace unmanaged directory')
    stage=Path(tempfile.mkdtemp(prefix='.bridge-package-',dir=output.parent))
    try:
        for name in FILES:
            src=ROOT/name
            if not src.is_file():raise ValueError(f'missing release input: {name}')
            dst=stage/name;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
        for name in DIRS:
            for src in (ROOT/name).rglob('*'):
                rel=src.relative_to(ROOT)
                if any(x in EXCLUDED for x in rel.parts):continue
                if src.is_symlink():raise ValueError(f'package input symlink: {rel}')
                if src.is_file():
                    dst=stage/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
        (stage/'GENERATED.txt').write_text('Generated from versioned ChatGPT Codex Bridge sources. Rebuild with scripts/package_plugin.py; runtime data is external.\n')
        hashes={p.relative_to(stage).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(stage.rglob('*')) if p.is_file()}
        (stage/'CONTENTS.sha256.json').write_text(json.dumps(hashes,indent=2)+'\n')
        if output.exists():
            backup=Path.home()/'.local/share/chatgpt-codex-bridge/package-backups';backup.mkdir(parents=True,exist_ok=True)
            shutil.move(str(output),str(backup/uuid.uuid4().hex))
        stage.rename(output)
        return {'package':str(output),'files':len(hashes),'version':json.loads((output/'plugin.json').read_text())['version']}
    finally:
        if stage.exists():shutil.rmtree(stage)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,default=Path.home()/'plugins/chatgpt-codex-bridge');a=p.parse_args()
    print(json.dumps(build(a.output),indent=2))

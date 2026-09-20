"""Scan source/package text for common private data. Never print matched values.

Heuristic release gate, not a guarantee that arbitrary private data is detectable.
Binary screenshots must additionally be inspected visually. Git metadata is separate.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

RULES = {
    'personal-home': r'(?:/Users|/home)/[A-Za-z0-9_.-]+/',
    'chat-link': r'https://chatgpt\.com/c/[0-9a-f-]{20,}',
    'live-tunnel': r'https://[a-z0-9-]+\.trycloudflare\.com',
    'github-token': r'\b(?:gh[pousr]_|github_pat_)[A-Za-z0-9_]{20,}',
    'private-key': r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',
    'email': r'\b[A-Za-z0-9._%+-]+@(?!(?:users\.noreply\.github\.com|example\.(?:com|invalid)|test\.invalid)\b)[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b',
}

def findings(text):
    return [name for name, pattern in RULES.items() if re.search(pattern, text)]

def scan(root, tracked=False):
    root = Path(root)
    files = ([root/p for p in subprocess.check_output(['git','-C',str(root),'ls-files','-z'], text=True).split('\0') if p]
             if tracked else [p for p in root.rglob('*') if p.is_file()])
    allow_path = root/'scripts/share-fixtures.json'
    reviewed = json.loads(allow_path.read_text()) if allow_path.exists() else {}
    hits, binary, fixtures = [], [], []
    for path in files:
        rel = str(path.relative_to(root))
        if hashlib.sha256(path.read_bytes()).hexdigest() == reviewed.get(rel, {}).get('sha256'):
            fixtures.append(rel)
            continue
        try:
            content = path.read_text(encoding='utf-8')
        except UnicodeError:
            binary.append(rel)
            continue
        for rule in findings(content):
            hits.append({'file': rel, 'rule': rule})
    return {'files': len(files), 'findings': hits, 'reviewed_fixtures': fixtures, 'binary_requires_review': binary}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root', type=Path)
    parser.add_argument('--tracked', action='store_true')
    parser.add_argument('--history', action='store_true')
    args = parser.parse_args()
    report = scan(args.root, args.tracked)
    if args.history:
        metadata = subprocess.check_output(['git','-C',str(args.root),'log','--all','--format=%H %ae %ce'],text=True)
        report['history_private_email_commits'] = [line.split()[0][:12] for line in metadata.splitlines() if 'email' in findings(line)]
    print(json.dumps(report, indent=2))
    raise SystemExit(bool(report['findings'] or report.get('history_private_email_commits')))

if __name__ == '__main__':
    main()

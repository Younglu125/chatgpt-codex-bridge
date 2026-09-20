"""Persist a Codex conversation's CCB preference; never dispatch messages.

The skill interprets user intent in context. This CLI deliberately does not match
raw prompt substrings: quotes, negation and plugin maintenance are not consent.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from bridge import DEFAULT_STATE, Store, dump, load, now


def decide(store, thread, intent='inherit', phase='routine'):
    if not thread.strip():
        raise ValueError('an actual Codex conversation ID is required')
    path = store.state/'sessions'/(hashlib.sha256(thread.encode()).hexdigest()+'.json')
    with store.transaction():
        saved = load(path) if path.exists() else {'enabled': False}
        if intent in {'enable', 'disable'}:
            saved = {'enabled': intent == 'enable', 'updated_at': now()}
            dump(path, saved)
        enabled = saved['enabled']
    consult = intent == 'require-gpt' or (enabled and phase in {'analysis', 'decision', 'review'})
    if intent in {'disable', 'local-once'}:
        consult = False
    return {'enabled': enabled, 'participant': 'chatgpt' if consult else 'codex',
            'phase': phase, 'intent': intent, 'dispatched': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--state', default=str(DEFAULT_STATE))
    parser.add_argument('--thread', required=True)
    parser.add_argument('--intent', choices=['inherit', 'enable', 'disable', 'local-once', 'require-gpt'], default='inherit')
    parser.add_argument('--phase', choices=['routine', 'analysis', 'decision', 'review'], default='routine')
    args = parser.parse_args()
    print(json.dumps(decide(Store(args.state), args.thread, args.intent, args.phase), indent=2))


if __name__ == '__main__':
    main()

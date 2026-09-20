"""Exercise session isolation and participation decisions through the public CLI."""
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]

def run(state, thread, *args):
    result = subprocess.run([sys.executable, str(ROOT/'scripts/session.py'),
                             '--state', str(state), '--thread', thread, *args],
                            text=True, capture_output=True, check=True)
    return json.loads(result.stdout)

def test_default_enable_resume_and_thread_isolation(tmp_path):
    assert run(tmp_path, 'a')['participant'] == 'codex'
    assert run(tmp_path, 'a', '--intent', 'enable', '--phase', 'analysis')['participant'] == 'chatgpt'
    assert run(tmp_path, 'a', '--phase', 'review')['participant'] == 'chatgpt'
    assert run(tmp_path, 'b', '--phase', 'review')['participant'] == 'codex'

def test_efficiency_overrides_and_exit(tmp_path):
    run(tmp_path, 'a', '--intent', 'enable')
    assert run(tmp_path, 'a')['participant'] == 'codex'
    assert run(tmp_path, 'a', '--intent', 'local-once', '--phase', 'decision')['participant'] == 'codex'
    assert run(tmp_path, 'a', '--phase', 'decision')['participant'] == 'chatgpt'
    assert run(tmp_path, 'a', '--intent', 'require-gpt')['participant'] == 'chatgpt'
    assert run(tmp_path, 'a', '--intent', 'disable', '--phase', 'review')['participant'] == 'codex'
    assert run(tmp_path, 'a', '--phase', 'analysis')['participant'] == 'codex'

def test_explicit_one_off_does_not_enable_session(tmp_path):
    assert run(tmp_path, 'a', '--intent', 'require-gpt')['participant'] == 'chatgpt'
    assert run(tmp_path, 'a', '--phase', 'review')['enabled'] is False

def test_thread_id_cannot_escape_state_directory(tmp_path):
    result = run(tmp_path/'state', '../../outside', '--intent', 'enable')
    assert result['enabled'] is True
    assert not (tmp_path/'outside').exists()
    assert len(list((tmp_path/'state'/'sessions').glob('*.json'))) == 1

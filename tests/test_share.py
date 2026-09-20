import importlib.util
import hashlib
import json
from pathlib import Path

spec = importlib.util.spec_from_file_location('audit_share', Path(__file__).resolve().parents[1]/'scripts/audit_share.py')
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)

def test_private_values_are_detected_without_returning_values():
    value = '/Users/' + 'fixture/Documents/private.txt'
    assert audit.findings(value) == ['personal-home']
    assert audit.findings('alice' + '@' + 'private.org') == ['email']
    assert audit.findings('https://chatgpt.com/c/' + 'a'*24) == ['chat-link']

def test_public_placeholders_and_github_privacy_email():
    assert audit.findings('fixture@example.invalid') == []
    assert audit.findings('123+maintainer@users.noreply.github.com') == []
    assert audit.findings('~/projects/project') == []

def test_fine_grained_github_token_is_detected():
    assert audit.findings('github_' + 'pat_' + 'x'*82) == ['github-token']

def test_binary_is_reported_for_visual_review(tmp_path):
    (tmp_path/'image.png').write_bytes(b'\x89PNG\xff')
    result = audit.scan(tmp_path)
    assert result['binary_requires_review'] == ['image.png']

def test_reviewed_fixture_exemption_is_invalidated_by_changes(tmp_path):
    sample = tmp_path/'fixture.txt'
    sample.write_text('fixture' + '@' + 'private.org')
    (tmp_path/'scripts').mkdir()
    (tmp_path/'scripts/share-fixtures.json').write_text(json.dumps({
        'fixture.txt': {'sha256': hashlib.sha256(sample.read_bytes()).hexdigest()}
    }))
    assert audit.scan(tmp_path)['findings'] == []
    sample.write_text(sample.read_text() + '\nchanged')
    assert audit.scan(tmp_path)['findings'] == [{'file': 'fixture.txt', 'rule': 'email'}]

import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest
from bridge import Store
from test_bridge import baseline, read_result

ROOT=Path(__file__).resolve().parents[1]

def module(name):
    spec=importlib.util.spec_from_file_location(name, ROOT/'scripts'/f'{name}.py')
    result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result);return result

@pytest.fixture
def store(tmp_path):
    project=tmp_path/'project';project.mkdir();(project/'main.py').write_text('x = 1\n')
    s=Store(tmp_path/'state');s.register('test',project);s.target('test-chat','fixture','test-only ordinary chat');return s

def test_per_project_target_and_pending_survive_restart(store,tmp_path):
    project=tmp_path/'second';project.mkdir();(project/'main.py').write_text('y = 2\n')
    store.register('second',project);store.target('separate-chat','fixture','test proof',project='second')
    a=store.prepare('test','first');b=store.prepare('second','second')
    assert a['target']['id']=='test-chat' and b['target']['id']=='separate-chat'
    store.begin(a['id'],baseline())
    resumed=Store(store.state)
    assert len(resumed.pending())==2
    with pytest.raises(ValueError,match='already started'):resumed.begin(a['id'],baseline())
    with pytest.raises(ValueError,match='another root'):store.register('test',project)

def test_auto_project_subdirectory_and_worktree(tmp_path):
    repo=tmp_path/'same';repo.mkdir()
    def git(*args):return subprocess.check_output(['git','-C',str(repo),*args],text=True)
    git('init','-q');git('config','user.email','test@example.invalid');git('config','user.name','Fixture')
    (repo/'a.py').write_text('x=1');git('add','.');git('commit','-qm','fixture')
    sub=repo/'nested';sub.mkdir();s=Store(tmp_path/'state')
    first=s.auto_project(sub);assert first['root']==str(repo.resolve())
    worktree=tmp_path/'other'/'same';git('worktree','add','-qb','other',str(worktree))
    other=s.auto_project(worktree)
    assert first['project']!=other['project']
    assert other['root']==str(worktree.resolve())

def capture(messages, generating=False, url='https://chatgpt.com/c/test-chat'):
    return {'source':'browser-ui','url':url,'generating':generating,'messages':messages}

def test_browser_collection_requires_complete_actual_matching_turn(store):
    j=store.prepare('test','analyze');prompt=store.prompt(j['id'])
    store.begin(j['id'],store.browser_data(capture([])))
    messages=[{'id':'u','role':'user','text':prompt},{'id':'a','role':'assistant','text':'analysis\nBRIDGE_DONE:'+j['id']}]
    with pytest.raises(ValueError):store.collect(j['id'],store.browser_data(capture(messages,True)))
    interrupted=messages[:1]+[{'id':'u2','role':'user','text':'unrelated'}]+messages[1:]
    with pytest.raises(ValueError):store.collect(j['id'],store.browser_data(capture(interrupted)))
    assert store.collect(j['id'],store.browser_data(capture(messages)))['state']=='analyzed'
    source=json.loads((store.job_dir(j['id'])/'response.json').read_text())
    assert source['source']=='browser-ui'

@pytest.mark.parametrize('url',['http://chatgpt.com/c/test-chat','https://evil.invalid/c/test-chat','https://chatgpt.com/','https://chatgpt.com/g/g-p-example/project'])
def test_browser_rejects_wrong_origins_or_non_chats(store,url):
    with pytest.raises(ValueError):store.browser_data(capture([],url=url))

def test_review_links_and_limit_and_access_revoke(store):
    j=store.prepare('test','analyze','mcp')
    with pytest.raises(ValueError):store.prepare('test','review',parent=j['id'])
    for iteration in range(4):
        assert j['iteration']==iteration
        store.begin(j['id'],baseline());store.collect(j['id'],read_result(j,store.prompt(j['id'])))
        store.finish(j['id'],'actual fixture implementation report')
        assert not store.job(j['id'])['mcp_enabled']
        if iteration<3:
            old=j;j=store.prepare('test','review','live',parent=j['id'])
            assert j['parent_job']==old['id'] and j['phase']=='review'
            assert store.evidence(j['id'])['files']=={}
    with pytest.raises(ValueError,match='limit'):store.prepare('test','review',parent=j['id'])

@pytest.mark.parametrize('args',[['start','--workspace','/tmp'],['doctor','--workspace=/tmp'],['status','-w/tmp']])
def test_full_adapter_cannot_override_registered_root(store,args):
    with pytest.raises(ValueError):module('full').command(store,'test',args)

@pytest.mark.parametrize('name', sorted(module('full').ALLOWED))
def test_full_adapter_exposes_complete_upstream_command_surface(store, name):
    full=module('full')
    cmd,_,_=full.command(store,'test',[name])
    assert name in cmd

def test_full_adapter_resolves_registered_root_and_isolated_state(store):
    backend=ROOT/'vendor/codex-with-chatgpt/dist/cli/index.js'
    if not backend.exists():pytest.skip('Full backend not built')
    cmd,cwd,env=module('full').command(store,'test',['status','--json'])
    assert cmd[-2:]==['--workspace',store.config()['projects']['test']['root']]
    assert str(cwd)==store.config()['projects']['test']['root']
    assert env['C2C_STATE_DIR']==str(store.state/'full')
    doctor,_,_=module('full').command(store,'test',['doctor','--json'])
    assert '--no-fix' not in doctor


def test_route_prefers_reusable_full_and_falls_back_without_user_work(store):
    route=module('route')
    ready={'ok':True,'running':True,'workspaceId':'abc','workspaceName':'project','tokenCount':1,
           'tunnel':{'running':True}}
    verified={'session':{'url':'https://chatgpt.com/c/chat'},
              'conversation':{'chatUrl':'https://chatgpt.com/c/chat'}}
    live=route.decide('repository', {'id':'chat'}, ready, session=verified)
    assert live['route']=='live' and live['full']['sessionMatchesTarget'] is True
    switched=route.decide('repository', {'id':'other-account-chat'}, ready, session=verified)
    assert switched['route']=='full-verify'
    assert switched['full']['savedChatSession'] is True
    assert switched['full']['sessionMatchesTarget'] is False
    assert route.decide('repository', {'id':'chat'}, ready)['route']=='full-verify'
    bounded=route.decide('bounded', {'id':'chat'}, {'ok':True,'running':True,'tokenCount':0,
                                                   'tunnel':{'running':True}})
    assert bounded['route']=='snapshot' and bounded['humanAction']=='none'
    broad=route.decide('repository', {'id':'chat'}, None, 'not configured')
    assert broad['route']=='full-setup'
    assert broad['humanAction']=='one_time_chatgpt_connector_authorization'


def test_pending_can_be_scoped_to_current_project(store,tmp_path):
    project=tmp_path/'other';project.mkdir();(project/'main.py').write_text('y=1\n')
    store.register('other',project);store.target('other-chat','fixture','test proof',project='other')
    store.prepare('test','first');store.prepare('other','second')
    pending=store.pending('test')
    assert len(pending)==1 and pending[0]['project']=='test'

def test_package_is_self_contained_and_lite_runs_without_mcp(tmp_path):
    dest=tmp_path/'path with spaces'/'chatgpt-codex-bridge'
    module('package_plugin').build(dest)
    assert (dest/'skills/chatgpt-codex-bridge/SKILL.md').exists()
    assert not (dest/'validation').exists() and not (dest/'.venv').exists()
    assert not list(dest.rglob('.tooling'))
    assert not list(dest.rglob('node_modules'))
    for file in dest.rglob('*'):
        assert not file.is_symlink()
    hashes=json.loads((dest/'CONTENTS.sha256.json').read_text())
    assert all(hashlib.sha256((dest/p).read_bytes()).hexdigest()==h for p,h in hashes.items())
    project=tmp_path/'consumer-project';project.mkdir();(project/'a.py').write_text('x=1\n')
    result=subprocess.run([sys.executable,'-S',str(dest/'bridge.py'),'--state',str(tmp_path/'empty-state'),'auto-project','--root',str(project)],text=True,capture_output=True,check=True)
    info=json.loads(result.stdout);assert info['root']==str(project.resolve())
    subprocess.run([sys.executable,'-S',str(dest/'scripts/doctor.py'),'--state',str(tmp_path/'empty-state')],check=True,capture_output=True)
    subprocess.run([sys.executable,'-S',str(dest/'scripts/setup.py'),'--mode','lite'],check=True,capture_output=True)

def test_vendored_sources_match_pin():
    lock=json.loads((ROOT/'UPSTREAM.json').read_text())
    vendor=ROOT/'vendor/codex-with-chatgpt'
    for rel,sha in lock['sha256'].items():
        assert hashlib.sha256((vendor/rel).read_bytes()).hexdigest()==sha, rel


def test_runtime_package_excludes_development_and_retired_helpers(tmp_path):
    dest = tmp_path / 'clean runtime'
    module('package_plugin').build(dest)
    for name in ('.github', 'tests', 'examples', 'marketing',
                 'scripts/render_share_demo.cjs', 'scripts/install_tunnel_client.py',
                 'scripts/tunnel', 'scripts/public-mcp', 'scripts/public_mcp.py'):
        assert not (dest / name).exists(), name
    for name in ('bridge.py', 'server.py', 'oauth_provider.py', 'scripts/setup.py',
                 'scripts/install_plugin.py', 'scripts/mcp-launch.py',
                 'vendor/codex-with-chatgpt/src/cli/index.ts',
                 'vendor/codex-with-chatgpt/tests/mcp-integration.test.ts'):
        assert (dest / name).is_file(), name
    # A release extraction must still support the documented convenience installer,
    # which repackages its own inputs before switching the personal installation.
    rebuilt = tmp_path / 'repacked runtime'
    subprocess.run([sys.executable, str(dest / 'scripts/package_plugin.py'),
                    '--output', str(rebuilt)], check=True, capture_output=True)
    assert (rebuilt / 'bridge.py').read_bytes() == (dest / 'bridge.py').read_bytes()
    assert not (rebuilt / 'tests').exists()

import asyncio
import json
from pathlib import Path
import sys

import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from bridge import Store, eligible, load, read_safe, sanitize, snapshot


@pytest.fixture
def workspace(tmp_path):
    root = tmp_path / "project"; root.mkdir()
    (root / "main.py").write_text("def add(a, b):\n    return a - b\n")
    store = Store(tmp_path / "state")
    store.register("fixture", root)
    store.target("test-chat", "fixture-model", "test-only ordinary chat")
    return root, store


def read_result(job, prompt, status="completed", answer_id="new-answer", thread="test-chat", suffix=True):
    return {"thread": {"id": thread, "kind": "chatgpt", "status": {"type": "idle"}}, "turns": [
        {"status": status, "error": None, "items": [
            {"type": "userMessage", "id": "new-user", "content": [{"type": "text", "text": prompt}]},
            {"type": "agentMessage", "id": answer_id, "text": "Fix main.py:2 to a + b.\n" + ("BRIDGE_DONE:" + job["id"] if suffix else "in progress")},
        ]}]}


def baseline():
    return {"thread": {"id": "test-chat", "kind": "chatgpt", "status": {"type": "idle"}}, "turns": [{"items": [{"id": "old-answer"}]}]}


def test_excludes_private_and_symlink_files(workspace, tmp_path):
    root, store = workspace
    (root / ".env").write_text("PASSWORD=private")
    (root / "credentials.json").write_text('{"password":"private"}')
    (root / "data").mkdir(); (root / "data" / "ledger.json").write_text("private")
    outside = tmp_path / "outside.py"; outside.write_text("private")
    (root / "linked.py").symlink_to(outside)
    (root / "linked-dir").symlink_to(tmp_path, target_is_directory=True)
    evidence = snapshot(root)
    assert set(evidence["files"]) == {"main.py"}
    with pytest.raises(OSError): read_safe(root, "linked-dir/outside.py")
    with pytest.raises(ValueError): read_safe(root, "../outside.py")


def test_redaction_keeps_line_numbers():
    value = "header\nAPI_KEY = 'sensitive'\nhttps://name:pwd@example.com/path\n"
    clean = sanitize(value)
    assert "sensitive" not in clean and "pwd" not in clean
    assert len(clean.splitlines()) == len(value.splitlines())
    key = "before\n-----BEGIN RSA PRIVATE KEY-----\nsecretbody\n-----END RSA PRIVATE KEY-----\nafter\n"
    assert "secretbody" not in sanitize(key)
    assert sanitize(key).splitlines().index("after") == key.splitlines().index("after")


def test_dispatch_no_duplicate_or_wrong_target(workspace):
    _, store = workspace
    job = store.prepare("fixture", "fix add")
    data = baseline(); data["thread"]["status"]["type"] = "running"
    with pytest.raises(ValueError): store.begin(job["id"], data)
    store.begin(job["id"], baseline())
    with pytest.raises(ValueError): store.begin(job["id"], baseline())
    other = store.prepare("fixture", "second job")
    with pytest.raises(ValueError, match="another pending"): store.begin(other["id"], baseline())


def test_target_does_not_invent_unavailable_model(workspace):
    _, store = workspace
    target = store.target("native-chat", None, "native kind and completed roundtrip", project="fixture")
    saved = store.config()["projects"]["fixture"]["target"]
    assert saved["model_label"] is None
    assert saved["mode"] == "chatgpt-mode-unconfirmed"


@pytest.mark.parametrize("change", ["old", "running", "wrong-chat", "unfinished-browser", "wrong-prompt"])
def test_collect_rejects_stale_or_partial(workspace, change):
    _, store = workspace
    job = store.prepare("fixture", "fix add"); store.begin(job["id"], baseline())
    data = read_result(job, store.prompt(job["id"]))
    if change == "old": data["turns"][0]["items"][1]["id"] = "old-answer"
    if change == "running": data["turns"][0]["status"] = "inProgress"
    if change == "wrong-chat": data["thread"]["id"] = "other-chat"
    if change == "unfinished-browser":
        data["source"] = "browser-ui"
        data["turns"][0]["items"][1]["text"] = "partial"
    if change == "wrong-prompt": data["turns"][0]["items"][0]["content"][0]["text"] += "modified"
    with pytest.raises(ValueError): store.collect(job["id"], data)
    assert store.job(job["id"])["state"] == "dispatching"


def test_native_completed_turn_can_omit_marker(workspace):
    _, store = workspace
    job = store.prepare("fixture", "fix add"); store.begin(job["id"], baseline())
    data = read_result(job, store.prompt(job["id"]), suffix=False)
    data["turns"][0]["items"][1]["text"] = "Complete native answer without a marker."
    completed = store.collect(job["id"], data)
    assert completed["state"] == "analyzed"
    assert completed["completion_proof"] == "native_completed_turn"


def test_collect_skips_progress_and_selects_final_marker(workspace):
    _, store = workspace
    job = store.prepare("fixture", "analyze"); store.begin(job["id"], baseline())
    data = read_result(job, store.prompt(job["id"]))
    data["turns"][0]["items"].insert(1, {
        "type": "agentMessage", "id": "progress", "text": "Still reading the files."
    })
    result = store.collect(job["id"], data)
    assert result["assistant_message_id"] == "new-answer"
    assert result["completion_proof"] == "marker"
    assert "Fix main.py" in (store.job_dir(job["id"]) / "analysis.md").read_text()


@pytest.mark.parametrize("problem", [
    "ambiguous", "answer-truncated", "turn-truncated", "response-truncated",
    "request-truncated", "marker-before-later-answer", "cross-user-boundary",
])
def test_collect_incomplete_or_ambiguous_native_stays_pending(workspace, problem):
    _, store = workspace
    job = store.prepare("fixture", "analyze"); store.begin(job["id"], baseline())
    data = read_result(job, store.prompt(job["id"]))
    turn = data["turns"][0]
    if problem == "ambiguous":
        turn["items"][1]["text"] = "A possible answer, without a completion marker."
        turn["items"].insert(1, {"type": "agentMessage", "id": "progress", "text": "Working."})
    elif problem == "answer-truncated":
        turn["items"][1]["truncated"] = True
    elif problem == "turn-truncated":
        turn["truncated"] = True
    elif problem == "response-truncated":
        data["truncated"] = True
    elif problem == "request-truncated":
        turn["items"][0]["content"][0]["truncated"] = True
    elif problem == "marker-before-later-answer":
        turn["items"].append({"type": "agentMessage", "id": "later", "text": "A further response."})
    else:
        turn["items"][1]["text"] = "Still working."
        turn["items"].extend([
            {"type": "userMessage", "id": "next-user", "content": [{"type": "text", "text": "Different task."}]},
            {"type": "agentMessage", "id": "later", "text": "Final\nBRIDGE_DONE:" + job["id"]},
        ])
    with pytest.raises(ValueError):
        store.collect(job["id"], data)
    assert store.job(job["id"])["state"] == "dispatching"
    assert not (store.job_dir(job["id"]) / "analysis.md").exists()


def test_collect_complete_current_turn_ignores_older_history_pagination(workspace):
    _, store = workspace
    job = store.prepare("fixture", "analyze"); store.begin(job["id"], baseline())
    data = read_result(job, store.prompt(job["id"]))
    data["page"] = {"order": "newest_first", "hasMore": True, "nextCursor": "older-turns"}
    assert store.collect(job["id"], data)["state"] == "analyzed"


def test_collect_missing_request_on_page_does_not_accept_old_answer(workspace):
    _, store = workspace
    job = store.prepare("fixture", "analyze"); store.begin(job["id"], baseline())
    data = read_result(job, store.prompt(job["id"]))
    data["turns"][0]["items"] = data["turns"][0]["items"][1:]
    data["page"] = {"hasMore": True, "nextCursor": "request-page"}
    with pytest.raises(ValueError):
        store.collect(job["id"], data)
    assert store.job(job["id"])["state"] == "dispatching"


def test_native_completed_turn_recovers_old_marker_only_cancellation(workspace):
    _, store = workspace
    job = store.prepare("fixture", "fix add"); store.begin(job["id"], baseline())
    cancelled = store.job(job["id"])
    cancelled.update(
        state="cancelled",
        cancel_reason="ChatGPT returned a complete substantive answer but omitted the required BRIDGE_DONE marker",
        cancelled_at="old-time",
    )
    store.save_job(cancelled)
    data = read_result(job, store.prompt(job["id"]), suffix=False)
    data["turns"][0]["items"][1]["text"] = "Recovered complete native answer."
    recovered = store.collect(job["id"], data)
    assert recovered["state"] == "analyzed"
    assert recovered["completion_proof"] == "native_completed_turn"
    assert recovered["recovered_from_cancelled_at"] == "old-time"
    assert "cancel_reason" not in recovered


def test_complete_reconcile_drift_and_finish(workspace):
    root, store = workspace
    job = store.prepare("fixture", "fix add"); store.begin(job["id"], baseline())
    # Even after uncertain send, read reconciliation can collect the real matched turn.
    completed = store.collect(job["id"], read_result(job, store.prompt(job["id"])))
    assert completed["state"] == "analyzed"
    assert completed["completion_proof"] == "marker"
    assert store.check(job["id"])["unchanged"]
    (root / "main.py").write_text("def add(a,b):\n    return a + b\n")
    assert not store.check(job["id"])["unchanged"]
    store.finish(job["id"], "Fixed main.py:2. Validated add(2,3)==5.")
    assert store.job(job["id"])["state"] == "implemented"


def test_analysis_only_completion_is_terminal(workspace):
    _, store = workspace
    job = store.prepare("fixture", "analysis only"); store.begin(job["id"], baseline())
    store.collect(job["id"], read_result(job, store.prompt(job["id"])))
    store.complete(job["id"], "Analysis delivered; no local modification was requested.")
    assert store.job(job["id"])["state"] == "completed"
    assert store.pending("fixture") == []


def test_prompt_transport_exports_no_local_files(workspace):
    _, store = workspace
    job = store.prepare("fixture", "compare two architecture options", "prompt")
    evidence = store.evidence(job["id"])
    assert job["transport"] == "prompt"
    assert job["mcp_enabled"] is False
    assert evidence["files"] == {} and evidence["scope"] == "no-local-files"
    assert "没有导出或提供任何本地文件内容" in store.prompt(job["id"])
    checked = store.check(job["id"])
    assert checked["unchanged"] is None and checked["scope"] == "no-local-files"


def test_tampered_prompt_and_snapshot_rejected(workspace):
    _, store = workspace
    job = store.prepare("fixture", "fix add")
    (store.job_dir(job["id"]) / "prompt.txt").write_text("tampered")
    with pytest.raises(ValueError, match="integrity"): store.begin(job["id"], baseline())
    (store.job_dir(job["id"]) / "evidence.json").write_text("{}")
    with pytest.raises(ValueError, match="integrity"): store.evidence(job["id"])


def test_oversize_inline_and_mismatched_receipt_rejected(workspace):
    root, store = workspace
    (root / "large.py").write_text("# text\n" * 3000)
    with pytest.raises(ValueError, match="18000"): store.prepare("fixture", "analyze")
    job = store.prepare("fixture", "analyze", "mcp")
    store.begin(job["id"], baseline())
    with pytest.raises(ValueError, match="receipt"): store.sent(job["id"], {"threadId": "wrong"})
    assert store.job(job["id"])["state"] == "dispatching"
    store.sent(job["id"], {"threadId": "test-chat"})
    assert store.job(job["id"])["state"] == "sent"


def test_real_stdio_mcp_roundtrip(workspace):
    root, store = workspace
    job = store.prepare("fixture", "fix add", "mcp")

    async def run():
        command = StdioServerParameters(command=sys.executable, args=[str(Path(__file__).resolve().parents[1] / "server.py"), "--state", str(store.state)])
        async with stdio_client(command) as (reader, writer):
            async with ClientSession(reader, writer) as session:
                await session.initialize()
                tools = await session.list_tools()
                assert len(tools.tools) == 6
                assert all(t.annotations.readOnlyHint for t in tools.tools)
                result = await session.call_tool("bridge_read", {"job_id": job["id"], "path": "main.py", "start_line": 1, "end_line": 2})
                assert not result.isError
                assert result.structuredContent["lines"][1]["text"] == "    return a - b"
                denied = await session.call_tool("bridge_read", {"job_id": job["id"], "path": "../outside.py"})
                assert denied.isError
                hit = await session.call_tool("bridge_search", {"job_id": job["id"], "query": "return"})
                assert hit.structuredContent["matches"][0]["line"] == 2
                (root / "main.py").write_text("modified after snapshot")
                frozen = await session.call_tool("bridge_read", {"job_id": job["id"], "path": "main.py", "start_line": 2, "end_line": 2})
                assert frozen.structuredContent["lines"][0]["text"] == "    return a - b"
                store.revoke(job["id"])
                revoked = await session.call_tool("bridge_overview", {"job_id": job["id"]})
                assert revoked.isError
                local_only = store.prepare("fixture", "inline analysis", "snapshot")
                denied = await session.call_tool("bridge_overview", {"job_id": local_only["id"]})
                assert denied.isError
    asyncio.run(run())

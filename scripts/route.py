"""Choose the least-friction bridge route while preferring a reusable live connection."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from bridge import DEFAULT_STATE, Store
from scripts.full import command as full_command


def full_json(store: Store, project: str, subcommand: str) -> tuple[dict | None, str | None]:
    """Read one Full JSON command without starting or repairing anything."""
    try:
        cmd, cwd, env = full_command(store, project, [subcommand, "--json"])
        result = subprocess.run(
            cmd, cwd=cwd, env=env, text=True, capture_output=True, timeout=15
        )
        if result.returncode:
            return None, (result.stderr or result.stdout or "Full status unavailable").strip()
        return json.loads(result.stdout), None
    except (ValueError, KeyError, OSError, subprocess.SubprocessError, json.JSONDecodeError) as exc:
        return None, str(exc)


def chat_id(url: str | None) -> str | None:
    """Return the ordinary ChatGPT conversation id from a saved chat URL."""
    if not url:
        return None
    try:
        path = urlparse(url).path
    except (TypeError, ValueError):
        return None
    match = re.search(r"(?:^|/)c/([A-Za-z0-9-]+)(?:/|$)", path)
    return match.group(1) if match else None


def decide(scope: str, target: dict | None, status: dict | None, error: str | None = None,
           session: dict | None = None, session_error: str | None = None) -> dict:
    tunnel = (status or {}).get("tunnel") or {}
    conversation = (session or {}).get("conversation") or {}
    saved_chat = bool((session or {}).get("session") and conversation.get("chatUrl"))
    session_chat_id = chat_id(conversation.get("chatUrl"))
    target_chat_id = (target or {}).get("id")
    session_matches_target = bool(
        saved_chat and session_chat_id and target_chat_id and session_chat_id == target_chat_id
    )
    session_verified = bool(saved_chat and session_matches_target)
    authorized = int((status or {}).get("tokenCount", 0)) > 0
    full_ready = bool(
        status
        and status.get("ok")
        and status.get("running")
        and tunnel.get("running")
        and authorized
        and session_verified
    )
    result = {
        "scope": scope,
        "targetBound": bool(target),
        "fullReady": full_ready,
        "full": {
            "running": bool((status or {}).get("running")),
            "tunnelRunning": bool(tunnel.get("running")),
            "authorizedConnections": int((status or {}).get("tokenCount", 0)),
            "verifiedChatSession": session_verified,
            "savedChatSession": saved_chat,
            "sessionMatchesTarget": session_matches_target,
            "workspaceId": (status or {}).get("workspaceId"),
            "workspaceName": (status or {}).get("workspaceName"),
        },
    }
    if error:
        result["fullStatusError"] = error
    if session_error:
        result["fullSessionError"] = session_error
    if not target:
        result.update(
            route="bind-target",
            reason="No ordinary ChatGPT conversation is bound to this project yet.",
            humanAction="select_or_create_one_chat_once",
        )
    elif scope == "prompt":
        result.update(
            route="prompt",
            reason="The task does not need local project contents.",
            humanAction="none",
        )
    elif full_ready:
        result.update(
            route="live",
            reason="This project's authorized live MCP is already running; reuse it.",
            humanAction="none",
        )
    elif scope == "bounded":
        result.update(
            route="snapshot",
            reason="Live MCP is not ready and the evidence can be bounded, so use an automatic frozen snapshot.",
            humanAction="none",
        )
    elif authorized:
        result.update(
            route="full-verify",
            reason=(
                "OAuth exists, but the saved Full chat does not match the current account target; "
                "verify workspace_info/read_file in the current chat and save it before reuse."
                if saved_chat and not session_matches_target else
                "OAuth exists, but no ChatGPT chat has passed workspace identity and file-read verification yet."
            ),
            humanAction="none_unless_login_or_oauth_consent",
        )
    else:
        result.update(
            route="full-setup",
            reason="Repository-wide discovery needs live MCP; complete this project's one-time connector authorization.",
            humanAction="one_time_chatgpt_connector_authorization",
        )
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state", default=str(DEFAULT_STATE))
    parser.add_argument("--project", required=True)
    parser.add_argument("--scope", choices=["prompt", "bounded", "repository"], required=True)
    args = parser.parse_args()
    store = Store(args.state)
    project = store.config().get("projects", {}).get(args.project)
    if not project:
        parser.error("unknown project; run bridge auto-project first")
    status, error = full_json(store, args.project, "status")
    session, session_error = full_json(store, args.project, "session")
    target = project.get("target") or store.config().get("target")
    print(json.dumps(decide(args.scope, target, status, error, session, session_error), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

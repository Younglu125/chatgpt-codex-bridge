"""Verify skill discovery via the public Codex app-server skills/list protocol."""
import os
from pathlib import Path
import shutil
import json
import queue
import subprocess
import threading


app_binary = Path("/Applications/ChatGPT.app/Contents/Resources/codex")
binary = os.environ.get("BRIDGE_CODEX_BINARY") or (str(app_binary) if app_binary.exists() else shutil.which("codex"))
if not binary:
    raise SystemExit("Codex binary not found; set BRIDGE_CODEX_BINARY")
process = subprocess.Popen([binary, "app-server"],
                           stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
messages = queue.Queue()


def reader():
    for line in process.stdout:
        try: messages.put(json.loads(line))
        except json.JSONDecodeError: pass


threading.Thread(target=reader, daemon=True).start()


def send(data):
    process.stdin.write(json.dumps(data) + "\n"); process.stdin.flush()


def response(request_id):
    while True:
        data = messages.get(timeout=20)
        if data.get("id") == request_id:
            if "error" in data: raise RuntimeError(data["error"])
            return data["result"]


try:
    send({"id": 1, "method": "initialize", "params": {"clientInfo": {"name": "bridge-loader-probe", "version": "0.1.0"}, "capabilities": {"experimentalApi": True}}})
    response(1)
    send({"method": "initialized", "params": {}})
    send({"id": 2, "method": "skills/list", "params": {"cwds": [os.getcwd()], "forceReload": True}})
    data = response(2)
    entries = [skill for item in data.get("data", []) for skill in item.get("skills", []) if "chatgpt-codex-bridge" in skill.get("name", "")]
    errors = [error for item in data.get("data", []) for error in item.get("errors", [])]
    print(json.dumps({"matching_skills": entries, "loader_errors": errors}, ensure_ascii=False, indent=2))
    if not entries: raise RuntimeError("bridge skill not discovered")
    send({"id": 3, "method": "mcpServerStatus/list", "params": {}})
    status = response(3)
    servers = [server for server in status.get("data", []) if "project-evidence" in server.get("name", "")]
    print(json.dumps({"matching_mcp_servers": [{"name": s["name"], "auth_status": s.get("authStatus"), "tool_names": list(s.get("tools", {}))} for s in servers]}, ensure_ascii=False, indent=2))
    # Lite deliberately has no auto-started MCP server.
finally:
    process.terminate(); process.wait(timeout=10)

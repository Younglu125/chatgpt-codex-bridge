#!/usr/bin/env python3
"""Manage the temporary public HTTPS + OAuth MCP test endpoint."""
from __future__ import annotations

import json
import os
from pathlib import Path
import re
import secrets
import signal
import subprocess
import sys
import time

import httpx

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = Path.home() / ".local/share/chatgpt-codex-bridge/runtime/public"
CLIENT = Path.home() / ".local/share/chatgpt-codex-bridge/runtime/bin/cloudflared"
PORT = 18767


def alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except (ProcessLookupError, PermissionError):
        return False


def read_pid(name: str) -> int | None:
    path = RUNTIME / f"{name}.pid"
    try:
        return int(path.read_text().strip())
    except (FileNotFoundError, ValueError):
        return None


def stop() -> dict:
    stopped = []
    for name in ("server", "cloudflared"):
        pid = read_pid(name)
        if pid and alive(pid):
            try:
                os.killpg(pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            stopped.append(name)
    for _ in range(50):
        if all(not pid or not alive(pid) for pid in (read_pid("server"), read_pid("cloudflared"))):
            break
        time.sleep(0.1)
    for path in RUNTIME.glob("*.pid"):
        path.unlink(missing_ok=True)
    return {"stopped": stopped}


def status(check_remote: bool = True) -> dict:
    url_path = RUNTIME / "public-url"
    url = url_path.read_text().strip() if url_path.exists() else None
    server = read_pid("server")
    tunnel = read_pid("cloudflared")
    remote = False
    if check_remote and url and server and tunnel and alive(server) and alive(tunnel):
        try:
            r = httpx.get(url + "/.well-known/oauth-protected-resource/mcp", timeout=8, trust_env=False)
            remote = r.status_code == 200
        except Exception:
            remote = False
    return {"public_url": url, "mcp_url": url + "/mcp" if url else None,
            "server_running": bool(server and alive(server)), "tunnel_running": bool(tunnel and alive(tunnel)),
            "oauth_metadata_reachable": remote, "owner_secret_file": str(RUNTIME / "owner-secret")}


def start() -> dict:
    current = status()
    if current["server_running"] or current["tunnel_running"]:
        if current["oauth_metadata_reachable"]:
            return current
        stop()
    RUNTIME.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(RUNTIME, 0o700)
    if not CLIENT.is_file():
        raise RuntimeError(f"cloudflared not found: {CLIENT}")
    secret_path = RUNTIME / "owner-secret"
    if not secret_path.exists():
        fd = os.open(secret_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "w") as f:
            f.write(secrets.token_urlsafe(32) + "\n")
    os.chmod(secret_path, 0o600)

    tunnel_log = open(RUNTIME / "cloudflared.log", "w")
    tunnel = subprocess.Popen([str(CLIENT), "tunnel", "--url", f"http://127.0.0.1:{PORT}", "--no-autoupdate"],
        stdout=tunnel_log, stderr=subprocess.STDOUT, start_new_session=True)
    (RUNTIME / "cloudflared.pid").write_text(str(tunnel.pid))
    url = None
    pattern = re.compile(r"https://[a-z0-9-]+\.trycloudflare\.com")
    try:
        for _ in range(200):
            if tunnel.poll() is not None:
                raise RuntimeError("cloudflared exited; inspect runtime/public/cloudflared.log")
            text = (RUNTIME / "cloudflared.log").read_text(errors="replace")
            hit = pattern.search(text)
            if hit:
                url = hit.group(0)
                break
            time.sleep(0.1)
        if not url:
            raise RuntimeError("timed out waiting for TryCloudflare URL")
        (RUNTIME / "public-url").write_text(url + "\n")
        os.chmod(RUNTIME / "public-url", 0o600)
        server_log = open(RUNTIME / "server.log", "w")
        server = subprocess.Popen([str(ROOT / ".venv/bin/python"), str(ROOT / "server.py"),
            "--transport", "streamable-http", "--port", str(PORT),
            "--public-url", url, "--owner-secret-file", str(secret_path)],
            cwd=ROOT, stdout=server_log, stderr=subprocess.STDOUT, start_new_session=True)
        (RUNTIME / "server.pid").write_text(str(server.pid))
        for _ in range(300):
            if server.poll() is not None:
                raise RuntimeError("MCP server exited; inspect runtime/public/server.log")
            try:
                r = httpx.get(url + "/.well-known/oauth-protected-resource/mcp", timeout=2, trust_env=False)
                if r.status_code == 200:
                    return {
                        "public_url": url,
                        "mcp_url": url + "/mcp",
                        "server_running": True,
                        "tunnel_running": True,
                        "oauth_metadata_reachable": True,
                        "owner_secret_file": str(secret_path),
                    }
            except Exception:
                pass
            time.sleep(0.1)
        raise RuntimeError("public OAuth metadata did not become reachable")
    except Exception:
        stop()
        raise


def main():
    command = sys.argv[1] if len(sys.argv) > 1 else "status"
    if command == "start": result = start()
    elif command == "stop": result = stop()
    elif command == "status": result = status()
    elif command == "secret-path": result = {"owner_secret_file": str(RUNTIME / "owner-secret")}
    else: raise SystemExit("usage: public_mcp.py [start|stop|status|secret-path]")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

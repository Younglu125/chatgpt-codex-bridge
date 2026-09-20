import base64
import hashlib
from pathlib import Path
import secrets
import socket
import subprocess
import sys
import time
from urllib.parse import parse_qs, urlparse

import httpx


def test_owner_approved_oauth_and_authenticated_mcp(tmp_path):
    secret = tmp_path / "owner-secret"
    secret.write_text("A" * 32)
    secret.chmod(0o600)
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0)); port = sock.getsockname()[1]
    process = subprocess.Popen([sys.executable, str(Path(__file__).resolve().parents[1] / "server.py"),
        "--state", str(tmp_path / "state"), "--transport", "streamable-http", "--port", str(port),
        "--public-url", "https://example.test", "--owner-secret-file", str(secret)],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    client = httpx.Client(base_url=f"http://127.0.0.1:{port}", headers={"host": "example.test"}, trust_env=False)
    try:
        for _ in range(100):
            try:
                if client.get("/.well-known/oauth-authorization-server").status_code == 200: break
            except httpx.TransportError:
                pass
            if process.poll() is not None: raise RuntimeError("OAuth MCP server exited")
            time.sleep(0.05)
        else: raise RuntimeError("OAuth MCP server did not start")
        metadata = client.get("/.well-known/oauth-protected-resource/mcp")
        assert metadata.status_code == 200
        assert metadata.json()["resource"] == "https://example.test/mcp"
        authorization_metadata = client.get("/.well-known/oauth-authorization-server").json()
        assert "offline_access" in authorization_metadata["scopes_supported"]

        registration = client.post("/register", json={
            "client_name": "bridge-test", "redirect_uris": ["https://client.example/callback"],
            "grant_types": ["authorization_code", "refresh_token"], "response_types": ["code"],
            "scope": "mcp:read offline_access",
        })
        assert registration.status_code == 201
        registered = registration.json()
        verifier = secrets.token_urlsafe(32)
        challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
        authorization = client.get("/authorize", params={
            "response_type": "code", "client_id": registered["client_id"],
            "redirect_uri": "https://client.example/callback", "scope": "mcp:read offline_access", "state": "state",
            "code_challenge": challenge, "code_challenge_method": "S256", "resource": "https://example.test/mcp",
        })
        assert authorization.status_code == 302
        request_id = parse_qs(urlparse(authorization.headers["location"]).query)["request"][0]
        page = client.get("/approve", params={"request": request_id})
        assert page.status_code == 200 and "read-only project evidence" in page.text
        assert page.headers["x-frame-options"] == "DENY"
        assert "form-action 'self'" in page.headers["content-security-policy"]
        assert client.post("/approve", data={"request": request_id, "secret": "wrong"}).status_code == 403
        approved = client.post("/approve", data={"request": request_id, "secret": "A" * 32})
        code = parse_qs(urlparse(approved.headers["location"]).query)["code"][0]
        token = client.post("/token", data={
            "grant_type": "authorization_code", "code": code,
            "redirect_uri": "https://client.example/callback", "client_id": registered["client_id"],
            "client_secret": registered["client_secret"], "code_verifier": verifier,
            "resource": "https://example.test/mcp",
        })
        assert token.status_code == 200

        initialize = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
            "protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "test", "version": "1"}}}
        accept = {"host": "example.test", "accept": "application/json, text/event-stream"}
        assert client.post("/mcp", headers=accept, json=initialize).status_code == 401
        accept["authorization"] = "Bearer " + token.json()["access_token"]
        initialized = client.post("/mcp", headers=accept, json=initialize)
        assert initialized.status_code == 200
        assert initialized.json()["result"]["protocolVersion"] == "2025-06-18"
    finally:
        client.close()
        process.terminate()
        process.wait(timeout=10)

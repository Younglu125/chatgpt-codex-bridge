"""Small owner-approved OAuth 2.1 provider for the private HTTPS MCP endpoint."""
from __future__ import annotations

import html
import os
import secrets
import stat
import time
from hashlib import sha256
from pathlib import Path
from urllib.parse import parse_qs

from mcp.server.auth.provider import (
    AccessToken,
    AuthorizationCode,
    AuthorizationParams,
    OAuthAuthorizationServerProvider,
    RegistrationError,
    RefreshToken,
    construct_redirect_uri,
)
from mcp.shared.auth import OAuthClientInformationFull, OAuthToken
from starlette.requests import Request
from starlette.responses import HTMLResponse, RedirectResponse, Response


class OwnerApprovedOAuth(OAuthAuthorizationServerProvider[AuthorizationCode, RefreshToken, AccessToken]):
    """Dynamic registration + PKCE with a local owner approval secret.

    OAuth clients may register, but no token is issued until the owner enters the
    secret kept in a 0600 local file. State is intentionally process-local: a
    restart revokes clients and tokens and requires reconnecting the private app.
    """

    def __init__(self, public_url: str, owner_secret_file: Path):
        self.public_url = public_url.rstrip("/")
        self.resource_url = self.public_url + "/mcp"
        self.owner_secret_file = owner_secret_file
        self.clients: dict[str, OAuthClientInformationFull] = {}
        self.pending: dict[str, tuple[str, AuthorizationParams, float]] = {}
        self.failed_approvals: dict[str, int] = {}
        self.codes: dict[str, AuthorizationCode] = {}
        self.access_tokens: dict[str, AccessToken] = {}
        self.refresh_tokens: dict[str, RefreshToken] = {}

    def _owner_secret_hash(self) -> bytes:
        info = self.owner_secret_file.stat()
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) & 0o077:
            raise RuntimeError("owner approval secret must be a current-user 0600 regular file")
        secret = self.owner_secret_file.read_text(encoding="utf-8").strip()
        if len(secret) < 24:
            raise RuntimeError("owner approval secret is missing or too short")
        return sha256(secret.encode()).digest()

    async def get_client(self, client_id: str) -> OAuthClientInformationFull | None:
        return self.clients.get(client_id)

    async def register_client(self, client_info: OAuthClientInformationFull) -> None:
        assert client_info.client_id
        if client_info.client_id not in self.clients and len(self.clients) >= 64:
            raise RegistrationError("invalid_client_metadata", "client registration limit reached")
        self.clients[client_info.client_id] = client_info

    async def authorize(self, client: OAuthClientInformationFull, params: AuthorizationParams) -> str:
        assert client.client_id
        now = time.time()
        self.pending = {key: value for key, value in self.pending.items() if value[2] >= now}
        if len(self.pending) >= 32:
            oldest = min(self.pending, key=lambda key: self.pending[key][2])
            self.pending.pop(oldest, None)
            self.failed_approvals.pop(oldest, None)
        request_id = secrets.token_urlsafe(32)
        self.pending[request_id] = (client.client_id, params, now + 300)
        return f"{self.public_url}/approve?request={request_id}"

    def approval_page(self, request_id: str) -> Response:
        pending = self.pending.get(request_id)
        if not pending or pending[2] < time.time():
            self.pending.pop(request_id, None)
            return HTMLResponse("Authorization request expired.", status_code=400)
        page = f"""<!doctype html><meta charset='utf-8'><title>Approve Project Evidence</title>
<style>body{{font:16px system-ui;max-width:620px;margin:10vh auto;padding:24px}}input,button{{font:inherit;padding:10px;width:100%;box-sizing:border-box;margin-top:12px}}code{{background:#eee;padding:2px 5px}}</style>
<h1>Approve read-only project evidence</h1>
<p>This grants the requesting ChatGPT private app access only to explicitly prepared, frozen MCP snapshots. It cannot run commands or edit files.</p>
<form method='post' action='/approve'><input type='hidden' name='request' value='{html.escape(request_id)}'>
<label>Owner approval secret<input type='password' name='secret' autocomplete='one-time-code' required></label>
<button type='submit'>Approve</button></form>"""
        return HTMLResponse(page, headers=self._html_headers())

    @staticmethod
    def _html_headers() -> dict[str, str]:
        return {
            "Cache-Control": "no-store",
            "Content-Security-Policy": "default-src 'none'; style-src 'unsafe-inline'; form-action 'self'; frame-ancestors 'none'",
            "Referrer-Policy": "no-referrer",
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
        }

    async def approve(self, request: Request) -> Response:
        raw = await request.body()
        if len(raw) > 4096:
            return HTMLResponse("Approval request too large.", status_code=413, headers=self._html_headers())
        body = parse_qs(raw.decode("utf-8", "strict"))
        request_id = body.get("request", [""])[0]
        supplied = body.get("secret", [""])[0]
        pending = self.pending.get(request_id)
        if not pending or pending[2] < time.time():
            self.pending.pop(request_id, None)
            self.failed_approvals.pop(request_id, None)
            return HTMLResponse("Authorization request expired.", status_code=400, headers=self._html_headers())
        if not secrets.compare_digest(sha256(supplied.encode()).digest(), self._owner_secret_hash()):
            failures = self.failed_approvals.get(request_id, 0) + 1
            self.failed_approvals[request_id] = failures
            if failures >= 5:
                self.pending.pop(request_id, None)
                self.failed_approvals.pop(request_id, None)
                return HTMLResponse("Too many failed attempts; authorization request revoked.", status_code=429, headers=self._html_headers())
            return HTMLResponse("Approval secret rejected.", status_code=403, headers=self._html_headers())
        client_id, params, _ = self.pending.pop(request_id)
        self.failed_approvals.pop(request_id, None)
        code = AuthorizationCode(
            code=secrets.token_urlsafe(32),
            client_id=client_id,
            scopes=params.scopes or ["mcp:read"],
            expires_at=time.time() + 300,
            code_challenge=params.code_challenge,
            redirect_uri=params.redirect_uri,
            redirect_uri_provided_explicitly=params.redirect_uri_provided_explicitly,
            resource=params.resource or self.resource_url,
            subject="owner",
        )
        self.codes[code.code] = code
        return RedirectResponse(construct_redirect_uri(str(params.redirect_uri), code=code.code, state=params.state), status_code=302)

    async def load_authorization_code(self, client: OAuthClientInformationFull, authorization_code: str) -> AuthorizationCode | None:
        code = self.codes.get(authorization_code)
        if not code or code.client_id != client.client_id or code.expires_at < time.time():
            return None
        return code

    def _mint(self, client_id: str, scopes: list[str], resource: str | None, subject: str | None) -> OAuthToken:
        access_value = secrets.token_urlsafe(32)
        refresh_value = secrets.token_urlsafe(40)
        now = int(time.time())
        resource = resource or self.resource_url
        self.access_tokens[access_value] = AccessToken(token=access_value, client_id=client_id, scopes=scopes,
            expires_at=now + 3600, resource=resource, subject=subject)
        self.refresh_tokens[refresh_value] = RefreshToken(token=refresh_value, client_id=client_id, scopes=scopes,
            expires_at=now + 30 * 86400, resource=resource, subject=subject)
        return OAuthToken(access_token=access_value, refresh_token=refresh_value, token_type="Bearer",
            expires_in=3600, scope=" ".join(scopes))

    async def exchange_authorization_code(self, client: OAuthClientInformationFull, authorization_code: AuthorizationCode) -> OAuthToken:
        self.codes.pop(authorization_code.code, None)
        return self._mint(authorization_code.client_id, authorization_code.scopes,
            authorization_code.resource, authorization_code.subject)

    async def load_access_token(self, token: str) -> AccessToken | None:
        value = self.access_tokens.get(token)
        if value and (value.expires_at is None or value.expires_at >= time.time()):
            return value
        self.access_tokens.pop(token, None)
        return None

    async def load_refresh_token(self, client: OAuthClientInformationFull, refresh_token: str) -> RefreshToken | None:
        value = self.refresh_tokens.get(refresh_token)
        if value and value.client_id == client.client_id and (value.expires_at is None or value.expires_at >= time.time()):
            return value
        self.refresh_tokens.pop(refresh_token, None)
        return None

    async def exchange_refresh_token(self, client: OAuthClientInformationFull, refresh_token: RefreshToken, scopes: list[str]) -> OAuthToken:
        self.refresh_tokens.pop(refresh_token.token, None)
        selected = scopes or refresh_token.scopes
        if not set(selected).issubset(refresh_token.scopes):
            raise ValueError("refresh scope escalation rejected")
        return self._mint(refresh_token.client_id, selected, refresh_token.resource, refresh_token.subject)

    async def revoke_token(self, token: AccessToken | RefreshToken) -> None:
        self.access_tokens.pop(token.token, None)
        self.refresh_tokens.pop(token.token, None)

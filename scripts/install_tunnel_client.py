"""Install the pinned official OpenAI Tunnel client for this Apple Silicon Mac.

Download from openai/tunnel-client releases, verify GitHub-published SHA256.
"""
import hashlib
import json
import os
from pathlib import Path
import platform
import urllib.request
import zipfile

VERSION = "v0.0.14"
SHA256 = "b540493c5bdbcdbb755700c8e2e16597e28b1569e425007e0f73111047bd6a64"
ASSET = "tunnel-client-v0.0.14-darwin-arm64.zip"
URL = "https://github.com/openai/tunnel-client/releases/download/" + VERSION + "/" + ASSET
if platform.system() != "Darwin" or platform.machine() != "arm64":
    raise RuntimeError("this pinned installer is for Darwin arm64; select the appropriate official asset on other systems")
runtime = Path.home() / ".local/share/chatgpt-codex-bridge/runtime"
archive = runtime / "downloads" / ASSET
archive.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
if not archive.exists():
    temporary = archive.with_suffix(".download")
    size = 0
    with urllib.request.urlopen(URL, timeout=30) as response, temporary.open("wb") as output:
        while chunk := response.read(1024 * 1024):
            size += len(chunk)
            if size > 64 * 1024 * 1024: raise RuntimeError("unexpected archive size")
            output.write(chunk)
    temporary.replace(archive)
if hashlib.sha256(archive.read_bytes()).hexdigest() != SHA256:
    raise RuntimeError("official archive checksum mismatch; do not run it")
destination = runtime / "bin"
destination.mkdir(parents=True, exist_ok=True, mode=0o700)
with zipfile.ZipFile(archive) as package:
    for name in ["tunnel-client", "cloudflared", "cloudflared-manifest.json", "LICENSE", "NOTICE", ASSET.removesuffix(".zip") + "-licenses.txt", ASSET.removesuffix(".zip") + ".spdx.json"]:
        # Explicit names, no arbitrary zip paths or symlinks extracted.
        data = package.read(name)
        path = destination / name
        path.write_bytes(data)
        path.chmod(0o700 if name in {"tunnel-client", "cloudflared"} else 0o600)
(runtime / "installation.json").write_text(json.dumps({"version": VERSION, "source": URL, "sha256": SHA256}, indent=2))
print(json.dumps({"client": str(destination / "tunnel-client"), "version": VERSION, "sha256_verified": True}, indent=2))

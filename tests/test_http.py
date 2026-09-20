import asyncio
from pathlib import Path
import socket
import subprocess
import sys
import time

import httpx
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

from bridge import Store


def test_actual_http_mcp_and_host_origin_guards(tmp_path):
    root = tmp_path / "project"; root.mkdir()
    (root / "source.py").write_text("value = 42\n")
    store = Store(tmp_path / "state"); store.register("http-fixture", root)
    job = store.prepare("http-fixture", "inspect source", "mcp")
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0)); port = sock.getsockname()[1]
    process = subprocess.Popen([sys.executable, str(Path(__file__).resolve().parents[1] / "server.py"),
                                "--state", str(store.state), "--transport", "streamable-http", "--port", str(port)],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    url = f"http://127.0.0.1:{port}/mcp"
    try:
        for _ in range(60):
            try:
                with socket.create_connection(("127.0.0.1", port), timeout=0.1): break
            except OSError:
                if process.poll() is not None: raise RuntimeError("HTTP server exited")
                time.sleep(0.05)
        else: raise RuntimeError("HTTP server did not start")
        # Local probes must bypass this machine's outbound proxy configuration.
        hostile_host = httpx.post(url, headers={"host": "evil.example", "accept": "application/json, text/event-stream"}, json={}, trust_env=False)
        assert hostile_host.status_code == 421
        hostile_origin = httpx.post(url, headers={"origin": "https://evil.example", "accept": "application/json, text/event-stream"}, json={}, trust_env=False)
        assert hostile_origin.status_code == 403

        async def run():
            async with httpx.AsyncClient(trust_env=False) as client:
                async with streamable_http_client(url, http_client=client) as (reader, writer, _):
                    async with ClientSession(reader, writer) as session:
                        await session.initialize()
                        result = await session.call_tool("bridge_read", {"job_id": job["id"], "path": "source.py", "start_line": 1, "end_line": 1})
                        assert not result.isError
                        assert result.structuredContent["lines"] == [{"line": 1, "text": "value = 42"}]
                        result = await session.call_tool("bridge_read", {"job_id": job["id"], "path": "source.py", "start_line": 1, "end_line": 999})
                        assert result.isError
        asyncio.run(run())
    finally:
        process.terminate()
        process.wait(timeout=10)

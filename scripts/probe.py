"""Real SDK initialize/list/call probe against the installed stdio server."""
import argparse
import asyncio
from pathlib import Path
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("job_id"); parser.add_argument("--state")
    args = parser.parse_args()
    command = [str(Path(__file__).resolve().parents[1] / "server.py")]
    if args.state: command += ["--state", args.state]
    async with stdio_client(StdioServerParameters(command=sys.executable, args=command)) as (reader, writer):
        async with ClientSession(reader, writer) as session:
            await session.initialize()
            tools = await session.list_tools()
            print("tools:", ", ".join(t.name for t in tools.tools))
            result = await session.call_tool("bridge_overview", {"job_id": args.job_id})
            if result.isError: raise RuntimeError(result.content)
            data = result.structuredContent
            if data is None: raise RuntimeError("missing structured MCP result")
            print("snapshot:", data["fingerprint"], "files:", len(data["files"]), "frozen:", data["frozen"])


if __name__ == "__main__": asyncio.run(main())

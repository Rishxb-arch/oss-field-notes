"""Probe the public hosted endpoint (no auth) with list_tools + read-only search_docs/get_context."""
import asyncio, sys, time, json
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client
URL = "https://mcp.byteask.ai/mcp"
QUERIES = sys.argv[1:] or ["FC16"]
async def main():
    async with streamable_http_client(URL) as (r, w):
        async with ClientSession(r, w) as s:
            init = await s.initialize()
            print("server:", init.server_info)
            tools = await s.list_tools()
            print("tools:", [t.name for t in tools.tools])
            for q in QUERIES:
                t0 = time.time()
                res = await s.call_tool("search_docs", {"query": q, "limit": 3})
                txt = "".join(c.text for c in res.content if hasattr(c, "text"))
                print(f"\n===== {q!r} ({time.time()-t0:.1f}s)\n{txt[:1800]}")
asyncio.run(main())

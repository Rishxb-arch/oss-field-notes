import asyncio, sys
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client
async def main():
    async with streamable_http_client("https://mcp.byteask.ai/mcp") as (r, w):
        async with ClientSession(r, w) as s:
            await s.initialize()
            for q in sys.argv[1:]:
                res = await s.call_tool("search_docs", {"query": q, "limit": 3})
                txt = "".join(c.text for c in res.content if hasattr(c, "text"))
                import re
                print("==",q); print("\n".join(l[:200] for l in txt.splitlines() if l.startswith("### ") or "_ref" in l))
asyncio.run(main())

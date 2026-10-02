import asyncio
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
async def main():
    async with streamablehttp_client("https://mcp.byteask.ai/mcp") as (r, w, _):
        async with ClientSession(r, w) as s:
            await s.initialize()
            for rid in ["p0_23:27:14:14", "p0_28:4.4:32:1"]:
                res = await s.call_tool("get_context", {"result_id": rid})
                txt = "".join(c.text for c in res.content if hasattr(c, "text"))
                print(f"== get_context {rid} -> {len(txt)} chars\n{txt[:600]}\n")
asyncio.run(main())

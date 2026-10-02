import asyncio, re, sys
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
async def main():
    async with streamablehttp_client("https://mcp.byteask.ai/mcp") as (r, w, _):
        async with ClientSession(r, w) as s:
            await s.initialize()
            for q in ["SYST_FOOBAR register reset value", "SYST_FOOBAR register reset value", "FC06 write single register"]:
                res = await s.call_tool("search_docs", {"query": q, "limit": 2})
                txt = "".join(c.text for c in res.content if hasattr(c, "text"))
                print(f"===== {q}\n{txt[:1500]}\n")
                refs = re.findall(r"_ref: `([^`]+)`_", txt)
            print("refs:", refs)
            res = await s.call_tool("get_context", {"result_id": refs[0]})
            txt = "".join(c.text for c in res.content if hasattr(c, "text"))
            print("get_context ->", len(txt), "chars\n", txt[:700])
asyncio.run(main())

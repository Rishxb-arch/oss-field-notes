"""Read-only probe of the public endpoint: identifier queries, out-of-corpus queries, get_context."""
import asyncio, re, time, json
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
URL = "https://mcp.byteask.ai/mcp"
Q = [
 ("id", "0x10"), ("id", "FC06"), ("id", "Modbus exception code 02"), ("id", "*IDN?"),
 ("id", "IEEE 1547 clause 6.4.1"), ("id", "SYST_RVR reload value maximum"),
 ("id", "CONTROL.SPSEL"),
 ("absent", "RP2040 SIO CPUID register offset"),
 ("absent", "ESP32 GPIO_ENABLE_W1TS_REG address"),
 ("absent", "nRF52840 RADIO TXPOWER register"),
 ("fake", "SYST_FOOBAR register reset value"),
 ("fake", "Modbus function code 0x7E Quantum Flux Write"),
 ("offtopic", "how do I bake sourdough bread"),
]
async def main():
    out = []
    async with streamablehttp_client(URL) as (r, w, _):
        async with ClientSession(r, w) as s:
            await s.initialize()
            first_ref = None
            for kind, q in Q:
                t0 = time.time()
                res = await s.call_tool("search_docs", {"query": q, "limit": 3})
                txt = "".join(c.text for c in res.content if hasattr(c, "text"))
                heads = re.findall(r"^### (.+)$", txt, re.M)
                nomatch = "No confident match" in txt
                refs = re.findall(r"_ref: `?([^`_]+)`?_", txt)
                first_ref = first_ref or (refs[0] if refs else None)
                rec = dict(kind=kind, q=q, secs=round(time.time()-t0, 1), no_match=nomatch, hits=heads[:3],
                           first_snippet=(txt.split("\n> ",1)[1][:220] if "\n> " in txt else ""))
                out.append(rec); print(json.dumps(rec, ensure_ascii=False), flush=True)
            if first_ref:
                res = await s.call_tool("get_context", {"result_id": first_ref})
                txt = "".join(c.text for c in res.content if hasattr(c, "text"))
                print("\nget_context", first_ref, "->", len(txt), "chars:", txt[:300].replace("\n"," | "))
            res = await s.call_tool("get_context", {"result_id": "does-not-exist"})
            print("get_context bogus ->", "".join(c.text for c in res.content if hasattr(c,'text'))[:200])
    json.dump(out, open("../hosted_eval.json","w"), indent=1, ensure_ascii=False)
asyncio.run(main())

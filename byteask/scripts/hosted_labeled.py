"""Labeled probe of the public endpoint (read-only search_docs). Saves full markdown per query."""
import asyncio, json, time
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
REAL = ["SYST_CSR COUNTFLAG", "SYST_RVR reload value", "SYST_CVR current value register", "CONTROL.SPSEL",
        "FC16 write multiple registers", "FC06", "0x10 write multiple registers", "Modbus exception code 0x02",
        "*IDN?", "*RST", "ESP32 GPIO_ENABLE_W1TS_REG", "STM32F4 RCC_CR HSEON bit", "ESP32 UART_CLKDIV_REG",
        "STM32F4 GPIOx_MODER reset value"]
FAKE = ["SYST_FOOBAR register reset value", "Modbus function code 0x7E Quantum Flux Write", "STM32F4 RCC_ZZTOP register",
        "ESP32 GPIO_TELEPORT_REG address", "RP2040 SIO_CPUID offset", "nRF52840 NRF_RADIO TXPOWER",
        "Cortex-M4 SYST_WARP bit", "SCPI command :FLUX:CAPacitor?"]
async def main():
    out = []
    async with streamablehttp_client("https://mcp.byteask.ai/mcp") as (r, w, _):
        async with ClientSession(r, w) as s:
            await s.initialize()
            for label, qs in (("real", REAL), ("fake", FAKE)):
                for q in qs:
                    t0 = time.time()
                    res = await s.call_tool("search_docs", {"query": q, "limit": 5})
                    txt = "".join(c.text for c in res.content if hasattr(c, "text"))
                    out.append(dict(label=label, q=q, secs=round(time.time()-t0, 2), text=txt))
                    print(label, q, "no_match" if "No confident match" in txt else "HITS", round(time.time()-t0,1), flush=True)
    json.dump(out, open("../hosted_labeled.json", "w"), indent=1, ensure_ascii=False)
asyncio.run(main())

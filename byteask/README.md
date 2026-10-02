# ByteAsk

Notes from using the public [ByteAsk](https://byteask.ai) MCP endpoint (`https://mcp.byteask.ai/mcp`) read-only, and from
running and patching the open-source server
[ByteAsk/ByteAsk-Embedded-MCP](https://github.com/ByteAsk/ByteAsk-Embedded-MCP) (MIT).

Most of it worked: no sign-up is needed, the stdio/HTTP MCP design is clean, there are 16 offline tests, and page-cited
hits for Modbus FC16, SysTick and SCPI `*IDN?` were exactly right. This folder records the rough edges.

## Environment

| | |
|---|---|
| Hosted endpoint | reports `serverInfo` name `code-search-mcp`, version `1.28.0` (the OSS README calls it `byteask-embedded-docs`) |
| OSS server | `ByteAsk-Embedded-MCP` @ `e7103ad` (HEAD, unchanged since 20 Jun 2026), Python 3.12, `uv sync` |
| Clients | Python `mcp` SDK; `scripts/hosted_probe.py` needs the older SDK API (`streamablehttp_client`), `hosted_probe_mcp2x.py` and `hosted_probe_headers.py` use the current 2.x API |
| Accounts / keys | none. Only `initialize`, `list_tools`, `search_docs` and `get_context` were called on the hosted server. `request_document` was never called, and the ByteAsk CLI was not run |

Dates: the hosted-endpoint findings 1-3 were first seen on 26 Sep 2026 and re-run on 2 Oct 2026; the OSS patch was
re-tested on 2 Oct 2026 (19/19 tests pass).

## Findings on the hosted endpoint

All of them use `search_docs` and the `get_context` result ids it returns.

### 1. Bare identifiers can miss

```bash
python scripts/hosted_probe_mcp2x.py "FC06" "FC06 write single register"
```
`"FC06"` returns Intel SDM `RELOAD_FC0` pages (a lexical sub-word match); `"FC06 write single register"` finds the Modbus
function. Likewise `"0x10"` returns ESP32 SLC / STM32 HASH / Intel pages. Across 13 real identifier queries the top hit
contained the queried identifier in about 8 (`evidence/hosted_labeled_summary.json`, `evidence/hosted_eval.json`).
Other misses: for `ESP32 UART_CLKDIV_REG` the top snippet is OCR noise from a rotated register diagram; for
`STM32F4 RCC_CR HSEON` the snippet shows `HSEBYP`; for `CONTROL.SPSEL` the snippet is cut before the SPSEL bit.

### 2. Some invented identifiers get a confident, cited hit

```bash
python scripts/hosted_probe_mcp2x.py "SYST_FOOBAR register reset value" "Modbus function code 0x7E Quantum Flux Write"
```
`SYST_FOOBAR ...` returns the real `SYST_CSR` section and `Modbus function code 0x7E Quantum Flux Write` returns the
Modbus serial-line CRC table, instead of "no confident match". The same query gives the same result when repeated
(`evidence/hosted_detail.txt`). The other fabricated or out-of-corpus queries were refused correctly: 6 of 8 in the
labelled run (`RCC_ZZTOP`, `GPIO_TELEPORT_REG`, `RP2040 SIO_CPUID`, `NRF_RADIO`, `SYST_WARP`, `:FLUX:CAPacitor?`). The
opposite miss also happens: the in-corpus query "IEEE 1547 clause 6.4.1" was flagged no_match.

### 3. Section labels come from body lines

Headings are parsed from lines of body text, so labels are garbled:

- Modbus FC16 (p.30) is labelled "§5 Currently in Listen Only Mode"; it is really §6.12.
- FC06 is labelled "§27 is the MSB of this byte, and output 20 is the LSB."
- Others: "§3 Park Avenue, New York, NY 10016-5997, USA", "§2 ns duration.", "§4 are sorted into 3 bins:".
- Consequence: `get_context("p0_23:27:14:14")` (the FC06 hit) returns a 29,340-character "section" spanning pp.12-22
  (`evidence/hosted_ctx.txt`).

Also noted but not claimed as a bug: a search takes about 3-4 s (the first call 10-14 s) on a shared box, and the hosted
`_ref:` format differs from the OSS renderer.

## Findings in the OSS server, with a patch

[`byteask-embedded-mcp-fixes.patch`](byteask-embedded-mcp-fixes.patch) is plain `git diff` output against `e7103ad`
(`git apply byteask-embedded-mcp-fixes.patch`). It fixes three things and adds `tests/test_fixes.py` (3 tests). Baseline: 16/16
tests pass; with the patch: 19/19.

1. **`QueryLogger` is never called.** The class exists and the README documents `BYTEASK_LOGS` query logs, but nothing outside
   `obs.py` calls it, so no `logs/queries.jsonl` is written. The patch wires it into `search_docs` and `get_context`.
2. **Project root is wrong when pip/uvx-installed.** `config._project_root()` resolves to `<venv>/lib/python3.12/`, so `.env` is
   looked up there and `document_requests.jsonl` was actually written there. The patch falls back to the current directory when
   not in a source checkout and adds a `BYTEASK_ROOT` override.
3. **Bearer check.** It is a plain `==` and the `Bearer` scheme is case-sensitive. The patch makes the scheme
   case-insensitive and compares with `hmac.compare_digest`.

Not patched: the local `request_document` tells self-hosters "we aim to add within 24 hours" even though it only writes a
local file; and the sample backend's keyword overlap matches generic words such as "register".

## An experiment that is not a fix

`scripts/identifier_guard_eval.py` tries an offline "the identifier must appear verbatim in the top hit" reranker over the 22
labelled queries. It scored 19/22, against 20/22 for the endpoint as-is, so it does **not** help. It is shared as an eval
set only. It reads the full responses (`hosted_labeled.json`), which are not included here because they quote third-party
manuals at length; regenerate them with `python scripts/hosted_labeled.py` (it writes `../hosted_labeled.json`, so run it
from inside `scripts/`), or use `evidence/hosted_labeled_summary.json` for the queries, labels and hit titles.

## Known issues check

On 26 Sep 2026 the OSS repo had only two issues, both third-party directory/badge spam, and no pull requests. None of the
above was reported there. The hosted endpoint has no public tracker.

## Files

| Path | What |
|---|---|
| `byteask-embedded-mcp-fixes.patch` | OSS patch (query log, project root, bearer check) + 3 tests |
| `scripts/hosted_*.py` | read-only probes of the hosted endpoint (`hosted_labeled.py` writes the labelled 22-query run) |
| `scripts/identifier_guard_eval.py` | the offline reranker experiment above |
| `evidence/hosted_ctx.txt`, `hosted_detail.txt`, `hosted_eval.json` | trimmed outputs of the probes (short quotes of documentation text) |
| `evidence/hosted_labeled_summary.json` | the 22 labelled queries, whether each was no_match, and the titles of the hits (no body text) |

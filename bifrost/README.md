# Bifrost (Maxim AI)

Notes from running [Bifrost](https://github.com/maximhq/bifrost), Maxim AI's open-source (Apache-2.0) Go LLM gateway, in front
of local [Ollama](https://ollama.com) models, the way an app team would: one OpenAI-compatible endpoint plus the Anthropic
drop-in endpoint, all CPU-backed. One reproducible rough edge and a small patch with a Go test.

What worked well: zero to a working gateway in a few minutes (`npx -y @maximhq/bifrost` plus a 10-line `config.json`;
`/v1/models` auto-discovered the local Ollama models). The Anthropic drop-in over a local model was impressively complete
(messages, SSE stream events, `tool_use` blocks, system and multi-turn). Request-level `fallbacks` worked and the response reports
the served model. Parameter parity with direct Ollama (stop, seed, logprobs / top_logprobs, `dimensions` on embeddings) was exact,
and the built-in SQLite request log made debugging easy.

## Environment

| | |
|---|---|
| Bifrost | `npx @maximhq/bifrost` wrapper 1.6.3 -> transport **v2.2.3** (`GET /api/version`); source checked at `maximhq/bifrost` `dev` @ `3123f05` (2 Oct 2026; earlier look at `09be2e6`, 25 Sep) |
| Ollama | 0.34.4 with `qwen2.5:0.5b-instruct`, `qwen2.5:1.5b-instruct`, `nomic-embed-text` |
| Clients | openai-python 2.x, anthropic-python 1.8.0 |
| Hardware | Linux x86_64, 8 vCPU, no GPU, shared and heavily loaded (load average 10-30), so there are no latency claims here |
| Go (for the patch test) | Go 1.24 |

## What I ran

| Script | What |
|---|---|
| `01_gateway_tests.py` | chat, streaming + `include_usage`, `json_schema`, tool calling, embeddings (base64 and float), bad model, empty messages, 10 concurrent requests |
| `02_fallback_anthropic.py` | request-level `fallbacks` (missing model -> fallback model); Anthropic SDK messages, stream, tools and multi-turn through `/anthropic` |
| `03_tool_parity.py`, `04_sniff_tools.py`, `sniff_proxy.py` | a logging reverse proxy between Bifrost and Ollama to compare the exact upstream tool-call payloads of the OpenAI and Anthropic paths |
| `05_misc.py`, `06_param_parity.py` | embeddings `dimensions`, Anthropic `count_tokens`, the `/litellm` route, text completions, Responses API, `/metrics`, stop / seed / logprobs parity |

The provider config is [`config/config.json`](config/config.json), the Ollama provider exactly as in the docs. Editing the `models`
allowlist and restarting applied correctly.

## The rough edge: `max_tokens` below 16 is silently raised to 16 for self-hosted providers

`ToOpenAIChatRequest` (`core/providers/openai/chat.go:46`) clamps `MaxCompletionTokens` to `MinMaxCompletionTokens = 16`
(`core/providers/openai/types.go:17`). Ollama, vLLM and SGLang go through that path, so small limits never reach the model.

Why it matters: `max_tokens=1..5` is a common pattern for yes/no classifiers, routers, judge labels and cheap health pings. Through
Bifrost these get up to 16 tokens, which costs more and can break parsers that expect one token, and there is no warning.

### Repro against a live gateway

```bash
# Ollama running with qwen2.5:0.5b-instruct; Bifrost started with:  npx -y @maximhq/bifrost -app-dir ./app -port 8080
#   (put config/config.json in ./app)
./repro_max_tokens.sh
```
Observed on v2.2.3 (the script prints `finish_reason` and completion tokens): `max_tokens=3` gives `length, 16 tokens` through Bifrost
and `3` direct to Ollama; `max_tokens=1` gave 3 tokens (`stop`) through Bifrost against 1 direct.

### Go test on `dev` @ `3123f05`

[`clamp_repro_test.go.txt`](clamp_repro_test.go.txt) (copy it into `core/providers/openai/` as `clamp_repro_test.go`) prints the wire
request after `ToOpenAIChatRequest`. Without the patch: OpenAI and vLLM requested 1 or 5 -> `max_completion_tokens=16`; **Ollama
requested 1 or 5 -> `max_tokens=16`**. With the patch: Ollama 1 -> 1 and 5 -> 5, vLLM likewise, and **OpenAI is still 16** (unchanged).

### Patch

[`patch-honour-small-max-tokens.diff`](patch-honour-small-max-tokens.diff) (17 lines, `git apply` against `dev` @ `3123f05`) skips the clamp
for Ollama, vLLM and SGLang. It compiles and the test above passes. `go test ./providers/openai` has one failure,
`TestRealtimeWebRTCUpstreamErrorCarriesRetryHint`, which **also fails without the patch** (unrelated). A maintainer may prefer a
different scope (for instance limiting the clamp to OpenAI reasoning models or to Responses only); I have not checked which
OpenAI-compatible endpoints actually enforce a minimum.

The floor is documented for OpenAI (`openai.mdx`: "Values below 16 are automatically set to 16"), but not for Ollama; the Ollama
page defers to the OpenAI page for chat.

Known? I searched issues and PRs (`max_tokens minimum 16`, `MaxCompletionTokens clamp 16 ollama`) and found nothing about the
floor for self-hosted providers. Related but different: #6132 (closed, Ollama `max_tokens` was dropped, fixed) and #4354 (closed;
documents the OpenAI floor of 16).

## Checked and NOT a Bifrost bug (recorded so I don't over-claim)

- Anthropic-path tool calls sometimes came back with nested args (`{"city":{"type":"string","value":"Pune"}}`) while the OpenAI path
  returned `{"city":"Pune"}`. The sniffing proxy showed **byte-identical upstream tool payloads** (`evidence/sniff_tool_payloads.jsonl`;
  only `max_tokens:200` differed), so this is small-model variance, not a conversion bug.
- `/v1/completions` echoing the prompt is Ollama's own behaviour.
- A docs nit I first noted (the Ollama page lists the Responses endpoint as `/v1/chat/completions`) was wrong: that column is the
  upstream endpoint, which is correct. Dropped.

## Smaller observation, not pursued

`POST /anthropic/v1/messages/count_tokens` for an Ollama model returned HTTP 400 with Anthropic error type `api_error`
("count_tokens is not supported by ollama provider") on v2.2.3. `api_error` is normally a server-side class, so an SDK that branches
on `error.type` would misclassify it. I could not find that string in the `dev` checkout, so it may already be gone.

## Not included

The SQLite config and log databases (about 85 MB, `config.db` / `logs.db`) and the upstream source tree.

# Dograh

Notes from self-hosting [Dograh](https://github.com/dograh-hq/dograh) (the open-source, self-hostable voice-agent platform)
fully locally with a local LLM, building an agent with the Python SDK, and driving it through the Test Chat API.

The Test Chat API is genuinely well designed (see "What worked well"), and BYOK with an OpenAI-compatible base URL
worked for real LLM turns with zero cloud keys. These are the rough edges I hit.

## What I built

- A local stack from the README one-liner (`docker-compose.yaml` + `start_docker.sh`), plus
  [`docker-compose.override.yaml`](docker-compose.override.yaml): host networking (only because bridge networking between
  containers was not available on my machine), no tunnel profile, telemetry off, the hosted-service URL pointed at a dead
  port, and the MinIO image swapped (see issue 1).
- BYOK model config via `PUT /api/v1/organizations/model-configurations/v2` ([`model_config.json`](model_config.json)): the LLM
  is the `openai` provider with `base_url` `http://127.0.0.1:11434/v1` (Ollama, `qwen2.5:1.5b-instruct`).
- [`build_and_chat.py`](build_and_chat.py): builds a 3-node **dental appointment-reminder agent** ("Asha", Sunrise Dental,
  Bengaluru) with the Python SDK `Workflow` builder (startCall -> reschedule agentNode -> endCall, natural-language edge
  conditions, `{{patient_name}}` / `{{appointment_date}}` template variables), creates it with `create_workflow`, and drives it
  through the Test Chat REST API (`/workflow/{id}/text-chat/sessions`, `/messages`, `/rewind`) with a Hinglish reschedule
  script, a prompt-injection turn and an off-topic medical question.

```bash
export DOGRAH_API_KEY=...   # an API key created in the Dograh UI
export DOGRAH_TOKEN=...     # the logged-in user's access token
python build_and_chat.py build            # prints the created workflow
python build_and_chat.py chat <workflow_id>
```

## Environment

| | |
|---|---|
| Date | 26 Sep 2026 (**not re-run on 2 Oct 2026**; the versions below may have moved on) |
| Dograh | `ghcr.io/dograh-hq/dograh-{api,ui}:latest`; `/api/v1/health` reports **1.47.0**. Repository `main` @ `3e66307` (25 Sep 2026) |
| SDK | `dograh-sdk` 0.1.8 from PyPI, and from repository `main` |
| LLM | Ollama, `qwen2.5:1.5b-instruct` (shared CPU-only machine, so no latency claims) |
| Python | 3.12 |

## Verified issues

### 1. The README quick start does not come up: the MinIO image cannot be pulled

`docker-compose.yaml` (line 60) uses `image: quay.io/minio/minio`.

```bash
curl -o docker-compose.yaml https://raw.githubusercontent.com/dograh-hq/dograh/main/docker-compose.yaml \
 && curl -o start_docker.sh https://raw.githubusercontent.com/dograh-hq/dograh/main/scripts/start_docker.sh \
 && chmod +x start_docker.sh && ./start_docker.sh
```
```
 minio Error unauthorized: access to the requested resource is not authorized
Error response from daemon: unauthorized: access to the requested resource is not authorized
```
([`evidence/minio_pull_error.txt`](evidence/minio_pull_error.txt).) `docker manifest inspect quay.io/minio/minio:latest` also
failed on that day, and `docker.io/minio/minio` answered `denied: requested access to the resource is denied`, including older
pinned tags. Quay itself was fine from the same host (`quay.io/prometheus/busybox` resolved).

**Known:** #761 (12 Sep) moved Docker Hub to quay.io and was closed on 15 Sep, so this looks like a regression of that fix.
No open issue found. **Workaround I used:** `cgr.dev/chainguard/minio:latest` (see the override file). It is distroless, so the
compose healthcheck (`curl -f .../minio/health/live`) has to change too. Which image source to use is your call.

### 2. The default quick start opens a public URL, and nothing says so

`start_docker.sh` runs `docker compose --profile tunnel up --pull always`. With no `CLOUDFLARE_TUNNEL_TOKEN`, `cloudflared`
runs `tunnel --url http://api:8000`, i.e. a public `*.trycloudflare.com` quick tunnel to the API. `ENABLE_SIGNUP` defaults
to `true`, and I confirmed that a second, unrelated account can sign up on the same instance
(`POST /api/v1/auth/signup` returned 200 and a new organization).

The README section "Download and setup Dograh on your Local Machine" doesn't mention the tunnel. The compose comments explain
it is there for inbound telephony webhooks, which makes sense. **Suggestion:** print the public URL plus a one-liner about
`ENABLE_SIGNUP=false`, or make the tunnel opt-in for laptop installs. Without the tunnel, the API logs
`Error connecting to cloudflared: Cannot connect to host cloudflared:2000` repeatedly. No existing issue found.

### 3. "Create from use case" needs Dograh's hosted service, even on a fully BYOK self-host

`POST /api/v1/workflow/create/template` calls the hosted service (`mps_service_key_client.call_workflow_api`). When it is
unreachable (air-gapped, or egress blocked) the response is
([`evidence/create_template_offline_500.json`](evidence/create_template_offline_500.json)):

```
HTTP 500 {"detail":"An unexpected error occurred: All connection attempts failed"}
```

with no hint of what it tried to reach. **Suggestion:** either a clear error ("template generation uses Dograh cloud; build
manually or via the SDK") or a BYOK-LLM fallback. Related: #152 (closed Feb 2026) explicitly kept the hosted client. No issue
for this error.

### 4. The PyPI SDK (0.1.8) cannot build agents against the current server

```bash
pip install dograh-sdk==0.1.8
DOGRAH_API_KEY=... python repro_sdk_version_mismatch.py
```
```
pydantic_core._pydantic_core.ValidationError: 23 validation errors for NodeSpec
properties.0.renderer_options
  Extra inputs are not permitted [type=extra_forbidden, input_value=None, input_type=NoneType]
...
graph_constraints.min_instances / max_instances, docs_url, nested properties   (all extra_forbidden)
```
([`evidence/sdk_0.1.8_nodespec_errors.txt`](evidence/sdk_0.1.8_nodespec_errors.txt).) Every `Workflow.add(...)` goes through
`client.get_node_type()`. Server 1.47.0 now emits `renderer_options` (17 times), `graph_constraints.min_instances` /
`max_instances` and `docs_url`, which the published SDK's generated models forbid.

The SDK at repository `main`, still labelled 0.1.8, already has those fields and works, so this probably just needs a version bump
and a publish (plus maybe a CI check that the published SDK validates against `/node-types`). The shipped example
`examples/python/build_workflow_with_sdk.py` hits the same thing. I did not pin down which commit introduced the fields. No
issue found.

### 5. Notes (not bugs)

- First signup on the OSS build mints a Dograh service key and provisions Cloudonix SIP on the hosted service. Offline it degrades
  gracefully (signup works, logs `Failed to bootstrap organization; will retry`), so this is an expectation / docs note.
- Signup rejects `.local` / `.test` email addresses ("special-use or reserved name") while `@corp.internal` passes; local evaluators
  tend to type `admin@local.test`.
- The text-chat turn timeout is hard-coded (`TEXT_CHAT_TURN_TIMEOUT_SECONDS = 60.0` in
  `api/services/workflow/text_chat_runner.py`) and surfaces as HTTP **500**, not 504
  ([`evidence/text_chat_turn_timeout_500.json`](evidence/text_chat_turn_timeout_500.json)). Caveat: my Ollama was on a shared
  CPU-only machine (a 10-token completion took ~37 s), so the timeouts themselves are mostly my environment. I am only suggesting
  that the timeout be configurable and return 504.

## What worked well

- Once MinIO was swapped, the stack came up healthy (api :8000, ui :3010), and `/api/v1/health` reports version, auth mode and
  `signup_enabled`.
- BYOK with an OpenAI-compatible `base_url` (Ollama) worked for real LLM turns with zero cloud keys, and per-turn token usage is
  recorded.
- Template variables from `initial_context` were substituted correctly in the greeting ("Hello Meera ... Monday, the 29th of
  September, at 10:30am"; [`evidence/test_chat_run.txt`](evidence/test_chat_run.txt)).
- The Test Chat API is well thought out: per-turn events (`node_transition`), `checkpoint_after_turn`, **rewind** to any completed
  turn (it discarded the 3 failed turns), optimistic concurrency (a stale `expected_revision` gives a clean
  `409 {"message":"Text chat session revision conflict","expected_revision":11,"actual_revision":12}`), empty text rejected with 422
  `min_length=1`, and failed turns recorded as `failed` with an `execution_error` event instead of vanishing.
- The SDK `Workflow` builder (repository `main`) is nice: typed node specs fetched from the server and readable
  `wf.edge(a, b, label=..., condition=...)`.

(The 1.5B model did not take the reschedule transition in my runs; that is model quality, not Dograh.)

## Files

| File | What it is |
|---|---|
| `build_and_chat.py` | build the agent with the SDK, then chat through the Test Chat API |
| `repro_sdk_version_mismatch.py` | minimal repro for issue 4 |
| `docker-compose.override.yaml` | the local override I used (MinIO swap, no tunnel, host networking) |
| `model_config.json` | BYOK config pointing at a local Ollama |
| `evidence/` | trimmed outputs |

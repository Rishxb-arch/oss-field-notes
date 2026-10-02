# Bolna

Notes from building a text-mode regression harness for a [Bolna](https://github.com/bolna-ai/bolna) agent with a local
LLM and no API keys, plus repros and a tested patch for the crashes I hit along the way.

Once it was running, the text channel was really clean, and the 1,955-test suite running in about a minute with no
network is great. This folder documents what stood in the way.

## What I built

`clinic_chat_harness.py`: a text-mode regression harness for an outbound appointment-reminder agent ("Asha", Sunrise
Dental, Bengaluru). It drives `AssistantManager(..., turn_based_conversation=True)` through an in-memory fake WebSocket
with a scripted conversation (a Hinglish reschedule, an empty turn, a prompt-injection attempt, a medical-advice
guardrail check), records per-turn time to first text, and can run N concurrent sessions. The LLM is a local model served
by Ollama via Bolna's `ollama` (litellm) provider, so everything runs with zero keys.

```bash
ollama pull qwen2.5:1.5b-instruct
python clinic_chat_harness.py --sessions 1        # needs the patched bolna, see below
```

## Environment

| | |
|---|---|
| OS / hardware | Linux x86_64, 8 vCPU (heavily shared, so no latency claims), no GPU, no microphone |
| Python | 3.12.14 (uv) |
| Bolna | `bolna==0.10.263` from PyPI; repo `HEAD` @ `3e2b2d3` (25 Sep 2026); the patch is against `3e2b2d3` |
| Other | websockets 15.0.1, litellm 1.84.0, Ollama with `qwen2.5:1.5b-instruct` / `0.5b-instruct`, no accounts or keys |

## Verified issues

Items 2, 3, 5 and 6 below were re-run in a clean venv on 2 Oct 2026 (outputs in [`evidence/`](evidence/)); items 1 and 4
come from the original runs on 26 Sep 2026 (also in `evidence/`).

### 1. `pip install bolna` fails on Python 3.13

`requires-python = ">=3.10"`, but the requirements pin `numpy==1.26.1` and `scipy==1.11.4`, which have no cp313 wheels, so
pip builds from source.

```bash
uv venv -p 3.13 && uv pip install bolna==0.10.263
```
```
error: Failed to build `numpy==1.26.1`
  ../../meson.build:1:0: ERROR: Unknown compiler(s): [['c++'], ['g++'], ...
hint: `numpy` (v1.26.1) was included because `bolna` (v0.10.263) depends on `numpy`
```
([`evidence/06_python313_install.txt`](evidence/06_python313_install.txt); the compiler error is because that machine had no C++
toolchain, but the root cause is the missing prebuilt wheels.) It installs fine on 3.12. Closest existing issue: #231
("Which is the Best Python version to use here?", open since 2025-07).

### 2. Both shipped examples fail at construction

`examples/text_only_assistant.py` and `examples/simple_assistant.py` pass `llm_config=SimpleLlmAgent(...)`, but
`LlmAgent.validate_llm_config` rejects non-dicts.

```bash
python 01_example_asis.py      # the example as shipped (OpenAI); 02_example_ollama.py is the same with a local model
```
```
pydantic_core._pydantic_core.ValidationError: 1 validation error for LlmAgent
llm_config
  Value error, llm_config must be a dict, got <class 'bolna.models.SimpleLlmAgent'> [type=value_error, ...]
```
([`evidence/01_examples_asis_llm_config.txt`](evidence/01_examples_asis_llm_config.txt).) No issue found.
**Fix (patch):** accept `BaseModel` instances via `value.model_dump()`.

### 3. The text-only `Assistant` path then crashes twice more

Passing the config as a dict (`03_example_dict.py`) gets past issue 2 and hits:

```
File ".../task_manager.py", line 1836, in __setup_synthesizer
    self.task_config["tools_config"]["transcriber"]["language"] == DEFAULT_LANGUAGE_CODE
TypeError: 'NoneType' object is not subscriptable
```
([`evidence/03_text_only_setup_synthesizer.txt`](evidence/03_text_only_setup_synthesizer.txt).) With the first crash fixed
(patch), the next one is:

```
File ".../task_manager.py", line 919, in __init__
    self.synthesizer_monitor_task = asyncio.create_task(self.tools["synthesizer"].monitor_connection())
KeyError: 'synthesizer'
```
([`evidence/04_after_patch_next_crash.txt`](evidence/04_after_patch_next_crash.txt).)

Also: `Assistant.execute()` calls `manager.run()` with `local=False`, so prompts are fetched from S3, and `add_task()` has no
way to pass a system prompt, `turn_based_conversation` or an input queue (the parameters are accepted but unused).

**Known (partly):** #897 / PR #907 "Fix Assistant pipelines for optional audio components" (open since 2026-07-30).
**The patch fixes only the first crash;** the `KeyError: 'synthesizer'` remains.

### 4. Text chat dies on the first user message for a text-only pipeline

With `pipelines=[["llm"]]` and `turn_based_conversation=True`, `DefaultInputHandler.__process_text` reads
`self.input_types["audio"]`:

```
KeyError: 'audio'
Error while handling websocket message: 'audio'
Conversation completed
```
([`evidence/02_keyerror_audio.txt`](evidence/02_keyerror_audio.txt).) The session ends silently; the client sees nothing.
**Known:** #898, with three open fix PRs (#874, #960, #907), none merged when I checked. **Fix (patch):** fall back to the
`text` input type.

### 5. Any non-OpenAI LLM still needs `OPENAI_API_KEY`

`StreamingContextualAgent.__init__` always builds `OpenAiLLM(model=CHECK_FOR_COMPLETION_LLM or llm.model)` and
`OpenAiLLM("gpt-4.1-mini")` for voicemail detection, so an Ollama-only agent fails at construction (and the *Ollama* model
name is sent to OpenAI for the completion check).

```bash
env -u OPENAI_API_KEY python clinic_chat_harness.py       # unpatched bolna
```
```
=== session 0 err=OpenAIError('Missing credentials. Please pass an `api_key`, `workload_identity`, `admin_api_key`, or set the `OPENAI_API_KEY` ...')
```
([`evidence/05_ollama_needs_openai_key.txt`](evidence/05_ollama_needs_openai_key.txt).) **Known:** #224 (2025-07, Groq) and open
PR #794 (2026-06); the construction-time failure and the hard-coded voicemail model are not mentioned there.
**Fix (patch):** create both helper LLMs lazily, and make end-of-call cleanup not instantiate them just to close them.

### 6. `local_setup/quickstart_client.py` cannot connect with the pinned `websockets`

```
websockets.connect(uri, open_timeout=None, extra_headers=headers)      # quickstart_client.py:163, websockets==15.0.1
TypeError: BaseEventLoop.create_connection() got an unexpected keyword argument 'extra_headers'
```
([`evidence/07_quickstart_client_websockets.txt`](evidence/07_quickstart_client_websockets.txt).) The argument was renamed
`additional_headers` in the new asyncio client. **Known:** reported in #231. Not covered by the patch.

## The patch

`bolna-text-mode-fixes.patch` (against `3e2b2d3`; applies cleanly to that commit; 4 files, +38/-7):

| Issue | Change |
|---|---|
| 2 | `models.py`: accept `BaseModel` instances for `llm_config` |
| 3 (first crash) | `task_manager.py`: tolerate a missing transcriber config in `__setup_synthesizer` |
| 4 | `input_handlers/default.py`: use the `text` input type when there is no `audio` one |
| 5 | `agent_types/contextual_conversational_agent.py` (+ cleanup in `task_manager.py`): lazy helper LLMs |

Full test suite with the patch: `1955 passed, 1 skipped` (pytest, 67 s, no `OPENAI_API_KEY` set). With the patch, the
harness runs a text chat against local Ollama with no keys at all
([`evidence/08_patched_run_no_key.txt`](evidence/08_patched_run_no_key.txt)).

Not counted as an issue: on a CPU-saturated machine, LLM turns sometimes exceeded Bolna's 60 s stall watchdog
(`LLM generation stuck for 60.0s ... - hanging up`); that was my environment. One detail worth knowing: on that hang-up the
text client only receives `<end_of_stream>`, with no reason or error event.

## What worked well

- Once patched, the turn-based text channel is clean: `<beginning_of_stream>` / `<end_of_stream>` framing,
  context substitution (`{patient_name}`, `{appointment_date}` into the prompt and welcome message) worked first try, and
  user turns sent mid-generation queue up in order instead of interleaving.
- The hermetic test suite (1,955 tests, about a minute, no network) is excellent, and the 60 s LLM-stall watchdog tears the
  call down cleanly instead of hanging forever.
- The litellm-backed `ollama` provider with `base_url` just worked.

## Files

| File | What it is |
|---|---|
| `01_example_asis.py` | the shipped text-only example (issue 2) |
| `02_example_ollama.py` | same, with a local Ollama model |
| `03_example_dict.py` | same, `llm_config` as a dict (issue 3) |
| `clinic_chat_harness.py` | the text-mode harness |
| `bolna-text-mode-fixes.patch` | the patch described above |
| `evidence/` | trimmed logs and outputs |

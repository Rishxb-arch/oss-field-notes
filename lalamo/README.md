# lalamo (Mirai)

Notes from trying [Mirai](https://github.com/trymirai)'s on-device stack from a Linux, CPU-only machine. `uzu` (the
inference engine) is Apple-only today, so I went through **lalamo**: converted Qwen3-0.6B, chatted with it, and ran
`lalamo server` for batched replies. The server design is nice (a resident model, clean 409 on a second batch, results
persisted to disk), but on a machine without device memory stats it cannot be used as shipped. There is a small patch.

## What I did

1. `uv run lalamo list-models`: fine, about 30 s from a fresh clone.
2. `lalamo convert Qwen/Qwen3-0.6B`: fine. Peak RSS about 3.7 GB; output `models/Qwen3-0.6B` (1.19 GB safetensors).
3. `lalamo chat models/Qwen3-0.6B --message "..." --temperature 0`: fine (1 m 53 s on a loaded machine).
4. `lalamo server` with batched requests (`POST /batches`, `GET /batches/{id}`): the issues below.

## Environment

| | |
|---|---|
| Machine | Linux x86_64, CPU only, heavily shared (load 16-27), so timings are noisy |
| lalamo | commit `2c182c5` (24 Sep 2026; PyPI 0.17.0). The patch is against this commit |
| uzu | commit `2095266` (read, plus the Python quickstart attempted) |
| Model | `Qwen/Qwen3-0.6B`, converted locally |

## Verified issues

Reproduce all three with [`repro_server.sh`](repro_server.sh) (it starts the server, posts the two request files, and prints
the results). Outputs from a re-run on 2 Oct 2026: [`evidence/server_unpatched_output.txt`](evidence/server_unpatched_output.txt),
[`evidence/server_patched_output.txt`](evidence/server_patched_output.txt).

### 1. `lalamo server` cannot run batches on CPU, and the suggested flag doesn't help

```bash
uv run --no-sync lalamo server
# Cannot get the default device's memory stats, use --vram-gb          (message observed in the original run)
uv run --no-sync lalamo server --vram-gb 3 --port 8293                 # starts fine
python run_batch.py batch_req.json                                      # POST /batches with 4 prompts
```
```
POST /batches -> 202 batch_8f4925
status=failed completed=0/4 after 5s error='Automatic batch size estimation is not supported because device memory statistics are unavailable. Specify --batch-size explicitly.'
```

The server-side traceback ([`evidence/server_unpatched_traceback.txt`](evidence/server_unpatched_traceback.txt)) ends in
`_get_device_memory_stats()` -> `RuntimeError: Automatic batch size estimation is not supported because device memory statistics are unavailable. Specify --batch-size explicitly.`
But there is no `--batch-size` option on `lalamo server`, or anywhere in the CLI; `server.py` hardcodes
`BatchSchedulerConfig(batch_size=None)`. So on CPU every batch fails, whichever flag you pass.

**Expected:** a way to set the batch size explicitly when memory stats are not available.
**Fix:** `lalamo-server-batch-size.patch` (about 25 lines in `main.py` and `server.py`) adds `--batch-size`, mutually exclusive with
`--vram-gb`, and passes it to `BatchSchedulerConfig`. With `--batch-size 2` the same 4 prompts complete (35 s in the re-run, 60-100 s on
a more loaded machine in the original runs):

```
status=completed completed=4/4 after 35s error=None
```

I couldn't find an existing issue: the repository had only 3 issues when I checked (#238, #316, #317), none about the server, CPU or stop
tokens.

### 2. Batch responses include the literal stop token

```
q2: response='Red<|im_end|>'
q0: response='The capital of France is **Paris**.<|im_end|>'         (reasoning_effort = no_reasoning; batch_req_nr.json)
```

**Cause (from reading the code):** `LanguageModel.trim_at_eos` keeps the EOS token (index + 1), and the Qwen3 output regex
`(?P<response>.*)\Z` captures it. `lalamo chat` doesn't show it because it streams text; `LanguageModel.reply()` appears to use the same
trim-and-decode path, but I didn't run it. **Expected:** the response text without `<|im_end|>`. Not reported as far as I could see.

### 3. No truncation signal: a cut-off reply looks like an empty one

With the default reasoning behaviour (Qwen3 thinks first) and `max_completion_tokens: 32`, every result is `response: ""` with the
chain of thought cut off mid-sentence:

```
q0: response=''
    chain_of_thought="\nOkay, the user is asking for the capital of France, and they mentioned it's one word. Let"...
```

There is no `finish_reason` / `truncated` field, so a client can't tell "cut off" from "empty". **Expected:** some indication that
generation stopped at the token limit. Not reported as far as I could see.

### 4. Minor

- `uv run lalamo` from a fresh clone syncs the whole dev group (a 2.8 GB `.venv`, 240 packages, including a `fish-speech` git
  dependency, tensorboard, memray and debugpy). `uv sync --no-dev --extra cpu --extra server` followed by `uv run --no-sync` avoids it.
- The `uzu` Python quickstart (`uv add uzu==0.5.30`) on Linux: "only has wheels for macosx_26_0_arm64, macosx_26_0_x86_64" (every release
  since at least 0.5.19), and the npm package is `os: darwin`. This is intentional (Package.swift targets 26.4; see the closed issues
  #841 and #499), so it is only a docs note: the README quickstarts don't state the OS requirement.
- Every batch on CPU logs a very large `Some donated buffers were not usable: bfloat16[...]` warning (about 200 shapes).
- The Pallas-to-XLA attention fallback warning and the `HF_TOKEN` warning each print twice.

## What worked well

- One-command conversion from a Hugging Face repo ID, and a clean model registry (`list-models`).
- The server design: a resident model, a clean `409` when a second batch is posted while one is running, batch IDs that can't be
  path-traversed (`GET /batches/../../etc/passwd` -> 404), results persisted to the cache directory.
- With `reasoning_effort: "no_reasoning"` all 4 answers were correct.

## Files

| File | What it is |
|---|---|
| `repro_server.sh` | step-by-step repro (stock vs patched server) |
| `run_batch.py` | posts a request file to a running server and prints the finished batch (standard library only) |
| `batch_req.json` | 4 prompts, default reasoning, `max_completion_tokens: 32` |
| `batch_req_nr.json` | the same with `reasoning_effort: "no_reasoning"` |
| `lalamo-server-batch-size.patch` | adds `--batch-size` to `lalamo server` |
| `evidence/` | outputs of the runs above |

Apply the patch inside a lalamo clone checked out at `2c182c5`: `git apply lalamo-server-batch-size.patch`.

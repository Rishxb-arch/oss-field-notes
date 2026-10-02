# Future AGI (agent-learning-kit)

Notes from building a small RAG-evaluation harness on
[`agent-learning-kit`](https://github.com/future-agi/agent-learning-kit) (formerly `ai-evaluation`; the Python package is
`agent-learning-kit`, the import namespace is `fi`), with local metrics and an LLM judge on a local Ollama model and no API keys.

What worked: the local metrics need no key and give clear reasons ("0/1 claims supported. 1 neutral"); an LLM-as-judge on a
local Ollama model worked first try through litellm model strings; the `litellm` provider in an `agent-learn eval` suite accepted
`api_base`, `temperature` and `system` directly; and the JSON / JUnit / SARIF / Markdown reports are a nice CI story. A typo'd metric
name fails clearly.

## Environment

| | |
|---|---|
| Package | `agent-learning-kit` 0.1.0 in the first runs (repo `future-agi/ai-evaluation` @ `458a8ee`); the rough edges below were re-checked on **0.2.2** (PyPI, repo HEAD `afac8e3`, 1 Oct 2026) on 2 Oct 2026, with the same results |
| Python | 3.12.14 |
| Local model | Ollama 0.34.x, `qwen2.5:1.5b-instruct` (shared, loaded CPU box: no latency claims) |
| Keys / accounts | none |

## What I built

1. [`01_rag_eval.py`](01_rag_eval.py): scores a 3-question support-bot RAG set (one answer is a deliberate hallucination) with
   `fi.evals.evaluate(..., engine="local")` (faithfulness, contains_valid_link, is_json, one_line) plus a custom LLM-as-judge
   prompt on Ollama (`engine="llm", model="ollama_chat/qwen2.5:1.5b-instruct"`). Output: [`evidence/01_rag_eval_output.txt`](evidence/01_rag_eval_output.txt).
2. [`suite/support_suite.json`](suite/support_suite.json): a promptfoo-style `agent-learn eval` suite with a `litellm` provider
   pointed at Ollama (system prompt = a store policy) and `contains`, `regex`, `not_contains` and `json_path_equals` assertions. It
   passed 3/3 cases and 4/4 assertions; reports are in `evidence/support_suite_result.{md,json}`.

## Rough edges (reproduced)

### 1. `--dry-run` does not validate assertion types; the real run fails only after all the provider calls

`agent-learn eval --help` says `--dry-run  Validate suite shape without executing providers`. A suite with `"type": "json-path"`
(normalised to `json_path`; the valid names are `json_path_equals`, `json_path_exists`, ...) gives `dry-run exit=0` and
`"score": 1.0`. The real run then makes every provider call and dies at the end with
`agent-learn eval: unsupported assertion type: json_path` and no partial results. (Against Ollama this was 1 min 38 s of work
first.)

```bash
./repro_dry_run_misses_bad_assertion.sh      # echo provider, so no model is needed
```
Patch: [`patch-validate-assertion-types-at-load.diff`](patch-validate-assertion-types-at-load.diff) checks the type in
`_normalize_assertion` (which runs at load and in dry-run) and suggests a name, e.g. ``assertion 1 in test `t1` has unsupported type
`json_path`; did you mean `json_path_contains`?`` (the first suggestion should really be `json_path_equals`: a small thing to polish).
With the patch, dry-run and the real run both fail at load, and the shipped `examples/eval_suite.json` still passes.

### 2. Missing required inputs come back as a normal "completed" result with score 0.0

```bash
python repro_invalid_inputs_score_zero.py
```
`evaluate("faithfulness", engine="local", output="...")` (no `context=`) returns `status=completed score=0.0 passed=False error=None`;
`groundedness` without `input=` does the same; the only hint is the `reason` string ("Input validation failed: ..."). A typo'd metric
name, by contrast, returns `status=failed`. In a CI gate, a mis-wired metric looks like a model regression.
Patch: [`patch-local-engine-fail-on-invalid-inputs.diff`](patch-local-engine-fail-on-invalid-inputs.diff) validates against
`metric.input_model` first and returns `status="failed", error="Invalid inputs for local metric 'faithfulness': ..."`. Valid and batch
calls were unchanged in my checks.

### 3. A stale install hint points at the old package and would downgrade the new one

Without `transformers`, faithfulness warns `For accurate NLI, install: pip install ai-evaluation[nli]` (also in `nli.py` and
`feedback/store.py`). `ai-evaluation` 1.1.0 is still on PyPI and ships the same `fi/` namespace: of its `.py` files, 252 overlap
`agent-learning-kit` 0.2.2's and 118 differ, so following the hint rewrites half of `fi.evals` in place. The right command is
`pip install "agent-learning-kit[nli]"`.

### 4. Pip users cannot run the README quickstart

The README says to install from PyPI and then run `agent-learn eval examples/eval_suite.json`, but the wheel ships no `examples/`:
`eval suite file not found`. `agent-learn init` scaffolds a working suite, but the README does not mention it. (From a git checkout
the quickstart works.)

### Smaller

- The base install is heavy (a 736 MB venv for 0.1.0): `claude-agent-sdk` (231 MB), `google-adk`, `retell-sdk`, `optuna` and `gepa` are
  hard dependencies even though extras exist.
- `fi/simulate/suite.py::_litellm_provider_output` sets `litellm.drop_params = True` globally on each call, a process-wide side effect
  for anyone else using litellm in the same process (seen in 0.1.0).
- `evaluate("groundedness", engine="llm", model="ollama_chat/...")` gives `LLMEngine requires a 'prompt' parameter`; the message
  could say that built-in metric names are not supported on the LLM engine and point to `prompt=` or `augment=True`.

### Not claimed

- The heuristic NLI scoring a direct contradiction as "neutral" (0.4): the warning says the fallback is approximate.
- Faithfulness returning 1.0 for an answer with no extractable claims, e.g. a wrong "Yes." to "Do you ship to Sri Lanka?". That is
  arguably by design, though a flag might be nice.

## Honest limits

- I did **not** manage to run the repository's full pytest suite (many environment-dependent failures, with and without the patches, and
  the run hung), so I am **not** claiming "existing tests pass" for the patches.
- Known issues: I searched the repo's issues and pull requests; nothing covered dry-run validation, input validation, the install hint
  or the quickstart.

## Files

| Path | What |
|---|---|
| `01_rag_eval.py`, `suite/support_suite.json` | the harness and the suite |
| `repro_dry_run_misses_bad_assertion.sh`, `repro_invalid_inputs_score_zero.py` | repros for rough edges 1 and 2 |
| `patch-*.diff` | the two patches (plain `git diff`, written against 0.1.0 / `458a8ee` and re-checked on 0.2.2 as described above) |
| `evidence/` | outputs of the harness and the suite run |

The upstream `examples/` directory (copied from the repo) is not included.

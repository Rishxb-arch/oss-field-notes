# Ringg AI

Notes from running two of the open [RinggAI](https://huggingface.co/RinggAI) transcript-analytics models on CPU over a small set
of synthetic Hinglish, Hindi and English collection calls, plus a look at the documented free Squirrel TTS endpoint.

What worked: the output was parseable JSON in every run, with no code fences or preamble. Devanagari and Hinglish input
produced fluent, accurate English summaries, key points and action items (amounts, dates, a transaction-ID prefix). Both
models are ungated; the 1.5B is Apache-2.0.

**This is n=6 synthetic transcripts and my own prompt (the model card does not give one). Treat the numbers as signals,
not a benchmark.**

## What was tested

| | |
|---|---|
| Models | `RinggAI/Transcript-Analytics-SLM1.5b` (Qwen2.5-1.5B fine-tune, last modified 2025-11-27) and `RinggAI/Transcript-Analytics-Consensus_0.5B` (2026-06-11, no README) |
| Hardware / libs | Linux x86_64, CPU only (shared box, so no latency claims), transformers 5.x, torch 2.x, bf16, greedy decoding, `max_new_tokens=300` |
| Data | `bench/cases.py`: 6 synthetic transcripts with a gold outcome: PROMISE_TO_PAY (Hinglish), ALREADY_PAID (Devanagari), REFUSED (English), CALLBACK_REQUESTED (noisy ASR), WRONG_NUMBER, NO_RESPONSE |
| Schema | the model card's own `response_schema` (key_points / action_items / summary / classification). The card never defines `classification_schema`, so two versions were tried: **nested** `{call_outcome enum, customer_sentiment enum}` and **flat** (a string enum of outcomes) |
| Prompt variants | `sys_schema`: schema in the system message and transcript in the user turn; `user_only`: transcript and schema both in the user turn |

```bash
git clone https://huggingface.co/RinggAI/Transcript-Analytics-SLM1.5b models/Transcript-Analytics-SLM1.5b
cd bench
MODELS_DIR=../models python run.py Transcript-Analytics-SLM1.5b sys_schema          # nested schema
MODELS_DIR=../models python run.py Transcript-Analytics-SLM1.5b sys_schema flat     # flat schema
MODELS_DIR=../models python run.py Transcript-Analytics-SLM1.5b user_only
python analyze.py     # prints per-case predictions and totals for the out_*.json files in this directory
```

## Results (JSON valid / outcome correct)

Two sets of runs are included. The numbers differ slightly between them (library versions changed in between, and the
runs are single greedy generations), so both are shown.

| model | variant | 26 Sep run | 2 Oct re-run |
|---|---|---|---|
| 0.5B Consensus | system, nested | 6/6 valid, 4/6 correct | 6/6 valid, 4/6 correct |
| 0.5B Consensus | system, flat | 6/6, 4/6 | 6/6, 5/6 |
| 1.5B SLM | system, nested | 6/6, 4/6 | 6/6, 5/6 |
| 1.5B SLM | system, flat | 6/6, 4/6 | 6/6, 4/6 |
| 1.5B SLM | user turn only, nested | 6/6, 2/6 | 6/6, **1/6** |

Outputs: `bench/rerun/out_*.json` (2 Oct) and `bench/original-26sep/out_*.json` (26 Sep); the noisy console logs were left out.
`bench/analyze.py` (run it inside a directory holding `out_*.json`) produces the table rows above and the per-case predictions.

## Rough edges

1. **The card gives no usage example.** The SLM1.5b README says "Provide the below schema for best output" and shows
   `"classification": classification_schema`, but never defines `classification_schema` or the prompt format. The 0.5B and
   4B Consensus repos have no README at all (the 1.5B one does).
2. **A nested classification is not honoured.** With `classification = {call_outcome, customer_sentiment}` the 1.5B returns
   `classification` as a single string (the sentiment is dropped), and the 0.5B returns only
   `{call_outcome, customer_sentiment}` at the top level, with no summary or key points.
3. **Prompt placement swings accuracy.** For the 1.5B, schema in the system message gave 4-5/6 correct outcomes; schema in the
   user turn gave 1-2/6, once returning `POSITIVE` (a sentiment value) as the outcome of the Hinglish promise-to-pay call.
4. **A clear refusal is labelled CALLBACK_REQUESTED** by the 1.5B in all three system-prompt runs of the 2 Oct re-run, although its own
   summary says the customer refused and asked not to be called.

A correction I made along the way: an earlier note that PROMISE_TO_PAY was labelled ALREADY_PAID in all four system-prompt runs
**does not reproduce** on the current library versions (the 1.5B got it right in 1 of its 2 system-prompt runs, the 0.5B in 0 of 2),
so I am not claiming it.

## The free Squirrel TTS endpoint (documented in the HF README, no key)

Tested read-only. These results are from **25-26 Sep 2026**, and the README's example request again returned 502 on 2 Oct:

- The README's verbatim example (`tts/squirrel_readme_example_request.json`) returns
  `HTTP 502 {"detail":"Failed to synthesize audio with Squirrel model"}` (`tts/squirrel_502_headers.txt`). So did a Hinglish
  sentence, an en-US voice, and 150-, 200- and 250-character texts; a retry about 15 minutes later still returned 502.
- Length validation does not match the docs. The README says the limit is 300 characters; the API returns
  `413 {"detail":"Text too large, limit is 500 characters"}` for 300-, 301- and 350-character texts, while 250 characters passes
  validation. So the real limit is somewhere between 251 and 299, and the message quotes a different number.
- Validation itself works: an unknown `voice_id` returns `404 "Voice not found"`.

## Known issues check

These are model-card and endpoint matters; there is no public issue tracker for them, so none of it was reported.

## Not included

Model weights, tokenizers and the Hugging Face cache (several GB) are deliberately left out; clone them from the Hub as shown above.

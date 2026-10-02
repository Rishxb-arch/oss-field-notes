# Chonkie

Notes from building a small RAG chunker comparison on [Chonkie](https://github.com/feyninc/chonkie)
(the repo redirects from `chonkie-inc/chonkie`), with deterministic repros and a small tested patch.

Chonkie is fast and pleasantly small: the default install is about 71 MB with no torch, and almost every chunker
returned exact offsets on a real documentation corpus.

## What I built

`rag_eval.py`: a local chunker bake-off. It chunks a folder of markdown docs (`corpus/*.md`; I used about 20k words of
public READMEs and docs, which are not redistributed here, so bring your own), embeds every chunk locally with
model2vec `minishlab/potion-base-8M`, and scores 14 hand-written factual questions by cosine top-k (hit@1 / hit@5).
It also checks the invariant `text[start_index:end_index] == chunk.text` for every chunk.

Results on that corpus (a small eval set, so directional only; [`evidence/rag_eval_results.json`](evidence/rag_eval_results.json)):

| chunker | chunks | avg chars | chunk time | hit@1 | hit@5 | offset mismatches |
|---|---|---|---|---|---|---|
| Token(gpt2, 512, overlap 64) | 163 | 1281 | 0.04 s | 4/14 | 12/14 | **9** |
| Sentence(512) | 158 | 1292 | 0.09 s | 5/14 | 13/14 | 0 |
| Recursive(512) | 146 | 1269 | 0.03 s | 7/14 | 11/14 | 0 |
| Recursive, markdown recipe(512) | 191 | 970 | 0.02 s | 5/14 | 13/14 | 0 |
| Semantic(potion-8M, 512, thr 0.7) | 797 | 232 | 1.03 s | 6/14 | 9/14 | 0 |
| Fast(2048 B) | 99 | 1872 | 0.00 s | 9/14 | 12/14 | 0 |

## Environment

| | |
|---|---|
| OS | Debian 13 x86_64 |
| Python | 3.12 (uv venv) |
| Packages | `pip install chonkie` -> chonkie **1.7.0**, chonkie-core 0.10.2, tokie **0.1.4** (plus `model2vec` for the semantic repro) |
| Source checked at | `main` @ `664454b` (26 Aug 2026); the patch is against this commit |

The repros below were re-run in clean venvs on 2 Oct 2026; outputs are in [`evidence/`](evidence/).

## Verified issues

### 1. `TokenChunker` emits empty chunks and shifts later offsets when a window boundary falls inside a multi-byte character

**Repro** (`repro_empty_chunk.py`):

```bash
pip install chonkie==1.7.0
python repro_empty_chunk.py
```
```
chonkie 1.7.0 | ids: [64, 6552, 224, 65] | decode(ids[:2]) = '' (expected 'a' or 'a\ufffd')
86 chunks, 10 empty (token_count still 7), joined chunk text = 1300 chars vs original 1480 chars
chunks where text[start:end] != chunk.text: 64
```

(`evidence/repro_empty_chunk.txt`.) The direct cause is in `tokie` (gpt2 backend): `decode()` returns `''` for the whole
window when it starts or ends inside a multi-byte character, e.g. `tk.decode(tk.encode("a│b")[:2])` is `''` rather than `'a'`.

**Seen on a real document:** `TokenChunker(tokenizer="gpt2", chunk_size=512, chunk_overlap=64)` on a project README that
contains a box-drawing CLI table: one chunk came back as `text=''` with `start_index == end_index` but `token_count 512`,
every later chunk's offsets were off by +736 characters, and roughly 600 characters of the CLI reference appeared in no
chunk. In the 6-chunker comparison above this shows up as the 9 offset mismatches for Token.

**Expected:** every chunk's `text` equals `text[start_index:end_index]`, and the chunks together cover the input.

**Known:** [#629](https://github.com/feyninc/chonkie/issues/629) (open), which already identifies the root cause; the
suggested fix there (offset-based reconstruction) is the right one. What this adds: it still happens on tokie 0.1.4 /
chonkie 1.7.0, and it affects ordinary English READMEs with box-drawing characters, not only CJK text. Related: tokie #12.

No patch is included for this one.

### 2. The README Pipeline example fails on the default install with a bare `ModuleNotFoundError`

**Repro** (`readme_pipeline.py`, the README "Pipeline Usage" block):

```bash
pip install chonkie==1.7.0
python readme_pipeline.py
```
```
ModuleNotFoundError: No module named 'huggingface_hub'
RuntimeError: Pipeline failed at step 2 (chunk): No module named 'huggingface_hub'
```

(`evidence/readme_pipeline_error.txt`.) `recipe="markdown"` downloads the recipe from the Hugging Face Hub, but
`huggingface_hub` is only in the `[hub]` extra, and the error doesn't say so. By contrast the embeddings step fails with the
helpful `Please install it via pip install chonkie[st]`.

**Fix:** `chonkie-small-fixes.patch` raises
`ImportError: Recipes are downloaded from the Hugging Face Hub, which needs the optional 'hub' extra. Install it with: pip install "chonkie[hub]"`.

### 3. Pipeline error step numbers are off by one

In the failure above, the failing component is the user's *first* `.chunk_with("recursive")`, but the message says
"step 2". `_reorder_steps()` inserts an implicit `TextChef` as step 1, so with several `chunk_with` / `refine_with`
calls it is hard to tell which one failed.

**Fix:** the patch names the user-facing call and keeps the number, so existing tests still pass:
`Pipeline failed at step 5 (refine: refine_with('embeddings'); step numbering includes the implicit TextChef): ...`

### 4. Minor: `SemanticChunker` + model2vec gives NaN similarities for lines of box-drawing characters

**Repro** (`repro_semantic_nan.py`, needs `pip install model2vec`):

```
chonkie/embeddings/model2vec.py:67: RuntimeWarning: invalid value encountered in divide
norm(embed(box)) = 0.0 | similarity(box, 'hello') = nan
chonkie 1.7.0 | RuntimeWarnings during chunk(): ['invalid value encountered in divide']
```

`Model2VecEmbeddings("minishlab/potion-base-8M").embed("┌─────────────────┐")` is an all-zero vector, so cosine
similarity is `0/0 = nan`. It happened on the real corpus during `SemanticChunker.chunk()`. In my small tests it did not
change chunk boundaries, but NaN flows into threshold comparisons. **Fix:** a zero-norm guard in `similarity()` (patch).

### 5. Minor: naming

The README basic example (`readme_basic.py`) prints `Tokens: 60` for a 60-character sentence, because the default
tokenizer is `character`; someone skimming may read "tokens" as model tokens.

## The patch

`chonkie-small-fixes.patch` (against `main` @ `664454b`; applies cleanly to that commit):

- `utils/hub.py`: missing `huggingface_hub` gives an actionable `ImportError` (issue 2)
- `pipeline/pipeline.py`: errors name the user-facing call (issue 3)
- `embeddings/model2vec.py`: zero-norm guard in `similarity()` returns 0.0 instead of NaN (issue 4)

Tests run: `tests/test_pipeline.py tests/test_async_pipeline.py tests/pipeline tests/embeddings/test_model2vec_embeddings.py tests/test_utils.py`
gave 151 passed, 2 failed; the same 2 fail on unpatched `main` in that environment because they need the optional
`tree_sitter_language_pack`.

## What worked well

- Tiny, fast default install (71 MB venv in about 0.6 s with uv), no torch.
- Chunkers are fast: the whole 20k-word corpus chunks in 0.02-0.09 s, except Semantic at about 1 s.
- Offsets were exact for Sentence, Recursive, the markdown recipe, Semantic and Fast on the real corpus (0 mismatches).
- The `[st]` missing-extra error message is a model of what errors should look like.

## Files

| File | What it is |
|---|---|
| `repro_empty_chunk.py` | deterministic repro for issue 1 |
| `readme_pipeline.py` | README pipeline block, for issues 2 and 3 |
| `repro_semantic_nan.py` | issue 4 |
| `readme_basic.py` | README basic example, issue 5 |
| `rag_eval.py` | the chunker comparison (needs your own `corpus/*.md`) |
| `chonkie-small-fixes.patch` | the patch described above |
| `evidence/` | trimmed outputs |

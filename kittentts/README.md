# KittenTTS

Notes from building a small tool on [KittenTTS](https://github.com/KittenML/KittenTTS) (tiny CPU-only text-to-speech
models), plus runnable repros and a small tested patch.

The core promise holds up well: CPU-only, no account, and the nano model renders speech far faster than real time.
What follows are rough edges I hit on the way.

## What I built

`speak.py`: an offline "read my notes aloud" command-line tool. It strips markdown, streams sentence by sentence with
`generate_stream`, writes a WAV, and reports load time, time to first audio and real-time factor (RTF).
`edge_cases.py` is an edge-input probe (empty text, punctuation only, Hindi, emoji, accents, bad voice, bad speed, ...).

```bash
python speak.py sample_notes.md out.wav --model KittenML/kitten-tts-nano-0.8 --voice Jasper
python edge_cases.py KittenML/kitten-tts-mini-0.8
```

## Environment

| | |
|---|---|
| OS / hardware | Debian 13 x86_64, 8 vCPU (shared VM, so wall-clock timings are rough), no GPU |
| Python | 3.12 (uv venv) |
| onnxruntime | 1.30.0 |
| Tested | release wheel `kittentts-0.8.1` (the README install command) and `main` @ `be57585` (18 Aug 2026) |
| Patch is against | `main` @ `be57585` |

## Verified issues

Logs from the edge-case probe on both versions are in [`evidence/edge_release.txt`](evidence/edge_release.txt) (0.8.1)
and [`evidence/edge_main.txt`](evidence/edge_main.txt) (main), run with `kitten-tts-mini-0.8` on 26 Sep 2026.

### 1. The README install pulls torch and ~5 GB of CUDA wheels

```bash
./repro_install_size.sh
```

`pip install https://github.com/KittenML/KittenTTS/releases/download/0.8.1/kittentts-0.8.1-py3-none-any.whl`
gives a **5.6 GB** venv (torch 2.14.0, triton, nvidia-* cu13) for a 25-80 MB ONNX model. The chain is wheel METADATA
`Requires-Dist: misaki[en]>=0.9.4` -> `spacy-curated-transformers` -> `torch`; `misaki` is only imported on line 1 of
`onnx_model.py` (`from misaki import en, espeak`) and not used.

**Expected:** a small CPU-only install. On `main` the dependency is gone and the same install is **172 MB with zero
torch/nvidia packages** (re-checked 2 Oct 2026, see [`evidence/install_size.txt`](evidence/install_size.txt)).

**Known:** issues #118, #105, #95 (open); fixed on `main` by PR #83. The remaining gap is that no release has been cut
since, so the README command still installs the heavy one. Suggested fix: cut 0.8.2.

### 2. `normalize_text` is documented, but missing from the 0.8.1 wheel

```python
from kittentts import normalize_text
```
```
ImportError: cannot import name 'normalize_text' from 'kittentts'
```

It exists only on `main` (added in PR #134). Same root cause as issue 1: the README follows `main`, the install command
points at the older wheel.

### 3. The 0.8.1 sentence splitter breaks decimals and abbreviations, and removes `?` / `!`

```python
from kittentts.onnx_model import chunk_text
chunk_text("Version 2.5 is out. Dr. Smith said so!")
chunk_text("Is it ready? Yes!")
```
```
0.8.1: ['Version 2,', '5 is out,', 'Dr,', 'Smith said so,']
       ['Is it ready,', 'Yes,']
main:  ['Version 2.5 is out.', 'Dr. Smith said so!']
       ['Is it ready?', 'Yes!']
```

Fixed on `main`; again only a release gap.

### 4. Empty or whitespace-only input crashes (release and `main`)

```python
KittenTTS("KittenML/kitten-tts-nano-0.8").generate("", voice="Jasper")
```
```
ValueError: need at least one array to concatenate
```

The cause is `np.concatenate` over zero chunks. A realistic trigger is streaming LLM output or markdown that strips down
to nothing. On 0.8.1, `"..."` fails the same way. **Expected:** an empty array (or a clear error). No existing issue found.

### 5. The voice error lists internal IDs rather than the names users pass

```python
model.generate("hello", voice="jasper")
```
```
ValueError: Voice 'jasper' not available. Choose from: ['expr-voice-2-m', 'expr-voice-2-f', 'expr-voice-3-m', ...]
```

The README tells users to pass `Jasper`, `Bella`, ... **Expected:** the error lists those names (and mentions case sensitivity).

### 6. `speed` is not validated

```python
model.generate("hello there.", voice="Jasper", speed=0)   # raw ONNX Expand error + two red ORT log lines
model.generate("hello there.", voice="Jasper", speed=-1)  # silently returns 0.19 s of audio
```
```
Fail: [ONNXRuntimeError] : 1 : FAIL : Non-zero status code returned while running Loop node. Name:'/Loop' ... Tensor shape.Size() must be >= 0
```

### 7. The README documents `generate_to_file(..., clean_text)`, but the public class does not accept it (release and `main`)

```python
model.generate_to_file("Hi 3 cats.", "k.wav", voice="Jasper", clean_text=False)
```
```
TypeError: KittenTTS.generate_to_file() got an unexpected keyword argument 'clean_text'
```

The README also says `generate(clean_text=...)` defaults to `False` while `generate_to_file` defaults to `True`.
That is accurate to the code, but the same text can be read differently by the two calls (`$12.50`).

### 8. Minor

- Every `generate()` prints `Generating audio for text: ...` to stdout, with no way to turn it off.
- `__version__` reports `0.1.0` in the 0.8.1 wheel.

## The patch

`kittentts-small-fixes.patch` (against `main` @ `be57585`; applies cleanly to that commit):

- empty input returns an empty float32 array instead of crashing (issue 4)
- the voice error lists the friendly names and says "case-sensitive" (issue 5)
- `speed <= 0` raises a clear `ValueError` (issue 6)
- `KittenTTS.generate_to_file` accepts and passes through `clean_text` (issue 7)
- removes the unconditional `print` in `generate` (issue 8)

Before/after on `main` ([`evidence/check_patch_before_after.txt`](evidence/check_patch_before_after.txt), produced by `check_patch.py`):

```
[err] empty input: ValueError: need at least one array to concatenate          ->  [ok ] empty input: (0,)
[err] speed=0: Fail: [ONNXRuntimeError] ...                                    ->  [err] speed=0: ValueError: speed must be > 0, got 0
[err] voice 'jasper': ... Choose from: ['expr-voice-2-m', ...]                 ->  ... Choose from: ['Bella', 'Jasper', ...] (names are case-sensitive)
[err] generate_to_file(clean_text=False): TypeError ...                        ->  [ok ] generate_to_file(clean_text=False): written
```

Apply with `git apply kittentts-small-fixes.patch` inside a clone of KittenTTS checked out at `be57585`.

## What worked well

- CPU-only, no account, no API key. On `main`, install takes seconds and is 172 MB.
- `speak.py` on a 319-character note (10 chunks, `main`, rough numbers on a shared 8-vCPU VM):

  | model | audio | wall | RTF | time to first audio |
  |---|---|---|---|---|
  | nano-0.8 | 46.0 s | 3.1 s | 0.07 | 0.89 s |
  | micro-0.8 | 43.2 s | 27.7 s | 0.64 | 4.43 s |
  | mini-0.8 | 34.6 s | 45.3 s | 1.31 | 8.17 s |

- `main`'s new `normalize_text` and chunker are clearly better (decimals, "Dr.", "?" and "!" all survive), and
  `generate_stream` made the streaming command-line tool trivial.

## Files

| File | What it is |
|---|---|
| `speak.py`, `sample_notes.md` | the "read my notes aloud" tool and a sample input |
| `edge_cases.py` | edge-input probe used for issues 3-7 |
| `repro_install_size.sh` | install footprint: release wheel vs `main` |
| `check_patch.py` | before/after checks for the patch |
| `kittentts-small-fixes.patch` | the patch described above |
| `evidence/` | trimmed logs |

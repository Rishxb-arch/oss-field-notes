# Moonshine (`moonshine-voice`)

Notes from running [Moonshine](https://github.com/moonshine-ai/moonshine) speech recognition on a CPU-only Linux VM,
with a runnable repro for one significant finding (non-deterministic transcripts on AMX-capable Xeons),
a small workaround, and a tested patch for two minor papercuts.

Moonshine is a lovely piece of engineering: small models, no account, a pleasant Python API. Everything below
is offered in that spirit.

## What I did

Transcribed the same 10 s clip (`beckett.wav`, copied from Moonshine's own `test-assets/`, MIT-licensed with the repo)
repeatedly with `Transcriber.transcribe_without_streaming`, across model sizes, with a shared or a fresh `Transcriber`,
and in fresh processes, then looked at whether the transcript is stable.

## Environment

| | |
|---|---|
| OS / CPU | Debian 13 x86_64, kernel 6.12, 8-vCPU Intel Xeon VM, no GPU. CPU flags include `avx512*`, **`amx_int8`, `amx_tile`, `amx_bf16`** |
| Python | 3.12 (uv venv) |
| Package | `pip install moonshine-voice==0.1.5` (bundles ONNX Runtime **1.23.2**) |
| Source read at | Moonshine `main` @ `234f60f` (24 Aug 2026), patch is against this commit |

## Verified issues

### 1. On an AMX-capable Xeon, transcripts are non-deterministic and often garbage (AMX int8 path in ONNX Runtime)

**Repro** (needs `gcc`, `pip install moonshine-voice==0.1.5 soundfile`, a CPU with `amx_int8`):

```bash
./amx_repro.sh
```

That compiles `noamx.c`, then runs `stability_tiny.py` (6 calls on one `Transcriber`, TINY model) twice: once as-is,
once with the shim preloaded (see "Build the shim" below). Output from a re-run on 2 Oct 2026
(full file: [`evidence/amx_repro_output.txt`](evidence/amx_repro_output.txt)):

```
== baseline
TINY distinct=6/6
    'До встре‒ Selector. No matter. TryBASE again. ˚, fam againfte, Fale!!! Boutoret SQLiteometryometry'
    'Everões, Ever failed. No matter. Try again. F samen again. Fell better.'
    "Ever tried xcode. Ever failed. No matter. Try again. 'fail again! Fell better."
    ...
== AMX denied
[noamx] denied ARCH_REQ_XCOMP_PERM
TINY distinct=1/6
    'Ever tried. Ever failed. No matter. Try again. Fare again. Fell better.'
    (identical x6)
```

**What I saw**

- TINY, 6 calls: 6/6 distinct transcripts at baseline, 1/6 with AMX denied (correct text).
  ([`evidence/tiny_baseline_amx.txt`](evidence/tiny_baseline_amx.txt), [`evidence/tiny_amx_denied.txt`](evidence/tiny_amx_denied.txt))
- TINY, BASE, SMALL_STREAMING and MEDIUM_STREAMING (the `get_model_for_language("en")` default), 4 calls each:
  4/4 distinct at baseline for every model, including MEDIUM_STREAMING outputs such as
  `'Ever tried? Ever, failed. No matter It K  It It It It It Y S Y Y Y Y Y - Y Algorithms,,in all'`
  ([`evidence/matrix_baseline.txt`](evidence/matrix_baseline.txt)).
  With AMX denied, BASE and MEDIUM_STREAMING (with and without `use_speculative_decoding`) each gave 1/4 distinct,
  with correct text ([`evidence/matrix_amx_denied.txt`](evidence/matrix_amx_denied.txt)).
- `use_speculative_decoding=false` does not help at baseline.
- It also happens with a fresh `Transcriber` per call (`stability_fresh.py`), in fresh processes, and pinned to one
  core (`taskset -c 0`), so it is not state carried between calls.

**Expected:** the same audio gives the same transcript on every call.

**Likely cause:** ONNX Runtime's AMX int8 kernels (or this VM's AMX state handling), not Moonshine's own code.
Denying AMX tile permission is enough to make every model deterministic and correct, and the same shim also
fixed output-length drift in an unrelated ONNX model (KittenTTS) on the same machine with stock onnxruntime 1.30.0.
Moonshine 0.1.5 ships ORT 1.23.2.

**Known upstream:** [microsoft/onnxruntime#26324](https://github.com/microsoft/onnxruntime/issues/26324)
("Wrong output of model shufflenet-v2-12-int8.onnx on Xeon 4 Gen (AVX-512VNNI, AMX-INT8)", ORT 1.23.1),
closed by the stale bot on 14 Jan 2026 without a fix. I could not find a Moonshine issue for it.

**Why it may matter:** Sapphire / Emerald / Granite Rapids are the default x86 instance families on AWS
(m7i/c7i/r7i), GCP (C3/C4) and Azure (Dv6), so server-side use could hit this without any error being raised.

**Workaround** (`noamx.c`): an `LD_PRELOAD` shim that makes `arch_prctl(ARCH_REQ_XCOMP_PERM, ...)` return `EPERM`, so
ONNX Runtime's MLAS cannot enable AMX and falls back to its AVX-512 kernels.

**Build the shim** (the compiled `.so` is intentionally not included):

```bash
gcc -shared -fPIC -O2 -o noamx.so noamx.c -ldl
LD_PRELOAD="$PWD/noamx.so" python stability_tiny.py
```

**Possible mitigations for the library:** bump/pin ORT and retest, detect `amx_int8` and skip the AMX request
(what the shim does), or run a one-off self-check at start-up that transcribes a bundled clip twice.

### 2. `moonshine-voice mic` dies with a raw `OSError` when PortAudio is missing

```bash
pip install moonshine-voice==0.1.5
moonshine-voice mic        # or: python -c "from moonshine_voice import MicTranscriber"
```

```
OSError: PortAudio library not found
```
(from `sounddevice.py`; [`evidence/mic_without_portaudio.txt`](evidence/mic_without_portaudio.txt))

**Expected:** a message that says what to install (`libportaudio2` on Debian/Ubuntu, `portaudio` on macOS).
File transcription via `Transcriber` is unaffected, since the import is lazy.

**Fix:** `moonshine-small-fixes.patch` turns it into
`ImportError: Microphone capture needs the PortAudio library, which was not found (...). Install it (Debian/Ubuntu: sudo apt install libportaudio2, macOS: brew install portaudio) or use Transcriber / moonshine-voice transcribe <file.wav> for file input.`

### 3. `moonshine-voice transcribe --help` describes itself as "Model info example"

```bash
moonshine-voice transcribe --help
```

shows `Model info example` as the description (copy-paste in `transcriber.py`).
**Fix:** `moonshine-small-fixes.patch` changes it to `Transcribe WAV files with Moonshine`.

## The patch

`moonshine-small-fixes.patch` (against `234f60f`) covers issues 2 and 3 only. Apply with:

```bash
cd moonshine && git checkout 234f60f && git apply /path/to/moonshine-small-fixes.patch
```

It does **not** change anything about issue 1; that one belongs in ONNX Runtime or in a start-up guard.

## What worked well

- `pip install` plus model download with no account or keys. Small models (tiny 42 MB, base 134 MB).
- The `get_model_for_language()` API is easy to use, and imports are lazy so file-only use needs no audio libraries.
- Once AMX is out of the way, accuracy on real speech is excellent: MEDIUM_STREAMING reproduces the clip exactly,
  including the "?" punctuation, on every run.
- The `lora` / `finetune` CLI and `set_keyterms` / `set_context` biasing speak directly to the domain-jargon problem.

## Files

| File | What it is |
|---|---|
| `amx_repro.sh` | one-command baseline vs AMX-denied comparison |
| `noamx.c` | the 15-line `LD_PRELOAD` workaround (build it yourself, see above) |
| `stability_tiny.py` | 6 calls on one `Transcriber`, TINY model |
| `stability_fresh.py` | a fresh `Transcriber` per call |
| `stability_matrix.py` | model size x speculative decoding matrix |
| `moonshine-small-fixes.patch` | PortAudio hint and `--help` text |
| `beckett.wav` | 10 s test clip, copied from Moonshine's `test-assets/` (MIT) |
| `evidence/` | trimmed outputs of the runs described above |

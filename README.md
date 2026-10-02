# oss-field-notes

Notes, reproduction scripts and small patches from building things with open-source AI tools.

When I try a new open-source project, I build something small with it, write down what worked, and, when something
doesn't, keep a repro that anyone can run plus (where it's small enough) a tested patch. This repository is where those
notes live, one folder per project. They are offered in good faith to the maintainers and to anyone who hits the same wall.

Each folder has a `README.md` with the environment and exact versions or commit SHAs, each issue with the commands to
reproduce it, the verbatim output, what I expected, whether it's already a known issue, and a fix or workaround. Every
folder also says what worked well, because most of it did.

| Folder | Project | What's in it |
|---|---|---|
| [`kittentts/`](kittentts/) | [KittenTTS](https://github.com/KittenML/KittenTTS) | Tiny CPU-only TTS: install size of the release wheel, empty-input and `speed` handling, voice-name errors, and a small patch |
| [`runanywhere/`](runanywhere/) | [RunAnywhere SDKs](https://github.com/RunanywhereAI/runanywhere-sdks) | Building the Python SDK from source on Linux: install hints, shared-library packaging, STT/TTS/VAD behaviour, and a patch for the build hints |
| [`chonkie/`](chonkie/) | [Chonkie](https://github.com/feyninc/chonkie) | A chunker comparison for RAG, an offset bug in `TokenChunker` on multi-byte text, clearer pipeline errors, and a patch |
| [`moonshine/`](moonshine/) | [Moonshine](https://github.com/moonshine-ai/moonshine) | Non-deterministic transcripts on AMX-capable Xeons, with a repro and a 15-line workaround, plus a small patch |
| [`lalamo/`](lalamo/) | [lalamo (Mirai)](https://github.com/trymirai/lalamo) | Running `lalamo server` batches on a CPU-only machine, stop-token and truncation behaviour, and a `--batch-size` patch |
| [`bolna/`](bolna/) | [Bolna](https://github.com/bolna-ai/bolna) | A text-mode test harness for a voice agent with a local LLM and no keys, the crashes on the way, and a patch |
| [`dograh/`](dograh/) | [Dograh](https://github.com/dograh-hq/dograh) | Self-hosting with a local LLM, the Python SDK and the Test Chat API, with the rough edges I hit |
| [`byteask/`](byteask/) | [ByteAsk](https://github.com/ByteAsk/ByteAsk-Embedded-MCP) | The public embedded-docs MCP endpoint and the OSS server: bare identifiers like `FC06` miss, some invented register names get confident cited hits, garbled section labels, and a patch for the never-called query logger, the pip-install project root and the bearer check |
| [`ringg/`](ringg/) | [RinggAI models](https://huggingface.co/RinggAI) | Two transcript-analytics SLMs on six synthetic Hinglish collection calls: always valid JSON, but a nested classification is flattened, prompt placement swings accuracy, a refusal is labelled as a callback, and the free TTS example returns 502 |
| [`gitnexus/`](gitnexus/) | [GitNexus](https://github.com/abhigyanpatwari/GitNexus) | Indexing a Python/JAX repo (the call graph was right), `detect-changes` on a stale index blaming a symbol the diff never touched, and a default `analyze` that repeats the same warnings hundreds of times |
| [`supermemory/`](supermemory/) | [Supermemory](https://github.com/supermemoryai/supermemory) | Self-hosting `supermemory-server` 0.0.8: the installer dies with no TTY, a document stuck in `indexing` when the LLM is slow, and a quickstart search call that returns nothing (already reported), with two small patches |
| [`futureagi/`](futureagi/) | [agent-learning-kit](https://github.com/future-agi/agent-learning-kit) | A key-free RAG-eval harness on a local model: `--dry-run` accepts a bad assertion type, missing inputs score 0.0 as "completed", a stale install hint, and two patches |
| [`bifrost/`](bifrost/) | [Bifrost](https://github.com/maximhq/bifrost) | A Go LLM gateway in front of Ollama: `max_tokens` below 16 is silently raised to 16 for Ollama/vLLM/SGLang, with a Go test and a 17-line patch |

## A note on tone

These are lovely projects, built by small teams moving fast. If something here is wrong, outdated, or already fixed, I'd
genuinely like to know. Versions and dates are recorded in each README, so you can tell quickly whether a note still applies.

## Layout and running things

- Scripts use relative paths and are meant to be run from inside their own folder.
- `evidence/` folders hold trimmed outputs of the runs described in each README.
- `*.patch` files are plain `git diff` output against the commit named in that folder's README
  (`git apply <file>.patch` in a checkout of that commit).
- Model weights, virtual environments, databases and the upstream source trees are deliberately not included.
- Dates matter. Most folders were re-run on 2 Oct 2026, but not all: the Dograh folder was **not** re-run on 2 Oct (its notes are from
  26 Sep 2026), and the RunAnywhere speech results (STT, TTS, VAD) are from 26 Sep 2026 runs. Each README says what was re-checked and when.

## License

My own scripts and notes are MIT-licensed (see [`LICENSE`](LICENSE)). The `.patch` files are modifications of the upstream projects
and follow each project's own license. The test clip `beckett.wav` (in `moonshine/` and `runanywhere/`) is copied from the Moonshine
repository's `test-assets/` and is covered by that repository's MIT license.

Rishxb-arch

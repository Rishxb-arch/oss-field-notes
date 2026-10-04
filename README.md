# OSS Field Notes

**Hands-on investigations of open-source AI tools — with scripts, logs, and fixes you can follow.**

Hi, I'm [Rishab](https://github.com/Rishxb-arch). This is the starting point for my public testing notes. Each linked repository records a specific investigation; check its README for the tested version, setup, results, and limitations.

## Start here

| Investigation | What to explore |
| --- | --- |
| [mcp-use](https://github.com/Rishxb-arch/mcp-use-repro) | MCP client pagination, schema handling, and session recovery |
| [Graphify](https://github.com/Rishxb-arch/graphify-repro) | Method-call resolution across classes |
| [Magnitude](https://github.com/Rishxb-arch/magnitude-repro) | CPU inference measurements and streaming behavior |
| [Lalamo](https://github.com/Rishxb-arch/lalamo-repro) | Model-serving testing and reproduction notes |
| [Dograh](https://github.com/Rishxb-arch/dograh-repro) | Voice-agent platform testing and reproduction notes |

## Merged upstream contributions

- [Dograh #851](https://github.com/dograh-hq/dograh/pull/851): clear 503 errors when the hosted service is unreachable for template workflows.
- [Lalamo #375](https://github.com/trymirai/lalamo/pull/375): a `--batch-size` option for CPU serving.
- [Dograh #850](https://github.com/dograh-hq/dograh/pull/850): quickstart documentation for public tunnels and open signup.

## Browse the notebook

**Voice and speech**  
[KittenTTS](https://github.com/Rishxb-arch/kittentts-repro) · [Moonshine](https://github.com/Rishxb-arch/moonshine-repro) · [Bolna](https://github.com/Rishxb-arch/bolna-repro) · [Dograh](https://github.com/Rishxb-arch/dograh-repro) · [Ringg](https://github.com/Rishxb-arch/ringg-repro)

**Inference and runtime**  
[RunAnywhere](https://github.com/Rishxb-arch/runanywhere-repro) · [Lalamo](https://github.com/Rishxb-arch/lalamo-repro) · [Magnitude](https://github.com/Rishxb-arch/magnitude-repro) · [Herdr](https://github.com/Rishxb-arch/herdr-repro)

**Agents, knowledge, and evaluation**  
[MCP-use](https://github.com/Rishxb-arch/mcp-use-repro) · [Chonkie](https://github.com/Rishxb-arch/chonkie-repro) · [GitNexus](https://github.com/Rishxb-arch/gitnexus-repro) · [Graphify](https://github.com/Rishxb-arch/graphify-repro) · [Supermemory](https://github.com/Rishxb-arch/supermemory-repro) · [FutureAGI](https://github.com/Rishxb-arch/futureagi-repro) · [Bifrost](https://github.com/Rishxb-arch/bifrost-repro) · [ByteAsk](https://github.com/Rishxb-arch/byteask-repro)

## Found something worth discussing?

Open an issue in the relevant reproduction repository with your version, environment, and what you observed. Corrections and smaller reproductions are welcome.

These notes are snapshots of specific versions and environments. A reported behavior may already be fixed upstream; see each investigation for its scope and patch status.

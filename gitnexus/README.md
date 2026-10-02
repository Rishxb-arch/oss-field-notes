# GitNexus (Akon Labs)

Notes from trying [GitNexus](https://github.com/abhigyanpatwari/GitNexus) 1.6.12 (the open-source code knowledge graph that
Akon Labs builds on) on a Python/JAX codebase, [trymirai/lalamo](https://github.com/trymirai/lalamo).

The graph held up: indexing was fast and every spot check matched what I had verified by hand. This folder documents two
rough edges I hit.

## Environment

| | |
|---|---|
| GitNexus | `gitnexus@1.6.12` from npm (latest on 2 Oct 2026); source looked at: `abhigyanpatwari/GitNexus` HEAD `ce79caa` (1 Oct 2026) |
| Node / npm | Node 22.x, npm 10.9.x; install took 40 s (254 packages), no C++ toolchain issues on linux-x64 |
| Target | `trymirai/lalamo` @ `2c182c5`, 277 `.py` files |
| Accounts / keys | none |

## What I ran and what held up

1. `gitnexus analyze --skip-skills --skip-agents-md` on lalamo: 6,268 nodes, 16,120 edges, 258 clusters, 544 flows in about 28-55 s
   (40.1 s as reported by the tool on a loaded box in one run; the script run on 2 Oct was about 28 s). `.gitnexus/` ships its own
   `.gitignore`, so the working tree was not dirtied.
2. Accuracy spot checks against my own reading of the code, all correct:
   - `impact trim_at_eos --direction upstream`: depth 1 `reply_many` and `LanguageModel.reply`; depth 2 `server.generate_replies`;
     depth 3 `run_generate_replies_with_stats`. Tests are excluded by default (`--include-tests`).
   - `context _get_device_memory_stats`: 3 callers, all correct.
   - `trace generate_replies _get_device_memory_stats` returned the exact 4-hop path
     `generate_replies -> reply_many -> _memory_budget_for_auto_batching -> _get_device_memory_stats`, including a nested closure.
3. An incremental re-index after a change took 22 s (16.7 s in one saved log), against 55 s cold.

## Rough edges

Both reproduce with one script, run end to end on 2 Oct 2026:

```bash
./repro_gitnexus_1.6.12.sh          # needs node >= 22, git, python3; clones lalamo into a temp dir, no keys
```

### 1. `detect-changes` on a stale index blames a symbol the diff never touched

Apply a 24-line change to `lalamo/main.py` and `lalamo/server.py` ([`lalamo-input-24line.diff`](lalamo-input-24line.diff), a
`--batch-size` option for `lalamo server`) **without** re-running `analyze`, then run `gitnexus detect-changes`:

- It reports `Changes: 2 files, 4 symbols`, including `Function _profile_memory -> lalamo/main.py`, which the diff does not touch.
- Cause (my reading, not confirmed by a maintainer): the hunks are matched with new-side line numbers against the stale index's
  old symbol ranges. The `+670` hunk line falls inside the old `_profile_memory` range (665+), whereas in old-side coordinates
  every hunk is inside `server()` (612-662).
- `gitnexus status` in the same state prints "Index content: 2 changed ... Status: stale", but `detect-changes` prints no
  staleness warning.
- After re-running `analyze` (incremental), the answer is correct: `server`, `generate_replies`, `start_server`, plus the new
  annotated local `vram_bytes` shown as a property.

Known? I searched the issue tracker for `detect_changes stale index` and related terms. Related but different: #3131, #2690 (other
`detect_changes` bugs) and #415 (new symbols treated as Modified, open). Nothing on the stale-index line mapping or a missing warning.

### 2. A default `analyze` floods the terminal with duplicate warnings

The default interactive run prints 368 raw JSON (pino) warning lines, `callable-value-flow: candidate set exceeded the cap; no partial
CALLS emitted` (candidateCount 33 vs cap 32), for only 31 distinct call sites. The most repeated site appears 158 times, which
looks like the same warning being re-emitted on every fixpoint iteration. `GITNEXUS_LOG_LEVEL` exists, but it is not the default.
See [`evidence/analyze_warn_summary.txt`](evidence/analyze_warn_summary.txt), computed from a saved log. I found no
issue about de-duplicating them.

### Minor, not reported

- `gitnexus status` prints two large "analyzer runner identity" JSON blobs before the useful line.
- `trace` start lines are 0-based while `context` and `impact` are 1-based. That is a documented parity follow-up
  (#2377 / #2380), so it is not new.

## Files

| Path | What |
|---|---|
| `repro_gitnexus_1.6.12.sh` | end-to-end repro of both rough edges |
| `lalamo-input-24line.diff` | the 24-line lalamo change used for edge 1 (against lalamo `2c182c5`) |
| `evidence/analyze_warn_summary.txt` | warning counts per call site and the non-warning output of a default `analyze` |

The full 100 KB logs, the `.gitnexus` index (95 MB) and the GitNexus and lalamo source trees are not included.

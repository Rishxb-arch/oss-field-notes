#!/usr/bin/env bash
# Reproduce the CPU `lalamo server` problems. Run from the root of a lalamo clone (commit 2c182c5), with this
# folder's files copied or referenced by path. Needs: uv, ~4 GB RAM, a CPU-only machine.
#
#   git clone https://github.com/trymirai/lalamo && cd lalamo && git checkout 2c182c5
#   uv sync --no-dev --extra cpu --extra server        # avoids the 2.8 GB dev group
#   uv run --no-sync lalamo convert Qwen/Qwen3-0.6B              # writes models/Qwen3-0.6B
#   /path/to/this/folder/repro_server.sh unpatched     # issues 1-3, stock server
#   git apply /path/to/this/folder/lalamo-server-batch-size.patch
#   /path/to/this/folder/repro_server.sh patched       # same requests with --batch-size 2
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
MODE="${1:-unpatched}"

if [ "$MODE" = "patched" ]; then
  uv run --no-sync lalamo server --batch-size 2 --port 8293 > server.log 2>&1 &
else
  uv run --no-sync lalamo server --vram-gb 3 --port 8293 > server.log 2>&1 &     # plain `lalamo server` stops with "use --vram-gb"
fi
SERVER=$!
trap 'kill $SERVER 2>/dev/null' EXIT
until curl -s -o /dev/null http://127.0.0.1:8293/batches/none; do sleep 2; done

echo "== default reasoning, max_completion_tokens=32"
python "$HERE/run_batch.py" "$HERE/batch_req.json"
echo "== reasoning_effort=no_reasoning"
python "$HERE/run_batch.py" "$HERE/batch_req_nr.json"

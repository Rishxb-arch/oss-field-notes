#!/usr/bin/env bash
# GitNexus 1.6.12 repros on a Python/JAX codebase (trymirai/lalamo @ 2c182c5, 277 .py files).
#  (1) default `analyze` floods the terminal with callable-value-flow warnings (many exact duplicates)
#  (2) `detect-changes` on a STALE index blames a symbol the diff never touched (_profile_memory)
# Needs: node >= 22, git, python3. No account/keys.
set -eu
HERE=$(cd "$(dirname "$0")" && pwd)
W=${W:-$(mktemp -d)}; mkdir -p "$W"; cd "$W"
npm install --prefix ./gn gitnexus@1.6.12 --no-audit --no-fund >/dev/null 2>&1
GN="$W/gn/node_modules/.bin/gitnexus"
git clone -q https://github.com/trymirai/lalamo.git && cd lalamo && git checkout -q 2c182c5
$GN analyze --skip-skills --skip-agents-md > "$W/analyze.log" 2>&1 || true
echo "== (1) warn lines: $(grep -c 'callable-value-flow' "$W/analyze.log")"
python3 - "$W/analyze.log" <<'PY'
import sys,json,collections
c=collections.Counter()
for l in open(sys.argv[1]):
    if l.startswith('{') and 'callable-value-flow' in l:
        c[json.loads(l).get('context')]+=1
print("   distinct sites:",len(c),"| most repeated:",c.most_common(1))
PY
git apply "$HERE/lalamo-input-24line.diff"   # 24-line patch to lalamo/main.py + server.py (new-side hunk at +670)
echo "== (2) status:"; $GN status 2>&1 | grep -E "Index content|Status"
echo "== (2) detect-changes WITHOUT re-running analyze (expect server, generate_replies, start_server only):"
($GN detect-changes 2>&1 || true) | grep -E "^Changes|Function|Method|Property"

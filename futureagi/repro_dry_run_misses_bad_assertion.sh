#!/usr/bin/env bash
# agent-learning-kit 0.1.0: --dry-run passes a suite whose assertion type is invalid;
# the real run then makes every provider call before failing with no partial results.
set -u
cat > /tmp/bad_suite.json <<'J'
{"version":"agent-learning.eval.v1","name":"bad","providers":[{"id":"echo","type":"echo"}],
 "prompts":[{"id":"p","template":"{{q}}"}],
 "tests":[{"id":"t1","vars":{"q":"{\"status\":\"ok\"}"},"assert":[{"type":"json-path","path":"$.status","value":"ok"}]}]}
J
agent-learn eval /tmp/bad_suite.json --dry-run --quiet; echo "dry-run exit=$?"
agent-learn eval /tmp/bad_suite.json --quiet; echo "real-run exit=$?"

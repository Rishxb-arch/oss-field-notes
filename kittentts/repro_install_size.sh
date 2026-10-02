#!/usr/bin/env bash
# Compare the install footprint of the README's release wheel (0.8.1) with `main` (be57585).
# Needs: uv (https://docs.astral.sh/uv/). Creates .venv-release/ and .venv-main/ next to this script.
# Note: the release venv downloads torch + CUDA wheels (about 5.6 GB on disk).
set -e
cd "$(dirname "$0")"

uv venv -p 3.12 .venv-release
uv pip install --python .venv-release/bin/python \
  https://github.com/KittenML/KittenTTS/releases/download/0.8.1/kittentts-0.8.1-py3-none-any.whl
echo "release 0.8.1 venv:"; du -sh .venv-release
echo -n "torch/nvidia packages: "; ls .venv-release/lib/python3.12/site-packages | grep -c -i -E '^(torch|nvidia|triton)' || true

uv venv -p 3.12 .venv-main
uv pip install --python .venv-main/bin/python "git+https://github.com/KittenML/KittenTTS@be57585"
echo "main be57585 venv:"; du -sh .venv-main
echo -n "torch/nvidia packages: "; ls .venv-main/lib/python3.12/site-packages | grep -c -i -E '^(torch|nvidia|triton)' || true

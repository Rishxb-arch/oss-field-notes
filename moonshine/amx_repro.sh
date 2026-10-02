#!/usr/bin/env bash
# Moonshine nondeterminism on AMX-capable x86 (Sapphire Rapids-class) CPUs.
# Same WAV (beckett.wav, copied from the Moonshine repo's test-assets), same Transcriber, 6 non-streaming calls:
#   baseline    -> several distinct transcripts, some garbage
#   AMX denied  -> 1 distinct transcript (correct)
# Needs: pip install moonshine-voice==0.1.5 soundfile ; gcc ; CPU flags amx_int8/amx_tile.
set -e
cd "$(dirname "$0")"
echo -n "CPU AMX flags: "; grep -o 'amx_[a-z0-9]*' /proc/cpuinfo | sort -u | tr '\n' ' '; echo
gcc -shared -fPIC -O2 -o noamx.so noamx.c -ldl
echo "== baseline";   python stability_tiny.py
echo "== AMX denied"; LD_PRELOAD="$PWD/noamx.so" python stability_tiny.py

"""Transcribe the same clip 6 times with one Transcriber (TINY model) and count distinct outputs.

usage: python stability_tiny.py [clip.wav]      (default: beckett.wav next to this file)
"""
import os
import sys

import soundfile as sf
from moonshine_voice import ModelArch, Transcriber, get_model_for_language

here = os.path.dirname(os.path.abspath(__file__))
wav = sys.argv[1] if len(sys.argv) > 1 else os.path.join(here, "beckett.wav")
audio, sr = sf.read(wav, dtype="float32")
audio = audio.tolist()
path, arch = get_model_for_language("en", ModelArch.TINY)
t = Transcriber(model_path=path, model_arch=arch)
outs = [" ".join(l.text for l in t.transcribe_without_streaming(audio, sr).lines) for _ in range(6)]
print(f"TINY distinct={len(set(outs))}/6")
for o in outs:
    print("   ", repr(o))

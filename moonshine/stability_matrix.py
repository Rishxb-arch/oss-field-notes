"""Same clip x model architecture (x speculative decoding on/off): number of distinct transcripts over 4 runs.

usage: [ARCHS=TINY,BASE,SMALL_STREAMING,MEDIUM_STREAMING] python stability_matrix.py [clip.wav]
"""
import os
import sys

import soundfile as sf
from moonshine_voice import ModelArch, Transcriber, get_model_for_language

here = os.path.dirname(os.path.abspath(__file__))
wav = sys.argv[1] if len(sys.argv) > 1 else os.path.join(here, "beckett.wav")
audio, sr = sf.read(wav, dtype="float32")
audio = audio.tolist()
archs = [ModelArch[x] for x in os.environ.get("ARCHS", "TINY,BASE,SMALL_STREAMING,MEDIUM_STREAMING").split(",")]
for arch in archs:
    path, arch = get_model_for_language("en", arch)
    for opts in [None, {"use_speculative_decoding": "false"}]:
        if opts and arch in (ModelArch.TINY, ModelArch.BASE):
            continue
        t = Transcriber(model_path=path, model_arch=arch, options=opts)
        outs = [" ".join(l.text for l in t.transcribe_without_streaming(audio, sr).lines) for _ in range(4)]
        print(f"{arch.name:17s} opts={opts} distinct={len(set(outs))}/4", flush=True)
        for o in outs:
            print("    ", repr(o), flush=True)

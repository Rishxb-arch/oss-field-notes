"""Same as stability_tiny.py, but a brand-new Transcriber for every run
(rules out state carried between calls).

usage: python stability_fresh.py [clip.wav] [runs]
"""
import os
import sys

import soundfile as sf
from moonshine_voice import Transcriber, get_model_for_language

here = os.path.dirname(os.path.abspath(__file__))
wav = sys.argv[1] if len(sys.argv) > 1 else os.path.join(here, "beckett.wav")
runs = int(sys.argv[2]) if len(sys.argv) > 2 else 5
audio, sr = sf.read(wav, dtype="float32")
audio = audio.tolist()
path, arch = get_model_for_language("en")
for r in range(runs):
    t = Transcriber(model_path=path, model_arch=arch)
    print(f"fresh-transcriber run{r}:", repr(" ".join(l.text for l in t.transcribe_without_streaming(audio, sr).lines)), flush=True)
    if hasattr(t, "close"):
        t.close()
    del t

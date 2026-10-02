"""speak.py - offline 'read my notes aloud' CLI on KittenTTS.
Strips markdown, streams sentence-by-sentence, reports time-to-first-audio and RTF.
usage: python speak.py sample_notes.md out.wav [--model KittenML/kitten-tts-micro-0.8] [--voice Luna] [--threads N]
"""
import argparse, re, time, io, contextlib
import numpy as np, soundfile as sf, onnxruntime as ort
from kittentts import KittenTTS

def strip_md(md: str) -> str:
    md = re.sub(r"```.*?```", " ", md, flags=re.S)          # drop code blocks
    md = re.sub(r"`([^`]*)`", r"\1", md)
    md = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", md)             # images
    md = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", md)          # links -> text
    md = re.sub(r"^\s{0,3}#{1,6}\s*(.*)$", r"\1.", md, flags=re.M)  # headings end a sentence
    md = re.sub(r"^\s*[-*+]\s+", "", md, flags=re.M)
    md = re.sub(r"[*_]{1,3}([^*_]+)[*_]{1,3}", r"\1", md)
    return re.sub(r"\s+", " ", md).strip()

ap = argparse.ArgumentParser()
ap.add_argument("inp"); ap.add_argument("out")
ap.add_argument("--model", default="KittenML/kitten-tts-micro-0.8")
ap.add_argument("--voice", default="Luna"); ap.add_argument("--threads", type=int, default=0)
a = ap.parse_args()

t0 = time.time()
tts = KittenTTS(a.model)
if a.threads:   # optional: limit ONNX Runtime intra-op threads
    so = ort.SessionOptions(); so.intra_op_num_threads = a.threads
    tts.model.session = ort.InferenceSession(tts.model.model_path, so)
load = time.time() - t0
text = strip_md(open(a.inp).read())
if not text:
    raise SystemExit("nothing to read")
chunks, t1, ttfa = [], time.time(), None
with contextlib.redirect_stdout(io.StringIO()):
    for c in tts.generate_stream(text, voice=a.voice, clean_text=True):
        if ttfa is None: ttfa = time.time() - t1
        chunks.append(np.asarray(c).squeeze())
wall = time.time() - t1
audio = np.concatenate(chunks)
sf.write(a.out, audio, 24000)
print(f"model={a.model} voice={a.voice} threads={a.threads or 'default'} load={load:.1f}s "
      f"chars={len(text)} chunks={len(chunks)} audio={len(audio)/24000:.1f}s wall={wall:.1f}s "
      f"RTF={wall/(len(audio)/24000):.2f} time_to_first_audio={ttfa:.2f}s")

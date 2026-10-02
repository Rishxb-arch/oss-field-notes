"""Edge-case probe for KittenTTS. Run with the release wheel and with main."""
import sys, time, traceback, io, contextlib
import numpy as np
import kittentts
from kittentts import KittenTTS
SR = 24000
m = KittenTTS(sys.argv[1] if len(sys.argv) > 1 else "KittenML/kitten-tts-mini-0.8")
inner = m.model

def run(label, fn):
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            t = time.time(); a = fn(); el = time.time() - t
        a = np.asarray(a).squeeze()
        print(f"[OK ] {label}: {len(a)/SR:.2f}s audio, {el:.2f}s wall")
        return a
    except Exception as e:
        print(f"[ERR] {label}: {type(e).__name__}: {e}")

# chunking of release/main
try:
    from kittentts.onnx_model import chunk_text
except ImportError:
    from kittentts.preprocess import chunk_text
for s in ["Version 2.5 is out. Dr. Smith said so!", "Is it ready? Yes!", "Pi is 3.14159."]:
    print("chunk_text", repr(s), "->", chunk_text(s))

run("empty string", lambda: m.generate("", voice="Jasper"))
run("whitespace only", lambda: m.generate("   ", voice="Jasper"))
run("only punctuation", lambda: m.generate("...", voice="Jasper"))
a1 = run("short 'OK.'", lambda: m.generate("OK.", voice="Jasper"))
a2 = run("short 'Yes.'", lambda: m.generate("Yes.", voice="Jasper"))
run("hindi devanagari", lambda: m.generate("नमस्ते, आप कैसे हैं?", voice="Jasper"))
run("accents", lambda: m.generate("The naïve café served crème brûlée.", voice="Jasper"))
run("emoji", lambda: m.generate("Great job 🎉🎉", voice="Jasper"))
run("bad voice", lambda: m.generate("hello", voice="jasper"))
run("speed 0", lambda: m.generate("hello there.", voice="Jasper", speed=0))
run("speed -1", lambda: m.generate("hello there.", voice="Jasper", speed=-1))
run("generate_to_file clean_text=False (README documents it)",
    lambda: m.generate_to_file("Hi 3 cats.", "k.wav", voice="Jasper", clean_text=False) or np.zeros(1))
long = " ".join(["word"] * 600)  # 600 words, no punctuation
run("600 words no punctuation", lambda: m.generate(long, voice="Jasper"))
# numbers with default clean_text=False vs True
for ct in (False, True):
    run(f"'Pay $12.50 by 3:05 pm' clean_text={ct}", lambda: m.generate("Pay $12.50 by 3:05 pm.", voice="Jasper", clean_text=ct))

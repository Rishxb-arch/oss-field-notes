"""Quick before/after check for kittentts-small-fixes.patch (run it on main, then again after applying the patch).

usage: python check_patch.py [model]      (default: KittenML/kitten-tts-nano-0.8)
"""
import contextlib
import io
import sys

import numpy as np
from kittentts import KittenTTS

m = KittenTTS(sys.argv[1] if len(sys.argv) > 1 else "KittenML/kitten-tts-nano-0.8")


def check(label, fn):
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(io.StringIO()):
            out = fn()
        print(f"[ok ] {label}: {out}")
    except Exception as e:  # noqa: BLE001
        print(f"[err] {label}: {type(e).__name__}: {str(e)[:160]}")


check("empty input", lambda: np.asarray(m.generate("", voice="Jasper")).shape)
check("voice 'jasper'", lambda: m.generate("hello", voice="jasper"))
check("speed=0", lambda: m.generate("hello there.", voice="Jasper", speed=0))
check("generate_to_file(clean_text=False)", lambda: m.generate_to_file("Hi 3 cats.", "check.wav", voice="Jasper", clean_text=False) or "written")
with contextlib.redirect_stdout(io.StringIO()) as cap:
    m.generate("Hi.", voice="Jasper")
print("stdout noise from generate():", repr(cap.getvalue()))

"""Offline: would an 'identifier must appear verbatim' guard fix the hosted endpoint's misses?
Input: hosted_labeled.json (public endpoint responses). No network."""
import json, re
IDENT = re.compile(r"\*[A-Z]{2,}\??|:[A-Z][A-Za-z:]+\??|0x[0-9A-Fa-f]+|\bFC\d{1,3}\b|\b[A-Z][A-Z0-9]*(?:[_.][A-Za-z0-9]+)+\b")
def idents(q): return [m.group(0) for m in IDENT.finditer(q)]
def norm(s): return re.sub(r"\s+", "", s).upper()
def variants(tok):
    t = tok.upper(); v = {t}
    m = re.fullmatch(r"FC(\d+)", t)
    if m: n = int(m.group(1)); v |= {f"0X{n:02X}", f"{n:02d}(0X{n:02X})"}
    if "X_" in t: v.add(t.replace("X_", "_"))          # GPIOx_MODER -> GPIO_MODER family
    return v
def hits(text): return re.split(r"^### ", text, flags=re.M)[1:]
rows = json.load(open("hosted_labeled.json"))
print(f"{'label':5} {'endpoint':9} {'guard':9} {'top-hit has id':14} query")
agg = {}
for r in rows:
    ids = idents(r["q"]); hs = hits(r["text"])
    endpoint = "no_match" if "No confident match" in r["text"] else "hits"
    top_has = bool(ids) and bool(hs) and any(any(v in norm(hs[0]) for v in variants(i)) for i in ids)
    any_has = bool(ids) and any(any(any(v in norm(h) for v in variants(i)) for i in ids) for h in hs)
    guard = endpoint if not ids else ("hits" if (endpoint == "hits" and any_has) else "no_match")
    ok_end = (endpoint == "hits") == (r["label"] == "real"); ok_g = (guard == "hits") == (r["label"] == "real")
    agg.setdefault("endpoint", []).append(ok_end); agg.setdefault("guard", []).append(ok_g)
    agg.setdefault("top_has_real", []).append(top_has) if r["label"] == "real" else None
    print(f"{r['label']:5} {endpoint:9} {guard:9} {str(top_has):14} {r['q']}   ids={ids}")
print({k: f"{sum(v)}/{len(v)}" for k, v in agg.items()})

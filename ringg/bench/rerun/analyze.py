import json,glob,re
def parse(text):
    m=re.search(r"\{.*\}",text,re.S)
    try: return json.loads(m.group(0))
    except Exception: return None
def outcome(j):
    if not isinstance(j,dict): return None
    c=j.get("classification",j if "call_outcome" in j else None)
    if isinstance(c,dict): return c.get("call_outcome")
    if isinstance(c,str): return c
    return None
for f in sorted(glob.glob("out_*.json")):
    d=json.load(open(f)); ok=0; js=0; print("\n##",f)
    for r in d:
        j=parse(r["text"]); js+= j is not None; o=outcome(j); ok+= (o==r["gold"])
        cls=(j or {}).get("classification") if isinstance(j,dict) else None
        print(f"  {r['case']:20s} gold={r['gold']:18s} pred={o!s:18s} classification_type={type(cls).__name__ if cls is not None else '-'} top_keys={sorted(j.keys()) if isinstance(j,dict) else None}")
    print(f"  JSON valid {js}/{len(d)}  outcome correct {ok}/{len(d)}")

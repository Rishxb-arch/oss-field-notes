import json, sys, time, torch, re
from transformers import AutoTokenizer, AutoModelForCausalLM
from cases import CASES, SCHEMA
import copy, cases
if len(sys.argv)>3 and sys.argv[3]=="flat":
    SCHEMA=copy.deepcopy(SCHEMA); SCHEMA["properties"]["classification"]={"type":"string","enum":cases.CLASSIFICATION["properties"]["call_outcome"]["enum"]}
torch.set_num_threads(4)
name = sys.argv[1]; variant = sys.argv[2] if len(sys.argv) > 2 else "sys_schema"
import os
path = os.path.join(os.environ.get("MODELS_DIR", "models"), name)  # git clone https://huggingface.co/RinggAI/<name>
tok = AutoTokenizer.from_pretrained(path)
t0 = time.time(); model = AutoModelForCausalLM.from_pretrained(path, dtype=torch.bfloat16); model.eval()
print(f"load {time.time()-t0:.1f}s", flush=True)
out = []
for cid, gold, tr in CASES:
    schema = json.dumps(SCHEMA)
    if variant == "sys_schema":
        msgs = [{"role": "system", "content": f"Analyse the call transcript and respond with JSON matching this schema:\n{schema}"},
                {"role": "user", "content": tr}]
    elif variant == "user_only":
        msgs = [{"role": "user", "content": f"Transcript:\n{tr}\n\nResponse schema:\n{schema}"}]
    elif variant == "no_schema":
        msgs = [{"role": "user", "content": tr}]
    ids = tok.apply_chat_template(msgs, add_generation_prompt=True, return_tensors="pt", return_dict=True)
    t = time.time()
    with torch.no_grad():
        g = model.generate(**ids, max_new_tokens=300, do_sample=False)
    text = tok.decode(g[0][ids["input_ids"].shape[1]:], skip_special_tokens=True)
    dt = time.time() - t; ntok = g.shape[1] - ids["input_ids"].shape[1]
    try:
        m = re.search(r"\{.*\}", text, re.S); j = json.loads(m.group(0)) if m else None; ok = j is not None
    except Exception: j = None; ok = False
    fenced = text.strip().startswith("```")
    pred = (j or {}).get("classification", {}).get("call_outcome") if isinstance((j or {}).get("classification"), dict) else None
    rec = dict(case=cid, gold=gold, pred=pred, json_ok=ok, fenced=fenced, keys=sorted(j.keys()) if isinstance(j, dict) else None,
               in_tokens=ids["input_ids"].shape[1], out_tokens=int(ntok), secs=round(dt, 1), text=text)
    out.append(rec); print(json.dumps({k: v for k, v in rec.items() if k != "text"}), flush=True)
json.dump(out, open(f"out_{name}_{variant}{'_'+sys.argv[3] if len(sys.argv)>3 else ''}.json", "w"), ensure_ascii=False, indent=1)

# Evaluate a tiny local RAG QA set with fi.evals: local heuristics + Ollama judge via litellm. No API keys.
import json, time, os, traceback
os.environ.setdefault("OLLAMA_API_BASE", "http://localhost:11434")
from fi.evals import evaluate
data = [
  {"q":"What is the refund window?", "ctx":"Refunds are accepted within 30 days of delivery if the item is unused.", "ans":"You can get a refund within 30 days of delivery, if unused."},
  {"q":"Do you ship to Sri Lanka?", "ctx":"We ship to India, Nepal and Bhutan only.", "ans":"Yes, we ship to Sri Lanka within 5 days."},   # hallucinated
  {"q":"How do I reset my password?", "ctx":"Click 'Forgot password' on the login page and follow the emailed link.", "ans":"Use the 'Forgot password' link on the login page, then follow the email."},
]
def run(name, fn):
    t=time.time()
    try:
        r=fn(); print(f"[{name}] {time.time()-t:.1f}s ->", r); return r
    except Exception as e:
        print(f"[{name}] EXC {time.time()-t:.1f}s {type(e).__name__}: {str(e)[:500]}")
def show(r):
    if hasattr(r, "results"): return [(x.eval_name if hasattr(x,'eval_name') else None, getattr(x,'score',None), (getattr(x,'reason','') or '')[:90]) for x in r.results]
    return (getattr(r,'eval_name',None), getattr(r,'score',None), (getattr(r,'reason','') or '')[:120], getattr(r,'error',None) if hasattr(r,'error') else None)
for i,d in enumerate(data):
    run(f"local faithfulness #{i}", lambda d=d: show(evaluate("faithfulness", output=d["ans"], context=d["ctx"], engine="local")))
run("local batch metrics", lambda: show(evaluate(["contains_valid_link","is_json","one_line"], output="See https://example.com for details", engine="local")))
run("llm judge (ollama) groundedness #1", lambda: show(evaluate("groundedness", output=data[1]["ans"], context=data[1]["ctx"], input=data[1]["q"], engine="llm", model="ollama_chat/qwen2.5:1.5b-instruct")))
run("llm custom prompt (ollama)", lambda: show(evaluate(prompt="Score 1 if the answer is fully supported by the context, else 0.\nContext: {context}\nAnswer: {output}", output=data[1]["ans"], context=data[1]["ctx"], engine="llm", model="ollama_chat/qwen2.5:1.5b-instruct")))
run("unknown metric", lambda: show(evaluate("faithfullness", output="x", context="y", engine="local")))
run("missing context", lambda: show(evaluate("faithfulness", output="x", engine="local")))
run("no engine, no key", lambda: show(evaluate("groundedness", output="x", context="y")))

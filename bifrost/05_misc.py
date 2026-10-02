import time, json, httpx
from openai import OpenAI
B="http://localhost:8080"
c=OpenAI(base_url=B+"/v1", api_key="x", max_retries=0, timeout=240)
def run(name, fn):
    t=time.time()
    try: out=fn(); print(f"[{name}] OK {time.time()-t:.1f}s ->", out)
    except Exception as e: print(f"[{name}] EXC {time.time()-t:.1f}s {type(e).__name__}: {str(e)[:500]}")
E="ollama/nomic-embed-text:latest"
run("embed dimensions=256", lambda: len(c.embeddings.create(model=E, input="hello", dimensions=256, encoding_format="float").data[0].embedding))
run("direct ollama /v1 dimensions=256", lambda: len(httpx.post("http://localhost:11434/v1/embeddings", json={"model":"nomic-embed-text","input":"hello","dimensions":256}, timeout=120).json()["data"][0]["embedding"]))
run("anthropic count_tokens", lambda: httpx.post(B+"/anthropic/v1/messages/count_tokens", json={"model":"ollama/qwen2.5:0.5b-instruct","messages":[{"role":"user","content":"hello there"}]}, timeout=120).text[:300])
run("litellm-compat route", lambda: httpx.post(B+"/litellm/v1/chat/completions", json={"model":"ollama/qwen2.5:0.5b-instruct","messages":[{"role":"user","content":"hi"}],"max_tokens":5}, timeout=120).text[:300])
run("text completions", lambda: c.completions.create(model="ollama/qwen2.5:0.5b-instruct", prompt="The capital of France is", max_tokens=5).choices[0].text)
run("responses api", lambda: c.responses.create(model="ollama/qwen2.5:0.5b-instruct", input="Say OK", max_output_tokens=16).output_text)
run("metrics", lambda: [l for l in httpx.get(B+"/metrics").text.splitlines() if l.startswith("bifrost_") ][:5])

import time, json, httpx
from openai import OpenAI
import anthropic
c=OpenAI(base_url="http://localhost:8080/v1", api_key="x")
def run(name, fn):
    t=time.time()
    try: out=fn(); print(f"[{name}] OK {time.time()-t:.1f}s ->", out)
    except Exception as e: print(f"[{name}] EXC {time.time()-t:.1f}s {type(e).__name__}: {str(e)[:700]}")
# fallbacks in body (documented bifrost extension)
run("fallback body", lambda: (lambda r: (r.model, r.choices[0].message.content[:40]))(c.chat.completions.create(model="ollama/nope:1b", messages=[{"role":"user","content":"hi"}], extra_body={"fallbacks":["ollama/qwen2.5:0.5b-instruct"]})))
a=anthropic.Anthropic(base_url="http://localhost:8080/anthropic", api_key="x")
run("anthropic msg", lambda: (lambda r: (r.model, r.stop_reason, r.content[0].text[:60], r.usage))(a.messages.create(model="ollama/qwen2.5:1.5b-instruct", max_tokens=100, messages=[{"role":"user","content":"Say hello in Hindi"}])))
def astream():
    out=[]; evs=[]
    with a.messages.stream(model="ollama/qwen2.5:1.5b-instruct", max_tokens=60, messages=[{"role":"user","content":"Count 1 to 3"}]) as s:
        for ev in s: evs.append(ev.type)
        fm=s.get_final_message()
    return sorted(set(evs)), fm.content[0].text[:40], fm.stop_reason, fm.usage
run("anthropic stream", astream)
tools=[{"name":"get_weather","description":"weather for a city","input_schema":{"type":"object","properties":{"city":{"type":"string"}},"required":["city"]}}]
run("anthropic tools", lambda: (lambda r: (r.stop_reason, [(b.type, getattr(b,'name',None), getattr(b,'input',None)) for b in r.content]))(a.messages.create(model="ollama/qwen2.5:1.5b-instruct", max_tokens=200, tools=tools, messages=[{"role":"user","content":"What's the weather in Pune?"}])))
run("anthropic system+multi-turn", lambda: a.messages.create(model="ollama/qwen2.5:1.5b-instruct", max_tokens=50, system="Answer in one word.", messages=[{"role":"user","content":"Capital of India?"},{"role":"assistant","content":"Delhi"},{"role":"user","content":"And of Japan?"}]).content[0].text)

import asyncio, time, json, base64, numpy as np
from openai import OpenAI, AsyncOpenAI
B="http://localhost:8080/v1"
c=OpenAI(base_url=B, api_key="x"); ac=AsyncOpenAI(base_url=B, api_key="x")
M="ollama/qwen2.5:1.5b-instruct"
def run(name, fn):
    t=time.time()
    try: print(f"[{name}] OK {time.time()-t:.1f}s ->", fn())
    except Exception as e: print(f"[{name}] EXC {type(e).__name__}: {str(e)[:500]}")
run("chat", lambda: c.chat.completions.create(model=M, messages=[{"role":"user","content":"2+2? number only"}]).choices[0].message.content)
def stream():
    s=c.chat.completions.create(model=M, messages=[{"role":"user","content":"Count 1 to 5"}], stream=True, stream_options={"include_usage":True})
    parts=[]; usage=None; n=0
    for ch in s:
        n+=1
        if ch.choices: parts.append(ch.choices[0].delta.content or "")
        if getattr(ch,"usage",None): usage=ch.usage
    return n, "".join(parts)[:60], usage
run("stream+usage", stream)
schema={"type":"object","properties":{"title":{"type":"string"},"priority":{"type":"integer","minimum":1,"maximum":5},"tags":{"type":"array","items":{"type":"string"}}},"required":["title","priority","tags"],"additionalProperties":False}
run("json_schema", lambda: c.chat.completions.create(model=M, messages=[{"role":"user","content":"Ticket for: Login 500s on Safari with emoji password, urgent"}], response_format={"type":"json_schema","json_schema":{"name":"t","schema":schema,"strict":True}}).choices[0].message.content)
tools=[{"type":"function","function":{"name":"get_weather","description":"weather","parameters":{"type":"object","properties":{"city":{"type":"string"}},"required":["city"]}}}]
run("tools", lambda: c.chat.completions.create(model=M, messages=[{"role":"user","content":"Weather in Pune?"}], tools=tools).choices[0].message.tool_calls)
run("embed default (sdk sends base64)", lambda: (lambda r: (len(r.data), len(r.data[0].embedding), r.data[0].embedding[:3]))(c.embeddings.create(model="ollama/nomic-embed-text:latest", input=["hello","world"])))
run("embed float", lambda: (lambda r: (len(r.data), len(r.data[0].embedding), r.data[0].embedding[:3]))(c.embeddings.create(model="ollama/nomic-embed-text:latest", input=["hello","world"], encoding_format="float")))
run("bad model", lambda: c.chat.completions.create(model="ollama/nope:1b", messages=[{"role":"user","content":"x"}]))
run("no provider prefix", lambda: c.chat.completions.create(model="qwen2.5:1.5b-instruct", messages=[{"role":"user","content":"x"}]).model)
run("empty messages", lambda: c.chat.completions.create(model=M, messages=[]))
async def conc():
    t=time.time()
    async def one(i):
        r=await ac.chat.completions.create(model="ollama/qwen2.5:0.5b-instruct", messages=[{"role":"user","content":f"Reply with {i} only"}], max_tokens=8)
        return r.choices[0].message.content.strip()
    res=await asyncio.gather(*[one(i) for i in range(10)], return_exceptions=True)
    return f"{time.time()-t:.1f}s", res
run("10 concurrent", lambda: asyncio.run(conc()))

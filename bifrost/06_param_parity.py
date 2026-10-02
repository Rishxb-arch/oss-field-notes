import httpx, json
body={"model":"qwen2.5:0.5b-instruct","messages":[{"role":"user","content":"List the numbers 1 to 10 separated by commas."}],"max_tokens":40,"seed":7,"temperature":0,"stop":["5"],"logprobs":True,"top_logprobs":2}
d=httpx.post("http://localhost:11434/v1/chat/completions", json=body, timeout=200).json()
b=dict(body, model="ollama/"+body["model"])
g=httpx.post("http://localhost:8080/v1/chat/completions", json=b, timeout=200).json()
for name,r in (("ollama direct",d),("via bifrost",g)):
    ch=r["choices"][0]; lp=ch.get("logprobs")
    print(f"{name}: finish={ch['finish_reason']} content={ch['message']['content']!r} logprobs={'present n='+str(len(lp['content'])) if lp and lp.get('content') else lp}")

from openai import OpenAI
import anthropic, json
B="http://localhost:8093"
c=OpenAI(base_url=B+"/v1", api_key="x"); a=anthropic.Anthropic(base_url=B+"/anthropic", api_key="x")
M="ollama/qwen2.5:1.5b-instruct"; q=[{"role":"user","content":"What's the weather in Pune?"}]
open("sniff.jsonl","w").close()
r1=c.chat.completions.create(model=M,messages=q,tools=[{"type":"function","function":{"name":"get_weather","description":"weather for a city","parameters":{"type":"object","properties":{"city":{"type":"string"}},"required":["city"]}}}])
r2=a.messages.create(model=M,max_tokens=200,messages=q,tools=[{"name":"get_weather","description":"weather for a city","input_schema":{"type":"object","properties":{"city":{"type":"string"}},"required":["city"]}}])
print("openai args:", r1.choices[0].message.tool_calls[0].function.arguments if r1.choices[0].message.tool_calls else r1.choices[0].message.content)
print("anthropic:", r2.content)
for l in open("sniff.jsonl"):
    d=json.loads(l)
    if d["path"].endswith("chat/completions") or d["path"].startswith("/api/chat"):
        print(d["path"], json.dumps(json.loads(d["body"]), indent=None)[:1200]); print()

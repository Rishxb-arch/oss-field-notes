from openai import OpenAI
import anthropic
c=OpenAI(base_url="http://localhost:8080/v1", api_key="x")
a=anthropic.Anthropic(base_url="http://localhost:8080/anthropic", api_key="x")
M="ollama/qwen2.5:1.5b-instruct"
q=[{"role":"user","content":"What's the weather in Pune?"}]
ot=[{"type":"function","function":{"name":"get_weather","description":"weather for a city","parameters":{"type":"object","properties":{"city":{"type":"string"}},"required":["city"]}}}]
at=[{"name":"get_weather","description":"weather for a city","input_schema":{"type":"object","properties":{"city":{"type":"string"}},"required":["city"]}}]
o=[bool(c.chat.completions.create(model=M,messages=q,tools=ot,temperature=0).choices[0].message.tool_calls) for _ in range(3)]
r=[a.messages.create(model=M,max_tokens=200,tools=at,messages=q) for _ in range(3)]
print("openai path tool_call:", o)
print("anthropic path tool_use:", [x.stop_reason for x in r])
print("anthropic text sample:", repr(r[0].content[0].text[:300]) if r[0].content[0].type=="text" else r[0].content)

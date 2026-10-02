#!/bin/bash
# Repro: Bifrost raises max_tokens < 16 to 16 for Ollama. Needs: ollama serve + qwen2.5:0.5b-instruct,
# Bifrost started with: npx -y @maximhq/bifrost -app-dir ./app2 -port 8080   (app2/config.json = Ollama provider from docs)
Q='{"role":"user","content":"Is Paris in France? Answer yes or no, then explain at length."}'
for mt in 1 3 5; do
  printf "max_tokens=%s  bifrost: " $mt
  curl -s localhost:8080/v1/chat/completions -H 'content-type: application/json' \
    -d "{\"model\":\"ollama/qwen2.5:0.5b-instruct\",\"messages\":[$Q],\"max_tokens\":$mt}" \
    | python3 -c "import sys,json;d=json.load(sys.stdin);print(d['choices'][0]['finish_reason'], d['usage']['completion_tokens'])"
  printf "max_tokens=%s  ollama : " $mt
  curl -s localhost:11434/v1/chat/completions \
    -d "{\"model\":\"qwen2.5:0.5b-instruct\",\"messages\":[$Q],\"max_tokens\":$mt}" \
    | python3 -c "import sys,json;d=json.load(sys.stdin);print(d['choices'][0]['finish_reason'], d['usage']['completion_tokens'])"
done

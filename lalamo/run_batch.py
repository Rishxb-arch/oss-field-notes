"""POST a list of requests to a running `lalamo server` and print the finished batch compactly.

usage: python run_batch.py batch_req.json [http://127.0.0.1:8293]
Standard library only.
"""
import json
import sys
import time
import urllib.error
import urllib.request

path = sys.argv[1]
base = (sys.argv[2] if len(sys.argv) > 2 else "http://127.0.0.1:8293").rstrip("/")

req = urllib.request.Request(
    f"{base}/batches", data=open(path, "rb").read(), headers={"Content-Type": "application/json"}, method="POST"
)
try:
    with urllib.request.urlopen(req) as r:
        batch = json.load(r)
except urllib.error.HTTPError as e:
    sys.exit(f"POST /batches -> HTTP {e.code}: {e.read().decode()}")
print("POST /batches -> 202", batch["id"])

t0 = time.time()
while True:
    with urllib.request.urlopen(f"{base}/batches/{batch['id']}") as r:
        batch = json.load(r)
    if batch["status"] != "in_progress":
        break
    time.sleep(5)
print(f"status={batch['status']} completed={batch['completed']}/{batch['total']} after {time.time() - t0:.0f}s error={batch['error']!r}")
for res in batch["results"]:
    print(f"  {res['sequence_id']}: response={res['response']!r}")
    if res["chain_of_thought"]:
        print(f"      chain_of_thought={res['chain_of_thought'][:90]!r}...")

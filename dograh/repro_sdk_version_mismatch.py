"""Issue 4: dograh-sdk from PyPI (0.1.8) vs a Dograh 1.47.0 server.

usage:  pip install dograh-sdk==0.1.8
        DOGRAH_API_KEY=<key created in the UI> python repro_sdk_version_mismatch.py
The same call works with the SDK from the repository's main branch (still labelled 0.1.8).
"""
import os

from dograh_sdk import DograhClient, Workflow

API = os.getenv("DOGRAH_API_ENDPOINT", "http://127.0.0.1:8000")

with DograhClient(base_url=API, api_key=os.environ["DOGRAH_API_KEY"]) as client:
    wf = Workflow(client=client, name="sdk mismatch repro")
    wf.add(type="startCall", name="greeting", prompt="Say hello.")   # -> client.get_node_type("startCall") -> NodeSpec.model_validate
    print("ok: node spec validated")

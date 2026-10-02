# agent-learning-kit 0.1.0: a missing required input is reported as status="completed", score=0.0, error=None
# (indistinguishable from a genuinely failing output). A typo'd metric name, by contrast, is status="failed".
from fi.evals import evaluate
r = evaluate("faithfulness", engine="local", output="We ship to India.")          # forgot context=
print("missing context :", r.status, r.score, r.passed, r.error)
r = evaluate("groundedness", output="We ship to India.", context="We ship to India only.")  # forgot input=
print("missing query   :", r.status, r.score, r.passed, r.error)
r = evaluate("faithfullness", engine="local", output="x", context="y")
print("typo metric     :", r.status, r.score, r.error)
r = evaluate("faithfulness", engine="local", output="Yes.", context="We ship to India, Nepal and Bhutan only.")
print("vacuous 'Yes.'  :", r.status, r.score, r.passed, r.reason)

# provider.py
from agent_under_test import answer
def call_api(prompt, options, context):
    return {"output": answer(prompt)["answer"]}
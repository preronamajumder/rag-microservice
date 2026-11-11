"""REPLACE THIS with a call into your real agent / RAG pipeline.

Contract: answer(question) -> {"answer": str, "sources": [str, ...]}
`sources` = the retrieved chunks / tool outputs the answer was based on.
The judge uses them to check groundedness, so return them if you can.
"""
import os
from llm import chat


def answer(question: str) -> dict:
    # Placeholder: a bare LLM with no retrieval. Swap for your RAG / agent call.
    text = chat(question, system="Answer concisely. If you don't know, say so.",
                model=os.getenv("AGENT_MODEL", "llama3.1:8b"))
    return {"answer": text, "sources": []}


def answer_mcp(question, user=None):
    result = agent.invoke({"messages": [("user", question)]})
    msgs = result["messages"]
    calls = [tc for m in msgs for tc in (getattr(m, "tool_calls", None) or [])]
    return {
        "answer": msgs[-1].content,                                   # final reply
        "sources": [m.content for m in msgs if m.type == "tool"],     # tool outputs
        "tool_calls": [{"name": c["name"], "args": c["args"]} for c in calls],
    }
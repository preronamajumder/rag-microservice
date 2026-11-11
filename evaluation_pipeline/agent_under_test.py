"""REPLACE the body of answer() with a call into your real agent / RAG pipeline.

Contract: answer(question) -> {"answer": str, "sources": [str, ...]}
Keep the system prompt in prompts/system.txt and the model in AGENT_MODEL, so that a prompt or
model change is a visible diff in git - that is what triggers the CI eval.
"""
import os
from pathlib import Path
from llm import chat

SYSTEM_PROMPT = Path(__file__).parent.joinpath("prompts", "system.txt").read_text()


def answer(question: str) -> dict:
    # Placeholder: bare LLM, no retrieval. Swap for your RAG / agent call.
    text = chat(question, system=SYSTEM_PROMPT, model=os.getenv("AGENT_MODEL", "llama3.1:8b"))
    return {"answer": text, "sources": []}
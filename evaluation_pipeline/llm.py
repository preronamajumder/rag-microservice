"""Tiny LLM client. Backends: ollama (default, local), openai (any OpenAI-compatible API), mock (offline test)."""
import os
import requests


def chat(prompt, system="", model=None, temperature=0.0, json_mode=False):
    backend = os.getenv("LLM_BACKEND", "ollama")
    model = model or os.getenv("JUDGE_MODEL", "llama3.1:8b")
    messages = [{"role": "system", "content": system}, {"role": "user", "content": prompt}]

    if backend == "mock":
        return os.getenv("MOCK_REPLY", '{"correctness": 4, "groundedness": 4, "reason": "mock"}')

    if backend == "ollama":
        body = {"model": model, "messages": messages, "stream": False,
                "options": {"temperature": temperature}}
        if json_mode:
            body["format"] = "json"
        r = requests.post(os.getenv("OLLAMA_URL", "http://localhost:11434") + "/api/chat",
                          json=body, timeout=300)
        r.raise_for_status()
        return r.json()["message"]["content"]

    if backend == "openai":
        body = {"model": model, "messages": messages, "temperature": temperature}
        if json_mode:
            body["response_format"] = {"type": "json_object"}
        r = requests.post(os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1") + "/chat/completions",
                          headers={"Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}"},
                          json=body, timeout=300)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]

    raise ValueError(f"Unknown LLM_BACKEND: {backend}")
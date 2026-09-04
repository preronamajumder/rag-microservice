"""
FastAPI microservice for the PDF RAG system — query only.

Ingestion is still done via ingest.py (run it once, or whenever you add a
new PDF). This service just answers questions against whatever is already
in Qdrant.

Run locally:
    uvicorn app:app --reload --host 0.0.0.0 --port 8000

Run in Docker: see Dockerfile / docker-compose.yml
"""

import os
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from query import build_chain

# --- Configuration (override via environment variables / docker-compose) ---
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
EMBED_MODEL = os.getenv("EMBED_MODEL", "nomic-embed-text")
LLM_MODEL = os.getenv("LLM_MODEL", "llama3.1")
DEFAULT_COLLECTION = os.getenv("DEFAULT_COLLECTION", "book_rag")
DEFAULT_K = int(os.getenv("DEFAULT_K", "4"))

app = FastAPI(title="PDF RAG Query API", version="1.0")

# Cache built chains per (collection, k) so we don't rebuild on every request
_chain_cache = {}


def get_chain(collection: str, k: int):
    key = (collection, k)
    if key not in _chain_cache:
        _chain_cache[key] = build_chain(
            collection, QDRANT_URL, EMBED_MODEL, LLM_MODEL, k, OLLAMA_URL
        )
    return _chain_cache[key]


class QueryRequest(BaseModel):
    question: str
    collection: Optional[str] = None
    k: Optional[int] = None


class QueryResponse(BaseModel):
    answer: str
    sources: List[str]


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/query", response_model=QueryResponse)
def query_rag(req: QueryRequest):
    collection = req.collection or DEFAULT_COLLECTION
    k = req.k or DEFAULT_K

    try:
        chain, retriever = get_chain(collection, k)
        answer = chain.invoke(req.question)
        sources = retriever.invoke(req.question)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {e}")

    return QueryResponse(
        answer=answer,
        sources=[d.page_content[:300] for d in sources],
    )

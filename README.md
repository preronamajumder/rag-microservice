# PDF RAG with Ollama + Qdrant + LangChain

## How it works

- **ingest.py** — Run once (on your host, with Python) per PDF. Loads it
  with LangChain's `PyPDFLoader`, splits it into overlapping chunks with
  `RecursiveCharacterTextSplitter`, embeds each chunk with a local Ollama
  embedding model, and writes the vectors into a Qdrant collection.
- **app.py** — A FastAPI microservice with a single `/query` endpoint.
  It embeds your question, retrieves the top-k most similar chunks from
  Qdrant, and feeds them as context to a local Ollama chat model to
  generate a grounded answer. This is the piece that runs in Docker.
- **query.py** — Same logic as a CLI script, useful for testing without
  the API.

## 1. Install Ollama and pull models (on your host machine — not in Docker)

```bash
# https://ollama.com/download
ollama pull nomic-embed-text   # embedding model
ollama pull llama3.1           # chat model (swap for any model you have)
```

Ollama needs to be running (check the tray icon / run `ollama --version`).

## 2. Ingest your book (also on your host, before starting the API)

```bash
pip install -r requirements.txt
python ingest.py path/to/book.pdf --collection book_rag --qdrant-url http://localhost:6333
```

This step needs Qdrant reachable. Either start it standalone first:
```bash
docker run -p 6333:6333 -p 6334:6334 qdrant/qdrant
```
or bring up the full stack from step 3 and then run ingest.py against
`http://localhost:6333` (the compose file publishes that port to your host).

## 3. Build and run the microservice

```bash
docker compose up --build
```

This starts two containers:
- `qdrant` — the vector database, on `localhost:6333`
- `rag-api` — the FastAPI query service, on `localhost:8000`

The API container reaches Ollama on your host via `host.docker.internal`
(already wired up in `docker-compose.yml`), so you don't need to
containerize Ollama.

## 4. Call it from Postman

- **Method:** POST
- **URL:** `http://localhost:8000/query`
- **Body:** raw JSON

```json
{
  "question": "What does the author say about X in chapter 2?"
}
```

Optional fields:
```json
{
  "question": "...",
  "collection": "book_rag",
  "k": 4
}
```

**Response:**
```json
{
  "answer": "...",
  "sources": ["chunk text preview 1...", "chunk text preview 2..."]
}
```

Health check: `GET http://localhost:8000/health`

## Notes

- The embedding model used at query time **must match** the one used at
  ingest time, or similarity scores will be meaningless.
- If you re-ingest the same PDF into the same collection, chunks are
  appended, not replaced — delete the Qdrant collection first if you want
  a clean rebuild.
- Swap `llama3.1` for any chat model you've pulled in Ollama (e.g.
  `mistral`, `qwen2.5`, `phi4`) by setting `LLM_MODEL` in
  `docker-compose.yml`.
- The `/query` endpoint caches the retrieval chain per `(collection, k)`
  pair after the first request to that combination, so repeated calls are
  faster. Restart the container if you re-ingest new content into an
  already-queried collection.


"""
Ingest a PDF (e.g. a book) into Qdrant — pure LangChain pipeline.

- LangChain's PyPDFLoader handles PDF loading.
- LangChain's RecursiveCharacterTextSplitter handles chunking.
- LangChain + Ollama handle embeddings and writing to Qdrant.

Usage:
    python ingest.py path/to/book.pdf
    python ingest.py path/to/book.pdf --collection mybook --chunk-size 800
"""

import argparse
from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from langchain_ollama import OllamaEmbeddings
from langchain_qdrant import QdrantVectorStore

from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams


def load_and_chunk_pdf(pdf_path: str, chunk_size: int = 1024, chunk_overlap: int = 200):
    """Load the PDF and split it into overlapping chunks, all via LangChain."""
    loader = PyPDFLoader(pdf_path)
    pages = loader.load()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    docs = splitter.split_documents(pages)
    return docs


def build_qdrant_index(
    docs, collection_name: str, qdrant_url: str, embed_model: str, ollama_url: str = "http://localhost:11434"
):
    """Embed documents with an Ollama embedding model and upsert into Qdrant."""
    embeddings = OllamaEmbeddings(model=embed_model, base_url=ollama_url)
    client = QdrantClient(url=qdrant_url)

    # Probe the embedding dimension so the collection is created with the right size.
    dim = len(embeddings.embed_query("dimension probe"))

    if not client.collection_exists(collection_name):
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
        )
        print(f"Created Qdrant collection '{collection_name}' (dim={dim})")

    vector_store = QdrantVectorStore(
        client=client,
        collection_name=collection_name,
        embedding=embeddings,
    )

    vector_store.add_documents(docs)
    print(f"Indexed {len(docs)} chunks into collection '{collection_name}'")


def main():
    parser = argparse.ArgumentParser(description="Ingest a PDF into Qdrant for RAG")
    parser.add_argument("pdf_path", help="Path to the PDF file")
    parser.add_argument("--collection", default="book_rag", help="Qdrant collection name")
    parser.add_argument("--qdrant-url", default="http://localhost:6333", help="Qdrant server URL")
    parser.add_argument("--embed-model", default="nomic-embed-text", help="Ollama embedding model")
    parser.add_argument("--ollama-url", default="http://localhost:11434", help="Ollama server URL")
    parser.add_argument("--chunk-size", type=int, default=1024, help="Chunk size in characters")
    parser.add_argument("--chunk-overlap", type=int, default=200, help="Chunk overlap in characters")
    args = parser.parse_args()

    if not Path(args.pdf_path).exists():
        raise FileNotFoundError(f"PDF not found: {args.pdf_path}")

    docs = load_and_chunk_pdf(args.pdf_path, args.chunk_size, args.chunk_overlap)
    build_qdrant_index(docs, args.collection, args.qdrant_url, args.embed_model, args.ollama_url)


if __name__ == "__main__":
    main()

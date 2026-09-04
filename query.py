"""
Query the RAG system built by ingest.py.

Retrieves relevant chunks from Qdrant and generates an answer using a
local Ollama LLM, via a LangChain LCEL chain.

Usage:
    python query.py "What is the main theme of chapter 3?"
    python query.py            # interactive mode
"""

import argparse

from langchain_ollama import OllamaEmbeddings, ChatOllama
from langchain_qdrant import QdrantVectorStore
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

from qdrant_client import QdrantClient

PROMPT_TEMPLATE = """You are a helpful assistant answering questions about a book.
Use only the following retrieved context to answer the question.
If the answer isn't in the context, say you don't know — don't make things up.

Context:
{context}

Question: {question}

Answer:"""


def format_docs(docs):
    return "\n\n".join(d.page_content for d in docs)


def build_chain(collection_name, qdrant_url, embed_model, llm_model, k, ollama_url="http://localhost:11434"):
    embeddings = OllamaEmbeddings(model=embed_model, base_url=ollama_url)
    client = QdrantClient(url=qdrant_url)

    vector_store = QdrantVectorStore(
        client=client,
        collection_name=collection_name,
        embedding=embeddings,
    )
    retriever = vector_store.as_retriever(search_kwargs={"k": k})

    llm = ChatOllama(model=llm_model, temperature=0, base_url=ollama_url)
    prompt = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)

    chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )
    return chain, retriever


def ask(chain, retriever, question: str):
    answer = chain.invoke(question)
    print("\nAnswer:\n" + answer)

    sources = retriever.invoke(question)
    print("\n--- Retrieved chunks ---")
    for i, doc in enumerate(sources, 1):
        preview = doc.page_content[:150].replace("\n", " ")
        print(f"[{i}] {preview}...")


def main():
    parser = argparse.ArgumentParser(description="Query the PDF RAG system")
    parser.add_argument("question", nargs="?", help="Question to ask (omit for interactive mode)")
    parser.add_argument("--collection", default="book_rag", help="Qdrant collection name")
    parser.add_argument("--qdrant-url", default="http://localhost:6333", help="Qdrant server URL")
    parser.add_argument("--embed-model", default="nomic-embed-text", help="Ollama embedding model")
    parser.add_argument("--llm-model", default="llama3.1", help="Ollama chat model")
    parser.add_argument("--ollama-url", default="http://localhost:11434", help="Ollama server URL")
    parser.add_argument("--k", type=int, default=4, help="Number of chunks to retrieve")
    args = parser.parse_args()

    chain, retriever = build_chain(
        args.collection, args.qdrant_url, args.embed_model, args.llm_model, args.k, args.ollama_url
    )

    if args.question:
        ask(chain, retriever, args.question)
    else:
        print("Interactive mode. Type 'exit' to quit.")
        while True:
            q = input("\nYour question: ").strip()
            if q.lower() in ("exit", "quit"):
                break
            if q:
                ask(chain, retriever, q)


if __name__ == "__main__":
    main()

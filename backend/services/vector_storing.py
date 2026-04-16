import os
from typing import List

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

CHROMA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "chroma_data")
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
BATCH_SIZE = 100

_chroma_client = None
_embedding_model = None


def _get_chroma_client() -> chromadb.PersistentClient:
    global _chroma_client
    if _chroma_client is None:
        os.makedirs(CHROMA_DIR, exist_ok=True)
        _chroma_client = chromadb.PersistentClient(
            path=CHROMA_DIR,
            settings=Settings(anonymized_telemetry=False)
        )
    return _chroma_client


def _get_embedding_model() -> SentenceTransformer:
    global _embedding_model
    if _embedding_model is None:
        print(f"Loading embedding model '{EMBEDDING_MODEL}'...")
        _embedding_model = SentenceTransformer(EMBEDDING_MODEL)
        print("Model loaded successfully!")
    return _embedding_model


def create_collection(session_id: str):
    client = _get_chroma_client()
    try:
        client.delete_collection(name=session_id)
    except Exception:
        pass
    return client.get_or_create_collection(
        name=session_id,
        metadata={"hnsw:space": "cosine"},
    )


def get_collection(session_id: str):
    client = _get_chroma_client()
    return client.get_collection(name=session_id)


def _get_embeddings(texts: List[str]) -> List[List[float]]:
    model = _get_embedding_model()
    embeddings = model.encode(texts, show_progress_bar=False)
    return embeddings.tolist()


def add_chunks(collection, chunks: List[dict]):
    if not chunks:
        return

    for i in range(0, len(chunks), BATCH_SIZE):
        batch = chunks[i:i + BATCH_SIZE]

        documents = []
        metadatas = []
        ids = []

        for j, chunk in enumerate(batch):
            doc = f"File: {chunk['file_path']} (lines {chunk['start_line']}-{chunk['end_line']})\n\n{chunk['content']}"
            documents.append(doc)
            metadatas.append({
                "file_path": chunk["file_path"],
                "start_line": chunk["start_line"],
                "end_line": chunk["end_line"],
                "language": chunk.get("language", "text"),
            })
            ids.append(f"chunk_{i + j}")

        embeddings = _get_embeddings(documents)

        collection.add(
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids,
        )


def search(collection, query: str, n_results: int = 5) -> List[dict]:
    query_embedding = _get_embeddings([query])[0]

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
        include=["documents", "metadatas", "distances"],
    )

    search_results = []
    if results["documents"] and results["documents"][0]:
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        ):
            search_results.append({
                "content": doc,
                "file_path": meta["file_path"],
                "start_line": meta["start_line"],
                "end_line": meta["end_line"],
                "language": meta.get("language", "text"),
                "relevance_score": 1 - dist,
            })

    return search_results
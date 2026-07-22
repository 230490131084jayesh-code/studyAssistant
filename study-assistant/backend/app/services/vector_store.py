"""Local vector store for retrieval. Uses ChromaDB with a local sentence-transformers
embedding model, so no extra API key or network call is needed for embeddings —
only the final answer/quiz/summary generation calls the Claude API."""
import uuid
from typing import List, Dict

import chromadb
from chromadb.utils import embedding_functions

from app.config import CHROMA_DIR, TOP_K_RESULTS

_client = None
_embedding_fn = None
_collection = None


def _get_collection():
    """Lazily create the Chroma client, embedding function, and collection.

    Deferred until first actual use (not at import time) so the server can
    bind its port immediately on boot instead of loading PyTorch + the
    embedding model before uvicorn even starts listening.
    """
    global _client, _embedding_fn, _collection
    if _collection is None:
        _client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        _embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        _collection = _client.get_or_create_collection(
            name="study_documents",
            embedding_function=_embedding_fn,
        )
    return _collection


def add_document_chunks(doc_id: str, filename: str, chunks: List[dict]) -> int:
    if not chunks:
        return 0
    ids = [f"{doc_id}::{i}" for i in range(len(chunks))]
    documents = [c["text"] for c in chunks]
    metadatas = [
        {"doc_id": doc_id, "filename": filename, "location": c["location"]}
        for c in chunks
    ]
    _get_collection().add(ids=ids, documents=documents, metadatas=metadatas)
    return len(chunks)


def query(question: str, doc_ids: List[str] = None, top_k: int = TOP_K_RESULTS) -> List[Dict]:
    where = {"doc_id": {"$in": doc_ids}} if doc_ids else None
    results = _get_collection().query(
        query_texts=[question],
        n_results=top_k,
        where=where,
    )
    if not results["documents"] or not results["documents"][0]:
        return []

    out = []
    for text, meta in zip(results["documents"][0], results["metadatas"][0]):
        out.append({"text": text, "filename": meta["filename"], "location": meta["location"]})
    return out


def get_all_chunks_for_docs(doc_ids: List[str]) -> List[Dict]:
    """Used for quiz/summary generation over a whole document (not similarity search)."""
    results = _get_collection().get(where={"doc_id": {"$in": doc_ids}})
    out = []
    for text, meta in zip(results["documents"], results["metadatas"]):
        out.append({"text": text, "filename": meta["filename"], "location": meta["location"]})
    return out


def delete_document(doc_id: str) -> None:
    _get_collection().delete(where={"doc_id": doc_id})


def new_doc_id() -> str:
    return uuid.uuid4().hex[:12]
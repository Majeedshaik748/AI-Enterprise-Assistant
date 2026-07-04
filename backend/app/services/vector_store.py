"""
Thin wrapper around ChromaDB so the rest of the app doesn't care which
vector database is in use. Swap in FAISS by implementing the same
interface (add, query, delete_by_document).
"""
from typing import List, Optional

import chromadb
from chromadb.config import Settings as ChromaSettings

from app.core.config import get_settings
from app.utils.logger import get_logger

settings = get_settings()
logger = get_logger(__name__)

_client = None
_collection = None


def _get_collection():
    global _client, _collection
    if _collection is None:
        _client = chromadb.PersistentClient(
            path=settings.CHROMA_PERSIST_DIR,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        _collection = _client.get_or_create_collection(name="documents")
    return _collection


def add_chunks(document_id: str, chunks: List[dict], embeddings: List[List[float]]) -> None:
    """chunks: list of {chunk_index, page_number, text}; embeddings: parallel list of vectors."""
    collection = _get_collection()
    ids = [f"{document_id}:{c['chunk_index']}" for c in chunks]
    documents = [c["text"] for c in chunks]
    metadatas = [
        {"document_id": document_id, "chunk_index": c["chunk_index"], "page_number": c["page_number"]}
        for c in chunks
    ]
    collection.add(ids=ids, documents=documents, embeddings=embeddings, metadatas=metadatas)


def query(query_embedding: List[float], top_k: int = 5, document_ids: Optional[List[str]] = None) -> dict:
    collection = _get_collection()
    where = {"document_id": {"$in": document_ids}} if document_ids else None
    return collection.query(query_embeddings=[query_embedding], n_results=top_k, where=where)


def delete_by_document(document_id: str) -> None:
    collection = _get_collection()
    collection.delete(where={"document_id": document_id})

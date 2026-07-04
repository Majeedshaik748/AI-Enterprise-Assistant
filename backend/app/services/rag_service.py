"""
Core RAG orchestration: ingestion, question answering with citations,
summarization, document comparison, and report generation.
"""
import time
from typing import List, Optional

from app.db.models import Chunk, Document
from app.services import document_processor, llm_provider, vector_store
from app.utils.logger import get_logger
from sqlalchemy.orm import Session

logger = get_logger(__name__)


def ingest_document(db: Session, document: Document) -> None:
    """Extract text, chunk it, embed it, store vectors + chunk metadata."""
    extraction = document_processor.extract_text(document.storage_path, document.file_type)
    chunks = document_processor.chunk_text(extraction.pages)

    if not chunks:
        raise ValueError("No extractable text found in document")

    embeddings = llm_provider.embed_texts([c["text"] for c in chunks])
    vector_store.add_chunks(document.id, chunks, embeddings)

    for c in chunks:
        db.add(Chunk(
            document_id=document.id,
            chunk_index=c["chunk_index"],
            text_preview=c["text"][:500],
            vector_id=f"{document.id}:{c['chunk_index']}",
        ))
    document.page_count = extraction.page_count
    db.commit()


def _retrieve(question: str, top_k: int, document_ids: Optional[List[str]]):
    query_embedding = llm_provider.embed_texts([question])[0]
    results = vector_store.query(query_embedding, top_k=top_k, document_ids=document_ids)
    return results


def answer_question(db: Session, question: str, top_k: int = 5,
                     document_ids: Optional[List[str]] = None) -> dict:
    start = time.time()
    results = _retrieve(question, top_k, document_ids)

    docs = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0] if "distances" in results else [0.0] * len(docs)

    context = "\n\n---\n\n".join(docs)
    prompt = (
        "You are an enterprise knowledge assistant. Answer the question using ONLY "
        "the context below. If the answer is not in the context, say so.\n\n"
        f"CONTEXT:\n{context}\n\nQUESTION:\n{question}"
    )
    answer = llm_provider.generate(prompt)

    sources = []
    for doc_text, meta, dist in zip(docs, metadatas, distances):
        document = db.query(Document).filter(Document.id == meta["document_id"]).first()
        sources.append({
            "document_id": meta["document_id"],
            "filename": document.filename if document else "unknown",
            "chunk_index": meta["chunk_index"],
            "excerpt": doc_text[:300],
            "score": round(1 - float(dist), 4) if dist is not None else 0.0,
        })

    latency_ms = int((time.time() - start) * 1000)
    return {"answer": answer, "sources": sources, "latency_ms": latency_ms}


def summarize_document(db: Session, document: Document) -> str:
    results = vector_store.query(
        llm_provider.embed_texts([f"Summary of {document.filename}"])[0],
        top_k=12,
        document_ids=[document.id],
    )
    docs = results.get("documents", [[]])[0]
    context = "\n\n".join(docs)
    prompt = (
        "Summarize the following document content in a concise executive summary "
        "(bullet points for key facts, then a 2-3 sentence overview):\n\n"
        f"CONTEXT:\n{context}\n\nQUESTION:\nSummarize this document."
    )
    summary = llm_provider.generate(prompt, max_tokens=700)
    document.summary = summary
    db.commit()
    return summary


def compare_documents(db: Session, doc_a: Document, doc_b: Document, focus: Optional[str] = None) -> str:
    results_a = vector_store.query(
        llm_provider.embed_texts([doc_a.filename])[0], top_k=8, document_ids=[doc_a.id]
    )
    results_b = vector_store.query(
        llm_provider.embed_texts([doc_b.filename])[0], top_k=8, document_ids=[doc_b.id]
    )
    context_a = "\n".join(results_a.get("documents", [[]])[0])
    context_b = "\n".join(results_b.get("documents", [[]])[0])

    focus_clause = f" Focus specifically on: {focus}." if focus else ""
    prompt = (
        f"Compare Document A ({doc_a.filename}) and Document B ({doc_b.filename}). "
        f"Highlight key similarities and differences.{focus_clause}\n\n"
        f"CONTEXT:\nDOCUMENT A:\n{context_a}\n\nDOCUMENT B:\n{context_b}\n\n"
        f"QUESTION:\nWhat are the similarities and differences between these two documents?"
    )
    return llm_provider.generate(prompt, max_tokens=800)


def generate_report(db: Session, documents: List[Document], title: str, instructions: Optional[str]) -> str:
    sections = []
    for doc in documents:
        summary = doc.summary or summarize_document(db, doc)
        sections.append(f"## {doc.filename}\n{summary}")

    instructions_clause = f"\n\nAdditional instructions: {instructions}" if instructions else ""
    body = "\n\n".join(sections)
    return f"# {title}\n\n{body}{instructions_clause}"

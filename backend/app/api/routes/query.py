import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.database import get_db
from app.db.models import Document, DocumentStatus, QueryLog, User
from app.schemas.schemas import (CompareRequest, QueryRequest, QueryResponse,
                                  ReportRequest, SummarizeRequest)
from app.services import rag_service

router = APIRouter(prefix="/api/v1", tags=["rag"])


def _get_owned_document(db: Session, document_id: str, current_user: User) -> Document:
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail=f"Document {document_id} not found")
    if current_user.role != "admin" and document.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    if document.status != DocumentStatus.INDEXED:
        raise HTTPException(status_code=409, detail=f"Document is not indexed yet (status={document.status})")
    return document


@router.post("/query", response_model=QueryResponse)
def query_documents(payload: QueryRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if payload.document_ids:
        for doc_id in payload.document_ids:
            _get_owned_document(db, doc_id, current_user)

    result = rag_service.answer_question(
        db, payload.question, top_k=payload.top_k, document_ids=payload.document_ids
    )

    db.add(QueryLog(
        user_id=current_user.id,
        question=payload.question,
        answer=result["answer"],
        sources=json.dumps(result["sources"]),
        latency_ms=result["latency_ms"],
    ))
    db.commit()
    return result


@router.post("/summarize")
def summarize(payload: SummarizeRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    document = _get_owned_document(db, payload.document_id, current_user)
    summary = rag_service.summarize_document(db, document)
    return {"document_id": document.id, "summary": summary}


@router.post("/compare")
def compare(payload: CompareRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    doc_a = _get_owned_document(db, payload.document_id_a, current_user)
    doc_b = _get_owned_document(db, payload.document_id_b, current_user)
    result = rag_service.compare_documents(db, doc_a, doc_b, focus=payload.focus)
    return {"comparison": result}


@router.post("/report")
def report(payload: ReportRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    documents = [_get_owned_document(db, doc_id, current_user) for doc_id in payload.document_ids]
    result = rag_service.generate_report(db, documents, payload.title, payload.instructions)
    return {"report_markdown": result}

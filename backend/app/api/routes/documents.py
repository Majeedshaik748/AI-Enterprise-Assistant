import os
import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.db.database import get_db
from app.db.models import Document, DocumentStatus, User
from app.schemas.schemas import DocumentOut
from app.services import rag_service, vector_store
from app.utils.logger import get_logger

router = APIRouter(prefix="/api/v1/documents", tags=["documents"])
settings = get_settings()
logger = get_logger(__name__)

ALLOWED_EXTENSIONS = {"pdf", "docx", "doc", "pptx", "ppt", "xlsx", "xls", "csv"}


@router.post("/upload", response_model=DocumentOut)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: .{ext}")

    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    stored_name = f"{uuid.uuid4()}.{ext}"
    storage_path = os.path.join(settings.UPLOAD_DIR, stored_name)

    contents = await file.read()
    if len(contents) > settings.MAX_UPLOAD_MB * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File too large")
    with open(storage_path, "wb") as f:
        f.write(contents)

    document = Document(
        owner_id=current_user.id,
        filename=file.filename,
        file_type=ext,
        storage_path=storage_path,
        status=DocumentStatus.PENDING,
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    background_tasks.add_task(_process_document, document.id)
    return document


def _process_document(document_id: str):
    """Runs in the background: extract, chunk, embed, index. Uses its own
    DB session since BackgroundTasks run outside the request scope."""
    from app.db.database import SessionLocal

    db = SessionLocal()
    try:
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            return
        document.status = DocumentStatus.PROCESSING
        db.commit()
        try:
            rag_service.ingest_document(db, document)
            document.status = DocumentStatus.INDEXED
        except Exception as exc:  # noqa: BLE001
            logger.error(f"Failed to index document {document_id}: {exc}")
            document.status = DocumentStatus.FAILED
            document.error_message = str(exc)
        db.commit()
    finally:
        db.close()


@router.get("", response_model=list[DocumentOut])
def list_documents(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    query = db.query(Document)
    if current_user.role != "admin":
        query = query.filter(Document.owner_id == current_user.id)
    return query.order_by(Document.created_at.desc()).all()


@router.get("/{document_id}", response_model=DocumentOut)
def get_document(document_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    if current_user.role != "admin" and document.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    return document


@router.delete("/{document_id}", status_code=204)
def delete_document(document_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    if current_user.role != "admin" and document.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    vector_store.delete_by_document(document.id)
    if os.path.exists(document.storage_path):
        os.remove(document.storage_path)
    db.delete(document)
    db.commit()

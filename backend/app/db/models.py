"""
ORM models: User, Document, Chunk, QueryLog.
"""
import enum
import uuid
from datetime import datetime

from sqlalchemy import (Boolean, Column, DateTime, Enum, ForeignKey, Integer,
                         String, Text)
from sqlalchemy.orm import relationship

# Portable "UUID as string" column (works on both Postgres and SQLite,
# the latter used for fast local test runs).
UUID = lambda **kw: String(36)  # noqa: E731

from app.db.database import Base


def gen_uuid():
    return str(uuid.uuid4())


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    USER = "user"


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    email = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.USER, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    documents = relationship("Document", back_populates="owner", cascade="all, delete-orphan")


class DocumentStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    INDEXED = "indexed"
    FAILED = "failed"


class Document(Base):
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    owner_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)
    filename = Column(String(512), nullable=False)
    file_type = Column(String(50), nullable=False)  # pdf, docx, pptx, xlsx
    storage_path = Column(String(1024), nullable=False)
    status = Column(Enum(DocumentStatus), default=DocumentStatus.PENDING)
    page_count = Column(Integer, nullable=True)
    summary = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    owner = relationship("User", back_populates="documents")
    chunks = relationship("Chunk", back_populates="document", cascade="all, delete-orphan")


class Chunk(Base):
    """Metadata row mirroring what's stored in the vector DB (for admin/debug views)."""
    __tablename__ = "chunks"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    document_id = Column(UUID(as_uuid=False), ForeignKey("documents.id"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    text_preview = Column(String(500), nullable=False)
    vector_id = Column(String(255), nullable=False)  # id in ChromaDB/FAISS

    document = relationship("Document", back_populates="chunks")


class QueryLog(Base):
    """Audit log of every question asked, for admin analytics."""
    __tablename__ = "query_logs"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=True)
    sources = Column(Text, nullable=True)  # JSON-encoded list of source citations
    latency_ms = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

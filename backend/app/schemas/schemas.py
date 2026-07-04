"""
Pydantic request/response schemas.
"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field


# ---------- Auth ----------
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: str
    email: EmailStr
    full_name: Optional[str]
    role: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


# ---------- Documents ----------
class DocumentOut(BaseModel):
    id: str
    filename: str
    file_type: str
    status: str
    page_count: Optional[int]
    summary: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ---------- RAG / Query ----------
class SourceCitation(BaseModel):
    document_id: str
    filename: str
    chunk_index: int
    excerpt: str
    score: float


class QueryRequest(BaseModel):
    question: str
    document_ids: Optional[List[str]] = None  # scope search to specific docs
    top_k: int = 5


class QueryResponse(BaseModel):
    answer: str
    sources: List[SourceCitation]
    latency_ms: int


class SummarizeRequest(BaseModel):
    document_id: str


class CompareRequest(BaseModel):
    document_id_a: str
    document_id_b: str
    focus: Optional[str] = None  # e.g. "differences in pricing terms"


class ReportRequest(BaseModel):
    document_ids: List[str]
    title: str
    instructions: Optional[str] = None


# ---------- Admin ----------
class AdminStats(BaseModel):
    total_users: int
    total_documents: int
    total_queries: int
    documents_by_status: dict

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

class PaperModel(BaseModel):
    """MongoDB document for a research paper."""

    paper_id: str = Field(..., description="SHA256-based unique ID")
    url: str
    title: str
    authors: List[str] = Field(default_factory=list)
    year: Optional[int] = None
    publisher: Optional[str] = None
    conference: Optional[str] = None
    doi: Optional[str] = None
    abstract: Optional[str] = None
    keywords: List[str] = Field(default_factory=list)
    citation_count: Optional[int] = None
    license: Optional[str] = None
    github_url: Optional[str] = None
    dataset: Optional[str] = None
    pdf_url: Optional[str] = None
    pdf_local_path: Optional[str] = None
    thumbnail: Optional[str] = None
    source: Optional[str] = None
    similarity_score: Optional[float] = None
    is_pdf_downloaded: bool = False
    summary: Optional[Dict[str, Any]] = None
    research_gaps: Optional[Dict[str, Any]] = None
    recommendations: Optional[Dict[str, Any]] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True

class SearchHistoryModel(BaseModel):
    """MongoDB document for a user search session."""

    query: str
    understanding: Optional[Dict[str, Any]] = None
    expansion: Optional[Dict[str, Any]] = None
    paper_ids: List[str] = Field(default_factory=list)
    total_results: int = 0
    research_gaps: Optional[Dict[str, Any]] = None
    recommendations: Optional[Dict[str, Any]] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class UserModel(BaseModel):
    """MongoDB document for a user (optional auth)."""

    user_id: str
    name: Optional[str] = None
    email: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class BookmarkModel(BaseModel):
    """MongoDB document for a bookmark."""

    user_id: str = "anonymous"
    paper_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class FeedbackModel(BaseModel):
    """MongoDB document for user feedback."""

    paper_id: Optional[str] = None
    query: Optional[str] = None
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ChatHistoryModel(BaseModel):
    """MongoDB document for a RAG chat message."""

    paper_id: str
    question: str
    answer: str
    chunks_used: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)

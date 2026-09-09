"""
Pydantic v2 schemas for API responses.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

class PaperCardResponse(BaseModel):
    """Condensed paper info for dashboard cards."""

    paper_id: str
    title: str
    authors: List[str] = Field(default_factory=list)
    year: Optional[int] = None
    publisher: Optional[str] = None
    conference: Optional[str] = None
    doi: Optional[str] = None
    abstract: Optional[str] = None
    keywords: List[str] = Field(default_factory=list)
    citation_count: Optional[int] = None
    github_url: Optional[str] = None
    dataset: Optional[str] = None
    pdf_url: Optional[str] = None
    thumbnail: Optional[str] = None
    url: str
    source: Optional[str] = None
    similarity_score: Optional[float] = None
    is_pdf_downloaded: bool = False
    summary: Optional[Dict[str, Any]] = None

    parsed_text: Optional[str] = None
    sections: Optional[Dict[str, str]] = None

    references: List[str] = Field(default_factory=list)
    page_count: Optional[int] = None

class SearchResponse(BaseModel):
    """Response for POST /search."""

    search_id: str
    query: str
    understanding: Optional[Dict[str, Any]] = None
    expansion: Optional[Dict[str, Any]] = None
    papers: List[PaperCardResponse] = Field(default_factory=list)
    total_results: int = 0
    research_gaps: Optional[Dict[str, Any]] = None
    recommendations: Optional[Dict[str, Any]] = None
    processing_time_seconds: float = 0.0

class SummaryResponse(BaseModel):
    """Response for POST /summary."""

    paper_id: str
    title: str
    summary: Dict[str, Any]

class ChatResponse(BaseModel):
    """Response for POST /chat."""

    paper_id: str
    question: str
    answer: str
    chunks_used: List[str] = Field(default_factory=list)

class ChatPrepareResponse(BaseModel):
    """Response for POST /chat/prepare."""

    paper_id: str
    status: str
    chunks_count: int
    message: str

class HistoryItemResponse(BaseModel):
    """Single search history item."""

    search_id: str
    query: str
    total_results: int
    created_at: datetime

class HistoryResponse(BaseModel):
    """Response for GET /history."""

    items: List[HistoryItemResponse] = Field(default_factory=list)
    total: int = 0

class BookmarkResponse(BaseModel):
    """Single bookmark entry."""

    paper_id: str
    title: str
    authors: List[str]
    year: Optional[int] = None
    url: str
    created_at: datetime

class BookmarksListResponse(BaseModel):
    """Response for GET /bookmarks."""

    items: List[BookmarkResponse] = Field(default_factory=list)
    total: int = 0

class HealthResponse(BaseModel):
    """Response for GET /health."""

    status: str
    version: str
    mongodb: str
    faiss_vectors: int
    timestamp: datetime

class ErrorResponse(BaseModel):
    """Standard error envelope."""

    error: str
    detail: Optional[str] = None
    code: int = 400

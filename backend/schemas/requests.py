"""
Pydantic v2 schemas for incoming API requests.
"""

from typing import List, Optional

from pydantic import BaseModel, Field, field_validator

class SearchRequest(BaseModel):
    """Request body for POST /search."""

    query: str = Field(..., min_length=3, max_length=1000, description="Natural language research query")
    max_results: int = Field(default=10, ge=1, le=50)
    year_from: Optional[int] = Field(default=None, ge=1990, le=2030)
    year_to: Optional[int] = Field(default=None, ge=1990, le=2030)
    domains: Optional[List[str]] = None
    force_refresh: bool = False

    @field_validator("query")
    @classmethod
    def query_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Query must not be empty or whitespace.")
        return v.strip()

class SummaryRequest(BaseModel):
    """Request body for POST /summary."""

    paper_id: str = Field(..., min_length=1)
    regenerate: bool = False

class ChatRequest(BaseModel):
    """Request body for POST /chat."""

    paper_id: str = Field(..., min_length=1)
    question: str = Field(..., min_length=3, max_length=1000)
    top_k: int = Field(default=5, ge=1, le=20)

class ChatPrepareRequest(BaseModel):
    """Request body for POST /chat/prepare."""

    paper_id: str = Field(..., min_length=1)

class BookmarkRequest(BaseModel):
    """Request body for POST /bookmark."""

    paper_id: str = Field(..., min_length=1)
    user_id: str = "anonymous"

class FeedbackRequest(BaseModel):
    """Request body for POST /feedback."""

    paper_id: Optional[str] = None
    query: Optional[str] = None
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = Field(default=None, max_length=2000)

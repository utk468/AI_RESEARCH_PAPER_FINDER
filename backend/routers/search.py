"""
FastAPI Router — Search endpoints.
POST /search
GET  /history
"""

import time
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from backend.database.mongodb import get_db, mongodb
from backend.schemas.requests import SearchRequest
from backend.schemas.responses import HistoryResponse, HistoryItemResponse, SearchResponse
from backend.services.search_service import SearchService
from backend.utils.logger import logger

router = APIRouter(prefix="/search", tags=["Search"])
_service = SearchService()

@router.post(
    "",
    response_model=SearchResponse,
    summary="Run a research paper search pipeline",
    status_code=status.HTTP_200_OK,
)
async def run_search(request: SearchRequest):
    """
    Execute the full LangGraph pipeline for the given research query.

    - Understands the query
    - Expands keywords
    - Searches academic sources
    - Downloads and parses PDFs
    - Creates embeddings
    - Summarizes papers
    - Identifies research gaps and makes recommendations
    """
    logger.info(f"[Router/search] POST /search query={request.query!r}")
    try:
        result = await _service.run_search(
            query=request.query,
            max_results=request.max_results,
            year_from=request.year_from,
            year_to=request.year_to,
            force_refresh=request.force_refresh,
        )
        return result
    except Exception as exc:
        logger.error(f"[Router/search] Error: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )

@router.get(
    "/history",
    response_model=HistoryResponse,
    summary="Retrieve recent search history",
)
async def get_history(
    limit: int = Query(default=20, ge=1, le=100),
):
    """Return the most recent search sessions."""
    try:
        docs = await _service.get_history(limit=limit)
        items = [
            HistoryItemResponse(
                search_id=str(doc.get("search_id", "")),
                query=doc.get("query", ""),
                total_results=doc.get("total_results", 0),
                created_at=doc.get("created_at"),
            )
            for doc in docs
            if doc.get("created_at")
        ]
        return HistoryResponse(items=items, total=len(items))
    except Exception as exc:
        logger.error(f"[Router/search] History error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))

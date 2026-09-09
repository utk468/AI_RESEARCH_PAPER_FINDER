"""
FastAPI Router — Bookmarks.
POST /bookmark
GET  /bookmarks
"""

from fastapi import APIRouter, HTTPException, Query, status
from datetime import datetime

from backend.database.mongodb import mongodb
from backend.schemas.requests import BookmarkRequest
from backend.schemas.responses import BookmarkResponse, BookmarksListResponse
from backend.utils.logger import logger

router = APIRouter(prefix="/bookmarks", tags=["Bookmarks"])

@router.post("", summary="Bookmark a paper", status_code=status.HTTP_201_CREATED)
async def add_bookmark(request: BookmarkRequest):
    """Save a paper to bookmarks."""
    paper = await mongodb.papers.find_one(
        {"paper_id": request.paper_id}, {"_id": 0}
    )
    if not paper:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Paper not found: {request.paper_id}",
        )
    try:
        await mongodb.bookmarks.insert_one({
            "user_id": request.user_id,
            "paper_id": request.paper_id,
            "created_at": datetime.utcnow(),
        })
        return {"message": "Bookmarked successfully.", "paper_id": request.paper_id}
    except Exception:

        return {"message": "Already bookmarked.", "paper_id": request.paper_id}

@router.get(
    "",
    response_model=BookmarksListResponse,
    summary="List all bookmarks",
)
async def list_bookmarks(
    user_id: str = Query(default="anonymous"),
    limit: int = Query(default=50, ge=1, le=200),
):
    """Return all bookmarked papers for a user."""
    cursor = mongodb.bookmarks.find(
        {"user_id": user_id}
    ).sort("created_at", -1).limit(limit)
    docs = await cursor.to_list(length=limit)

    items = []
    for doc in docs:
        paper = await mongodb.papers.find_one(
            {"paper_id": doc["paper_id"]}, {"_id": 0}
        )
        if paper:
            items.append(
                BookmarkResponse(
                    paper_id=paper.get("paper_id", ""),
                    title=paper.get("title", ""),
                    authors=paper.get("authors", []),
                    year=paper.get("year"),
                    url=paper.get("url", ""),
                    created_at=doc.get("created_at", datetime.utcnow()),
                )
            )

    return BookmarksListResponse(items=items, total=len(items))

"""
FastAPI Router — Feedback.
POST /feedback
"""

from datetime import datetime

from fastapi import APIRouter, status

from backend.database.mongodb import mongodb
from backend.schemas.requests import FeedbackRequest
from backend.utils.logger import logger

router = APIRouter(prefix="/feedback", tags=["Feedback"])

@router.post("", summary="Submit feedback", status_code=status.HTTP_201_CREATED)
async def submit_feedback(request: FeedbackRequest):
    """Accept user ratings and comments for papers or searches."""
    await mongodb.feedback.insert_one({
        "paper_id": request.paper_id,
        "query": request.query,
        "rating": request.rating,
        "comment": request.comment,
        "created_at": datetime.utcnow(),
    })
    logger.info(f"[Router/feedback] Rating={request.rating} for paper={request.paper_id}")
    return {"message": "Feedback submitted. Thank you!"}

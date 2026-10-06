"""
FastAPI Router — Health check.
GET /health
"""

from datetime import datetime

from fastapi import APIRouter

from backend.database.mongodb import mongodb
from backend.schemas.responses import HealthResponse
from backend.config import settings

router = APIRouter(tags=["Health"])

@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Application health check",
)
async def health_check():
    """Return system health status including MongoDB connectivity."""

    try:
        await mongodb.database.command("ping")
        mongo_status = "connected"
    except Exception:
        mongo_status = "disconnected"

    return HealthResponse(
        status="ok",
        version=settings.APP_VERSION,
        mongodb=mongo_status,
        faiss_vectors=0,
        timestamp=datetime.utcnow(),
    )

"""
FastAPI Router — Paper endpoints.
GET  /paper/{id}
GET  /related/{id}
POST /summary
"""

from fastapi import APIRouter, HTTPException, status

from backend.schemas.requests import SummaryRequest
from backend.schemas.responses import PaperCardResponse, SummaryResponse
from backend.services.paper_service import PaperService
from backend.utils.logger import logger

router = APIRouter(prefix="/paper", tags=["Papers"])
_service = PaperService()

@router.get(
    "/{paper_id}",
    summary="Get full paper details by ID",
)
async def get_paper(paper_id: str):
    """Retrieve complete paper metadata and summary from MongoDB."""
    paper = await _service.get_paper(paper_id)
    if not paper:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Paper not found: {paper_id}",
        )
    paper.pop("_id", None)
    return paper

@router.get(
    "/related/{paper_id}",
    summary="Get semantically related papers",
)
async def get_related(paper_id: str, limit: int = 5):
    """Return papers semantically similar to the given paper using FAISS."""
    related = await _service.get_related_papers(paper_id, limit=limit)
    return {"paper_id": paper_id, "related": related, "total": len(related)}

@router.post(
    "/summary",
    response_model=SummaryResponse,
    summary="Generate or retrieve paper summary",
)
async def get_summary(request: SummaryRequest):
    """
    Generate a grounded paper summary using RAG (or return cached summary).
    Set regenerate=true to force a fresh LLM call.
    """
    paper = await _service.get_paper(request.paper_id)
    if not paper:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Paper not found: {request.paper_id}",
        )

    summary = await _service.generate_summary(
        paper_id=request.paper_id,
        regenerate=request.regenerate,
    )

    if summary is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Unable to generate summary for this paper.",
        )

    return SummaryResponse(
        paper_id=request.paper_id,
        title=paper.get("title", ""),
        summary=summary,
    )

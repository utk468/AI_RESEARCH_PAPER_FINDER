from fastapi import APIRouter, HTTPException, status

from backend.schemas.requests import ChatRequest, ChatPrepareRequest
from backend.schemas.responses import ChatResponse, ChatPrepareResponse
from backend.services.paper_service import PaperService
from backend.utils.logger import logger

router = APIRouter(prefix="/chat", tags=["Chat"])
_service = PaperService()

@router.post(
    "/prepare",
    response_model=ChatPrepareResponse,
    summary="Prepare paper vector store for chat",
    status_code=status.HTTP_200_OK,
)
async def prepare_chat(request: ChatPrepareRequest):
    """
    Auto-embeds the research paper and builds its FAISS index.
    Call this when opening the chat panel to warm up the RAG system.
    """
    logger.info(f"[Router/chat] POST /chat/prepare paper_id={request.paper_id}")
    try:
        res = await _service.prepare_paper_rag(request.paper_id)
        if res.get("status") == "error":
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=res.get("message"),
            )
        return ChatPrepareResponse(**res)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"[Router/chat] Prepare error: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )

@router.post(
    "",
    response_model=ChatResponse,
    summary="Chat with a research paper using RAG",
)
async def chat_with_paper(request: ChatRequest):
    """
    Answer questions about a specific research paper.
    Uses parsed paper text + Groq for grounded answers only.

    Example questions:
    - "What loss function is used?"
    - "What dataset was used for evaluation?"
    - "What are the main contributions?"
    """
    logger.info(
        f"[Router/chat] paper_id={request.paper_id}, question={request.question!r}"
    )

    result = await _service.chat_with_paper(
        paper_id=request.paper_id,
        question=request.question,
        top_k=request.top_k,
    )

    return ChatResponse(
        paper_id=request.paper_id,
        question=request.question,
        answer=result.get("answer", ""),
        chunks_used=result.get("chunks_used", []),
    )

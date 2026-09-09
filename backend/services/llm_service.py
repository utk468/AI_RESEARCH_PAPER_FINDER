"""
LLM service — Groq only (llama-3.3-70b-versatile).
Returns a LangChain-compatible ChatGroq instance.
"""

from functools import lru_cache

from langchain_groq import ChatGroq

from backend.config import settings
from backend.utils.logger import logger

def get_llm() -> ChatGroq:
    """
    Return a cached ChatGroq instance.
    Uses llama-3.3-70b-versatile by default (configurable via GROQ_MODEL).
    """
    if not settings.GROQ_API_KEY:
        raise ValueError(
            "GROQ_API_KEY is not set. "
            "Please add it to your .env file. Get a free key at https://groq.com"
        )

    logger.info(f"[LLMService] Initializing Groq model: {settings.GROQ_MODEL}")
    return ChatGroq(
        model=settings.GROQ_MODEL,
        api_key=settings.GROQ_API_KEY,
        temperature=0.1,
        max_tokens=4096,
    )

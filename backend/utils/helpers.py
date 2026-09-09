"""
General-purpose utility helpers.
"""

import hashlib
import re
import time
import unicodedata
from functools import wraps
from typing import Any, Callable, List, Optional
from urllib.parse import urlparse

from backend.utils.logger import logger

ACADEMIC_DOMAINS: List[str] = [
    "arxiv.org",
    "ieeexplore.ieee.org",
    "dl.acm.org",
    "springer.com",
    "link.springer.com",
    "nature.com",
    "sciencedirect.com",
    "semanticscholar.org",
    "openreview.net",
    "cvf.com",
    "aclanthology.org",
    "paperswithcode.com",
    "researchgate.net",
    "plos.org",
    "biorxiv.org",
    "medrxiv.org",
    "ssrn.com",
]

def is_academic_url(url: str) -> bool:
    """Check whether a URL belongs to a trusted academic domain."""
    try:
        parsed = urlparse(url)
        hostname = parsed.hostname or ""
        return any(
            hostname == domain or hostname.endswith(f".{domain}")
            for domain in ACADEMIC_DOMAINS
        )
    except Exception:
        return False

def is_likely_pdf(url: str) -> bool:
    """Check whether a URL is likely to lead to a PDF document directly or indirectly."""
    url_lower = url.lower()
    if url_lower.endswith(".pdf") or "/pdf/" in url_lower or ".pdf?" in url_lower:
        return True
    if any(domain in url_lower for domain in ["arxiv.org", "openreview.net", "biorxiv.org", "medrxiv.org", "springer.com", "ieeexplore.ieee.org", "dl.acm.org"]):
        return True
    return False

def clean_text(text: str) -> str:
    """
    Normalize unicode, strip HTML tags, collapse whitespace.

    Args:
        text: Raw text string.

    Returns:
        Cleaned plain text.
    """
    if not text:
        return ""

    text = unicodedata.normalize("NFKC", text)

    text = re.sub(r"<[^>]+>", " ", text)

    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)

    text = re.sub(r"\s+", " ", text).strip()
    return text

def clean_abstract_text(text: str) -> str:
    """Clean raw scraped paper abstracts by removing LaTeX noise, markdown tables, section headers, inline citations, and truncation markers."""
    if not text:
        return ""

    text = re.sub(r"#{1,6}\s*\d*(?:\.\d*)*\s*[^.\n]+(?=\n|\s)", "", text)

    text = re.sub(r"\|(?:\s*[-:]+\s*\|)+", " ", text)
    text = re.sub(r"\|[^|\n]+\|", " ", text)

    text = re.sub(r"\b[A-Z][a-zA-Z0-9\s\.\&\-]{1,40}\s+et\s+al\.\s*\(\d{4}\)", "", text)
    text = re.sub(r"\b[A-Z][a-zA-Z0-9\s\.\&\-]{1,40}\s*\(\d{4}\)", "", text)
    text = re.sub(r"\((?:[A-Z][a-zA-Z0-9\s\.\&\-]{1,30}(?:\s+et\s+al\.)?,?\s*)?\d{4}(?:;\s*(?:[A-Z][a-zA-Z0-9\s\.\&\-]{1,30}(?:\s+et\s+al\.)?,?\s*)?\d{4})*\)", "", text)

    text = re.sub(r"\\[a-zA-Z]+(?:\{[^}]*\})*", "", text)
    text = re.sub(r"[$_^{}\\]+", "", text)

    text = re.sub(r"[\u2200-\u22FF\u2A00-\u2AFF\u2100-\u214F]", "", text)
    text = re.sub(r"[𝒫𝒯ℛ∪∩∈∉⊂⊃⊆⊇ˆ˜¯⃗⋅×÷±=≠<>⩽⩾]", "", text)

    text = re.sub(r"\[\s*\.\.\.\s*\]", " ", text)
    text = re.sub(r"\.\.\.", " ", text)
    text = re.sub(r"\bABSTARCT\b|\bABSTRACT\b", "", text, flags=re.IGNORECASE)

    text = re.sub(r"\s+", " ", text).strip()
    return text

def generate_paper_id(url: str, title: str = "") -> str:
    """Generate a deterministic paper ID from URL + title."""
    raw = f"{url}::{title}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:24]

def slugify(text: str) -> str:
    """Convert text to a URL-safe slug."""
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^\w\s-]", "", text).strip().lower()
    return re.sub(r"[-\s]+", "-", text)

def extract_arxiv_id(url: str) -> Optional[str]:
    """Extract arXiv paper ID from a URL."""
    match = re.search(r"arxiv\.org/(?:abs|pdf|html)/(\d{4}\.\d{4,5}(?:v\d+)?)", url)
    return match.group(1) if match else None

def extract_doi(text: str) -> Optional[str]:
    """Extract DOI from text."""
    match = re.search(r"10\.\d{4,}/[^\s\"'<>]+", text)
    return match.group(0) if match else None

def chunk_text(text: str, chunk_size: int = 512, overlap: int = 64) -> List[str]:
    """
    Split text into overlapping semantic chunks.

    Args:
        text: Input text.
        chunk_size: Max characters per chunk.
        overlap: Overlap characters between chunks.

    Returns:
        List of text chunks.
    """
    if not text:
        return []

    sentences = re.split(r"(?<=[.!?])\s+", text)
    chunks: List[str] = []
    current = ""

    for sentence in sentences:
        if len(current) + len(sentence) + 1 <= chunk_size:
            current = f"{current} {sentence}".strip()
        else:
            if current:
                chunks.append(current)

            words = current.split()
            overlap_text = " ".join(words[-overlap:]) if len(words) > overlap else current
            current = f"{overlap_text} {sentence}".strip()

    if current:
        chunks.append(current)

    return [c for c in chunks if len(c.strip()) > 20]

def retry(max_attempts: int = 3, delay: float = 1.0, exceptions: tuple = (Exception,)):
    """Decorator for automatic retry with exponential backoff."""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as exc:
                    if attempt == max_attempts:
                        logger.error(
                            f"{func.__name__} failed after {max_attempts} attempts: {exc}"
                        )
                        raise
                    wait = delay * (2 ** (attempt - 1))
                    logger.warning(
                        f"{func.__name__} attempt {attempt} failed: {exc}. "
                        f"Retrying in {wait:.1f}s..."
                    )
                    time.sleep(wait)

        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as exc:
                    if attempt == max_attempts:
                        logger.error(
                            f"{func.__name__} failed after {max_attempts} attempts: {exc}"
                        )
                        raise
                    wait = delay * (2 ** (attempt - 1))
                    logger.warning(
                        f"{func.__name__} attempt {attempt} failed: {exc}. "
                        f"Retrying in {wait:.1f}s..."
                    )
                    time.sleep(wait)

        import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator

def truncate(text: str, max_len: int = 200, suffix: str = "...") -> str:
    """Truncate text to max_len characters."""
    if not text or len(text) <= max_len:
        return text
    return text[: max_len - len(suffix)] + suffix

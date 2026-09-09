"""
Node 6 — PDF Fetch
Downloads PDFs for papers that have a PDF URL available.
"""

import asyncio
from pathlib import Path
from typing import Any, Dict, List

import httpx

from backend.config import settings
from backend.langgraph.state import GraphState
from backend.utils.logger import logger

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

async def _download_pdf(paper: Dict[str, Any], pdf_dir: Path) -> Dict[str, Any]:
    """
    Download PDF for a single paper.

    Args:
        paper: Paper metadata dict.
        pdf_dir: Directory to save PDFs.

    Returns:
        Updated paper dict with pdf_local_path set if successful.
    """
    pdf_url = paper.get("pdf_url")
    paper_id = paper.get("paper_id", "unknown")

    if not pdf_url:
        return paper

    pdf_path = pdf_dir / f"{paper_id}.pdf"

    if pdf_path.exists() and pdf_path.stat().st_size > 1024:
        logger.info(f"[PDFFetch] Already exists: {pdf_path.name}")
        return {**paper, "pdf_local_path": str(pdf_path), "is_pdf_downloaded": True}

    try:
        async with httpx.AsyncClient(
            headers=HEADERS, timeout=30.0, follow_redirects=True
        ) as client:
            resp = await client.get(pdf_url)
            resp.raise_for_status()

            if not resp.content[:4] == b"%PDF":
                logger.warning(
                    f"[PDFFetch] {pdf_url} doesn't seem to be a PDF (magic bytes mismatch). Skipping."
                )
                return paper

            pdf_path.write_bytes(resp.content)
            logger.info(
                f"[PDFFetch] Downloaded: {pdf_path.name} "
                f"({len(resp.content) // 1024} KB)"
            )
            return {**paper, "pdf_local_path": str(pdf_path), "is_pdf_downloaded": True}

    except httpx.HTTPStatusError as exc:
        logger.warning(
            f"[PDFFetch] HTTP {exc.response.status_code} for {pdf_url}"
        )
    except Exception as exc:
        logger.warning(f"[PDFFetch] Failed to download {pdf_url}: {exc}")

    return paper

async def pdf_fetch_node(state: GraphState) -> GraphState:
    """
    LangGraph Node 6: Download PDFs concurrently.

    Input: papers
    Output: papers (updated with pdf_local_path and is_pdf_downloaded)
    """
    papers = state.get("papers", [])
    pdf_dir = Path(settings.PDF_STORAGE_PATH)
    pdf_dir.mkdir(parents=True, exist_ok=True)

    papers_with_pdf = [p for p in papers if p.get("pdf_url")]
    logger.info(
        f"[PDFFetch] Attempting to download {len(papers_with_pdf)}/{len(papers)} PDFs..."
    )

    semaphore = asyncio.Semaphore(3)

    async def bounded(paper):
        async with semaphore:
            return await _download_pdf(paper, pdf_dir)

    tasks = [bounded(p) for p in papers]
    updated_papers = await asyncio.gather(*tasks, return_exceptions=True)

    result_papers: List[Dict] = []
    for r in updated_papers:
        if isinstance(r, Exception):
            logger.error(f"[PDFFetch] Unexpected error: {r}")
        elif isinstance(r, dict):
            if r.get("pdf_url") or r.get("is_pdf_downloaded"):
                result_papers.append(r)

    if len(result_papers) < 3:
        result_papers = [r for r in updated_papers if isinstance(r, dict)]

    max_results = state.get("max_results", 10)
    result_papers = result_papers[:max_results]

    downloaded = len(result_papers)
    logger.info(f"[PDFFetch] Kept {downloaded} papers that have successfully downloaded PDFs (capped at {max_results}).")

    return {**state, "papers": result_papers}

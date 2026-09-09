import asyncio
import json
import re
from typing import Any, Dict, List, Optional

import httpx
from langchain_core.messages import HumanMessage

from backend.langgraph.state import GraphState
from backend.prompts.templates import METADATA_EXTRACTION_PROMPT
from backend.services.llm_service import get_llm
from backend.utils.helpers import (
    clean_text,
    clean_abstract_text,
    extract_arxiv_id,
    extract_doi,
    generate_paper_id,
)
from backend.utils.logger import logger

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

async def _fetch_page_text(url: str, timeout: float = 10.0) -> str:
    try:
        async with httpx.AsyncClient(
            headers=HEADERS, timeout=timeout, follow_redirects=True
        ) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            text = re.sub(r"<[^>]+>", " ", resp.text)
            text = clean_text(text)
            return text[:3000]
    except Exception as exc:
        logger.warning(f"[Metadata] Failed to fetch {url}: {exc}")
        return ""

async def _extract_metadata_llm(url: str, snippet: str, content: str) -> Dict[str, Any]:
    combined = snippet + "\n\n" + content
    try:
        llm = get_llm()
        prompt = METADATA_EXTRACTION_PROMPT.format(
            content=combined[:2500], url=url
        )
        response = await llm.ainvoke([HumanMessage(content=prompt)])
        raw = response.content.strip()

        if "```json" in raw:
            raw = raw.split("```json")[1].split("```")[0].strip()
        elif "```" in raw:
            raw = raw.split("```")[1].split("```")[0].strip()

        return json.loads(raw)
    except Exception as exc:
        logger.error(f"[Metadata] LLM extraction failed for {url}: {exc}")
        return {}

def _detect_pdf_url(url: str, metadata: Dict) -> Optional[str]:
    url_lower = url.lower()
    if url_lower.endswith(".pdf") or "/pdf/" in url_lower:
        return url

    arxiv_id = extract_arxiv_id(url)
    if arxiv_id:
        clean_id = re.sub(r"v\d+$", "", arxiv_id)
        return f"https://arxiv.org/pdf/{clean_id}.pdf"

    if "openreview.net" in url_lower:
        match = re.search(r"id=([a-zA-Z0-9_-]+)", url)
        if match:
            return f"https://openreview.net/pdf?id={match.group(1)}"

    if "ieeexplore.ieee.org" in url_lower:
        match = re.search(r"arnumber=(\d+)|document/(\d+)", url)
        if match:
            arnum = match.group(1) or match.group(2)
            return f"https://ieeexplore.ieee.org/stamp/stamp.jsp?tp=&arnumber={arnum}"

    if "springer.com" in url_lower:
        doi = extract_doi(url) or metadata.get("doi")
        if doi:
            return f"https://link.springer.com/content/pdf/{doi}.pdf"

    if "dl.acm.org" in url_lower:
        doi = extract_doi(url) or metadata.get("doi")
        if doi:
            return f"https://dl.acm.org/doi/pdf/{doi}"

    return metadata.get("pdf_url")

async def _process_single_result(result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    url = result.get("url", "")
    snippet = result.get("snippet", "")
    title_hint = result.get("title", "")

    content = await _fetch_page_text(url)

    meta = await _extract_metadata_llm(url, snippet, content)

    if not meta:
        meta = {}

    title = meta.get("title") or title_hint or url

    paper_id = generate_paper_id(url, title)

    pdf_url = _detect_pdf_url(url, meta) or meta.get("pdf_url")

    paper = {
        "paper_id": paper_id,
        "url": url,
        "title": title,
        "authors": meta.get("authors") or [],
        "year": meta.get("year"),
        "publisher": meta.get("publisher"),
        "conference": meta.get("conference"),
        "doi": meta.get("doi") or extract_doi(content),
        "abstract": clean_abstract_text(meta.get("abstract") or snippet),
        "keywords": meta.get("keywords") or [],
        "citation_count": meta.get("citation_count"),
        "license": meta.get("license"),
        "github_url": meta.get("github_url"),
        "dataset": meta.get("dataset"),
        "pdf_url": pdf_url,
        "thumbnail": meta.get("thumbnail"),
        "source": result.get("source", "unknown"),
        "similarity_score": result.get("score", 0.0),
        "is_pdf_downloaded": False,
    }

    return paper

async def metadata_extraction_node(state: GraphState) -> GraphState:
    filtered = state.get("filtered_results", [])
    max_results = state.get("max_results", 10)

    to_process = filtered[:max_results]

    logger.info(f"[Metadata] Extracting metadata for {len(to_process)} papers (max_results={max_results})...")

    semaphore = asyncio.Semaphore(3)

    async def bounded(result):
        async with semaphore:
            return await _process_single_result(result)

    tasks = [bounded(r) for r in to_process]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    papers: List[Dict[str, Any]] = []

    for r in results:
        if isinstance(r, Exception):
            logger.error(f"[Metadata] Processing error: {r}")
        elif r is not None:
            papers.append(r)

    logger.info(f"[Metadata] Successfully extracted {len(papers)} papers.")
    return {**state, "papers": papers}

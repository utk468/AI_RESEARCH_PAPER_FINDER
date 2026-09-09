"""
Node 8 (formerly 10) — Summarization
Generates grounded, structured summaries for each paper using parsed text + Groq.
No FAISS or embeddings — chunks the paper text directly and feeds to the LLM.
"""

import asyncio
import json
from typing import Any, Dict, List

from langchain_core.messages import HumanMessage

from backend.langgraph.state import GraphState
from backend.prompts.templates import SUMMARIZATION_PROMPT
from backend.services.llm_service import get_llm
from backend.utils.helpers import chunk_text, truncate
from backend.utils.logger import logger

def _get_best_chunks(paper: Dict[str, Any], max_chunks: int = 8) -> List[str]:
    """
    Extract the best text chunks from a parsed paper for summarization.
    Always feeds the official PDF paper abstract directly to the LLM first.
    """
    chunks: List[str] = []

    official_abstract = paper.get("abstract", "").strip()
    if official_abstract and len(official_abstract) > 30:
        chunks.append(f"OFFICIAL PAPER ABSTRACT:\n{official_abstract}")

    parsed = paper.get("parsed", {})

    sections = parsed.get("sections", {})
    priority_keys = ["introduction", "methodology", "method", "approach", "experiments", "results", "conclusion"]

    for key in priority_keys:
        text = sections.get(key, "").strip()
        if text and len(text) > 50:
            chunks.append(f"SECTION ({key.upper()}):\n{text[:1000]}")

    if len(chunks) > 1:
        return chunks[:max_chunks]

    full_text = parsed.get("text", "")
    if full_text:
        fallback_chunks = chunk_text(full_text, chunk_size=600, overlap=80)
        return (chunks + fallback_chunks)[:max_chunks]

    return chunks

async def _summarize_paper(paper: Dict[str, Any]) -> Dict[str, Any]:
    """Generate a structured Groq summary for a single paper."""
    paper_id = paper.get("paper_id", "")
    title = paper.get("title", "")
    authors = ", ".join(paper.get("authors", []))

    chunks = _get_best_chunks(paper)
    if not chunks:
        logger.warning(f"[Summarizer] No text available for paper: {paper_id}")
        return paper

    chunks_text = "\n\n---\n\n".join(chunks[:8])

    try:
        llm = get_llm()
        prompt = SUMMARIZATION_PROMPT.format(
            title=title,
            authors=authors,
            chunks=chunks_text,
        )
        response = await llm.ainvoke([HumanMessage(content=prompt)])
        content = response.content.strip()

        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        summary = json.loads(content)
        logger.info(f"[Summarizer] Summary generated for: {truncate(title, 60)}")

        try:
            from pathlib import Path
            from backend.config import settings
            summaries_dir = Path(settings.PDF_STORAGE_PATH).parent / "summaries"
            summaries_dir.mkdir(parents=True, exist_ok=True)
            summary_file = summaries_dir / f"{paper_id}.json"
            with open(summary_file, "w", encoding="utf-8") as f:
                json.dump(summary, f, indent=2, ensure_ascii=False)
            logger.info(f"[Summarizer] Saved summary file to {summary_file}")
        except Exception as e:
            logger.warning(f"[Summarizer] Failed to save summary file: {e}")

        from backend.utils.helpers import clean_abstract_text
        clean_abs = clean_abstract_text(summary.get("abstract") or paper.get("abstract", ""))
        return {**paper, "summary": summary, "abstract": clean_abs}

    except json.JSONDecodeError as exc:
        logger.error(f"[Summarizer] JSON parse error for {paper_id}: {exc}")
        return paper
    except Exception as exc:
        logger.error(f"[Summarizer] Error for {paper_id}: {exc}")
        return paper

async def summarization_node(state: GraphState) -> GraphState:
    """
    LangGraph Node 8: Generate Groq-powered grounded summaries for all papers.
    Uses parsed PDF text or abstract — no vector embeddings required.

    Input:  parsed_papers
    Output: parsed_papers (each entry updated with .summary dict)
    """
    parsed_papers = state.get("parsed_papers", [])
    logger.info(f"[Summarizer] Summarizing {len(parsed_papers)} papers with Groq...")

    semaphore = asyncio.Semaphore(2)

    async def bounded(paper: Dict) -> Dict:
        async with semaphore:
            return await _summarize_paper(paper)

    tasks = [bounded(p) for p in parsed_papers]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    summarized: List[Dict] = []
    for r in results:
        if isinstance(r, Exception):
            logger.error(f"[Summarizer] Task error: {r}")
        elif isinstance(r, dict):
            summarized.append(r)

    logger.info(f"[Summarizer] Done — {len(summarized)} papers summarized.")
    return {**state, "parsed_papers": summarized}

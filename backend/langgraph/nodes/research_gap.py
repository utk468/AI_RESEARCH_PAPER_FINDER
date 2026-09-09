"""
Node 11 — Research Gap Analysis
Analyzes all papers collectively to surface trends, gaps, and novel ideas.
"""

import json
from typing import Any, Dict, List

from langchain_core.messages import HumanMessage

from backend.langgraph.state import GraphState
from backend.prompts.templates import RESEARCH_GAP_PROMPT
from backend.services.llm_service import get_llm
from backend.utils.helpers import truncate
from backend.utils.logger import logger

async def research_gap_node(state: GraphState) -> GraphState:
    """
    LangGraph Node 11: Cross-paper research gap analysis.

    Input: parsed_papers
    Output: research_gaps
    """
    parsed_papers = state.get("parsed_papers", [])
    logger.info(
        f"[ResearchGap] Analyzing gaps across {len(parsed_papers)} papers..."
    )

    paper_summaries: List[str] = []

    for i, paper in enumerate(parsed_papers[:10], 1):
        summary_obj = paper.get("summary", {})
        abstract = paper.get("abstract", "")

        lines = [f"Paper {i}: {paper.get('title', 'Unknown Title')}"]
        lines.append(f"Authors: {', '.join(paper.get('authors', []))}")
        lines.append(f"Year: {paper.get('year', 'N/A')}")

        if summary_obj:
            lines.append(f"Summary: {summary_obj.get('summary_100_words', '')}")
            lines.append(f"Methodology: {summary_obj.get('methodology', '')}")
            lines.append(f"Results: {truncate(summary_obj.get('results', ''), 300)}")
        else:
            lines.append(f"Abstract: {truncate(abstract, 400)}")

        paper_summaries.append("\n".join(lines))

    papers_text = "\n\n" + "=" * 60 + "\n\n".join(paper_summaries)

    if not paper_summaries:
        logger.warning("[ResearchGap] No papers to analyze.")
        return {**state, "research_gaps": {}}

    try:
        llm = get_llm()
        prompt = RESEARCH_GAP_PROMPT.format(papers=papers_text)
        response = await llm.ainvoke([HumanMessage(content=prompt)])
        content = response.content.strip()

        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        gaps = json.loads(content)
        logger.info(
            f"[ResearchGap] Found {len(gaps.get('research_gaps', []))} gaps, "
            f"{len(gaps.get('current_trends', []))} trends."
        )
        return {**state, "research_gaps": gaps}

    except json.JSONDecodeError as exc:
        logger.error(f"[ResearchGap] JSON parse error: {exc}")
        return {**state, "research_gaps": {"error": "Failed to parse research gaps."}}
    except Exception as exc:
        logger.error(f"[ResearchGap] Unexpected error: {exc}")
        errors = state.get("errors", [])
        return {**state, "research_gaps": {}, "errors": errors + [f"research_gap: {exc}"]}

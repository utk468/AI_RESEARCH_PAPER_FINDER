"""
Node 12 — Recommendation
Generates recommendations for related papers, datasets, authors, and conferences.
"""

import json
from typing import Any, Dict

from langchain_core.messages import HumanMessage

from backend.langgraph.state import GraphState
from backend.prompts.templates import RECOMMENDATION_PROMPT
from backend.services.llm_service import get_llm
from backend.utils.helpers import truncate
from backend.utils.logger import logger

async def recommendation_node(state: GraphState) -> GraphState:
    """
    LangGraph Node 12: Generate personalized academic recommendations.

    Input: parsed_papers, understanding
    Output: recommendations
    """
    parsed_papers = state.get("parsed_papers", [])
    understanding = state.get("understanding", {})
    research_topic = understanding.get("research_topic", state.get("query", ""))

    logger.info(f"[Recommendation] Generating recommendations for: {research_topic!r}")

    paper_lines = []
    for i, paper in enumerate(parsed_papers[:8], 1):
        summary_obj = paper.get("summary", {})
        line_parts = [
            f"Paper {i}: {paper.get('title', 'Unknown')}",
            f"  Authors: {', '.join(paper.get('authors', [])[:3])}",
            f"  Year: {paper.get('year', 'N/A')}",
            f"  Conference: {paper.get('conference', 'N/A')}",
            f"  Keywords: {', '.join(paper.get('keywords', [])[:5])}",
        ]
        if summary_obj:
            line_parts.append(
                f"  Applications: {', '.join(summary_obj.get('applications', []))}"
            )
        paper_lines.append("\n".join(line_parts))

    papers_text = "\n\n".join(paper_lines)

    if not papers_text.strip():
        logger.warning("[Recommendation] No papers available for recommendations.")
        return {**state, "recommendations": {}}

    try:
        llm = get_llm()
        prompt = RECOMMENDATION_PROMPT.format(
            papers=papers_text, research_topic=research_topic
        )
        response = await llm.ainvoke([HumanMessage(content=prompt)])
        content = response.content.strip()

        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        recs = json.loads(content)
        logger.info(
            f"[Recommendation] Generated recommendations: "
            f"{len(recs.get('related_papers', []))} related papers, "
            f"{len(recs.get('recommended_conferences', []))} conferences."
        )
        return {**state, "recommendations": recs}

    except json.JSONDecodeError as exc:
        logger.error(f"[Recommendation] JSON parse error: {exc}")
        return {**state, "recommendations": {}}
    except Exception as exc:
        logger.error(f"[Recommendation] Error: {exc}")
        errors = state.get("errors", [])
        return {**state, "recommendations": {}, "errors": errors + [f"recommendation: {exc}"]}

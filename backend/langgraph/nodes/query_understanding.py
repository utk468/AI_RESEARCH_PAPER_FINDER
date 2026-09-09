"""
Node 1 — Query Understanding
Parseing  the natural language research query into structured research intent.
"""

import json
from typing import Any, Dict

from langchain_core.messages import HumanMessage, SystemMessage

from backend.langgraph.state import GraphState
from backend.prompts.templates import QUERY_UNDERSTANDING_PROMPT
from backend.services.llm_service import get_llm
from backend.utils.logger import logger

async def query_understanding_node(state: GraphState) -> GraphState:
    """
    LangGraph node that understands the research query.

    Input state fields: query
    Output state fields: understanding
    """
    query = state.get("query", "")
    logger.info(f"[QueryUnderstanding] Processing: {query!r}")

    try:
        llm = get_llm()

        prompt = QUERY_UNDERSTANDING_PROMPT.format(query=query)

        response = await llm.ainvoke([HumanMessage(content=prompt)])

        content = response.content.strip()

        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        understanding: Dict[str, Any] = json.loads(content)

        logger.info(
            f"[QueryUnderstanding] Topic: {understanding.get('research_topic')}, "
            f"Keywords: {understanding.get('keywords')}"
        )

        return {**state, "understanding": understanding}

    except json.JSONDecodeError as exc:
        logger.error(f"[QueryUnderstanding] JSON parse error: {exc}")

        fallback = {
            "research_topic": query,
            "subtopics": [],
            "keywords": query.split()[:5],
            "publication_year_range": {"from": 2020, "to": 2025},
            "conferences": [],
            "paper_type": "empirical",
            "search_intent": "find latest",
            "domain": "computer science",
        }
        return {**state, "understanding": fallback}

    except Exception as exc:
        logger.error(f"[QueryUnderstanding] Unexpected error: {exc}")
        errors = state.get("errors", [])
        return {**state, "errors": errors + [f"query_understanding: {exc}"]}

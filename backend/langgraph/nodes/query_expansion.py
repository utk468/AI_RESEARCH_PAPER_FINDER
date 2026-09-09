import json
from typing import Any, Dict, List

from langchain_core.messages import HumanMessage

from backend.langgraph.state import GraphState
from backend.prompts.templates import QUERY_EXPANSION_PROMPT
from backend.services.llm_service import get_llm
from backend.utils.logger import logger

async def query_expansion_node(state: GraphState) -> GraphState:
    """
    LangGraph node that expands the research query.

    Input state fields: understanding
    Output state fields: expansion, search_queries
    """
    understanding = state.get("understanding", {})

    research_topic = understanding.get("research_topic", state.get("query", ""))
    keywords = understanding.get("keywords", [])
    subtopics = understanding.get("subtopics", [])

    logger.info(f"[QueryExpansion] Expanding topic: {research_topic!r}")

    try:
        llm = get_llm()

        prompt = QUERY_EXPANSION_PROMPT.format(
            research_topic=research_topic,
            keywords=", ".join(keywords),
            subtopics=", ".join(subtopics),
        )

        response = await llm.ainvoke([HumanMessage(content=prompt)])

        content = response.content.strip()

        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        expansion: Dict[str, Any] = json.loads(content)

        search_queries: List[str] = []
        search_queries.append(research_topic)
        search_queries.extend(keywords[:3])
        search_queries.extend(expansion.get("expanded_topics", [])[:3])
        search_queries.extend(expansion.get("boolean_queries", [])[:2])

        seen: set = set()
        unique_queries: List[str] = []

        for q in search_queries:
            if q.lower() not in seen:
                seen.add(q.lower())
                unique_queries.append(q)

        logger.info(f"[QueryExpansion] Generated {len(unique_queries)} search queries.")
        return {**state, "expansion": expansion, "search_queries": unique_queries}

    except json.JSONDecodeError as exc:
        logger.error(f"[QueryExpansion] JSON parse error: {exc}")

        fallback_queries = [research_topic] + keywords[:4]
        return {
            **state,
            "expansion": {"expanded_topics": keywords},
            "search_queries": fallback_queries,
        }

    except Exception as exc:
        logger.error(f"[QueryExpansion] Error: {exc}")
        errors = state.get("errors", [])
        return {
            **state,
            "search_queries": [research_topic],
            "errors": errors + [f"query_expansion: {exc}"],
        }

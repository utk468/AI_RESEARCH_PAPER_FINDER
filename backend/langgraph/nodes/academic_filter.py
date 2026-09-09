"""
Node 4 — Academic Filter
Keeps only results from trusted academic domains.
"""

from typing import Any, Dict, List

from backend.langgraph.state import GraphState
from backend.utils.helpers import ACADEMIC_DOMAINS, is_academic_url, is_likely_pdf
from backend.utils.logger import logger

async def academic_filter_node(state: GraphState) -> GraphState:
    """
    LangGraph Node 4: Filter raw results to trusted academic sources only.

    Input: raw_results
    Output: filtered_results
    """
    raw_results = state.get("raw_results", [])
    logger.info(f"[AcademicFilter] Filtering {len(raw_results)} results...")

    filtered: List[Dict[str, Any]] = []

    for result in raw_results:
        url = result.get("url", "")
        if is_academic_url(url):
            filtered.append(result)
        else:
            logger.debug(f"[AcademicFilter] Rejected non-academic URL: {url}")

    filtered.sort(
        key=lambda r: (is_likely_pdf(r.get("url", "")), r.get("score", 0.0)),
        reverse=True
    )

    logger.info(
        f"[AcademicFilter] {len(filtered)} academic results "
        f"(removed {len(raw_results) - len(filtered)})."
    )

    if not filtered and raw_results:
        logger.warning(
            "[AcademicFilter] No academic URLs found. Using all results as fallback."
        )
        filtered = raw_results

    return {**state, "filtered_results": filtered}

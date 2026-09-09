"""
Node 3 — Web Search
Searches multiple search engines and deduplicates results.
"""

import asyncio
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from backend.config import settings
from backend.langgraph.state import GraphState
from backend.utils.logger import logger

async def _search_tavily(query: str, max_results: int) -> List[Dict]:
    """Search using Tavily API."""
    try:

        from tavily import AsyncTavilyClient

        client = AsyncTavilyClient(api_key=settings.TAVILY_API_KEY)

        try:
            response = await client.search(
                query=query,
                max_results=max(15, max_results),
                search_depth="advanced",
                include_domains=[
                    "arxiv.org",
                    "ieeexplore.ieee.org",
                    "dl.acm.org",
                    "springer.com",
                    "link.springer.com",
                    "semanticscholar.org",
                    "openreview.net"
                ],
            )
            results = response.get("results", [])
        except Exception:
            results = []

        if not results:

            response = await client.search(
                query=query,
                max_results=max(15, max_results),
                search_depth="advanced",
            )
            results = response.get("results", [])
        return [
            {
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "snippet": r.get("content", ""),
                "score": r.get("score", 0.0),
                "source": "tavily",
            }
            for r in response.get("results", [])
        ]

    except Exception as exc:
        logger.error(f"[WebSearch] Tavily error: {exc}")
        return []

SEARCH_PROVIDERS = {
    "tavily": _search_tavily
}

async def web_search_node(state: GraphState) -> GraphState:
    """
    LangGraph Node 3: Searches multiple engines and deduplicates by URL.

    Input: search_queries
    Output: raw_results
    """
    search_queries = state.get("search_queries", [])
    max_results = state.get("max_results", 10)

    provider_name = settings.SEARCH_PROVIDER.lower()

    logger.info(
        f"[WebSearch] Provider: {provider_name}, Queries: {len(search_queries)}"
    )

    search_fn = SEARCH_PROVIDERS.get(provider_name, _search_tavily)

    tasks = [
        search_fn(q, max(5, max_results // 2))
        for q in search_queries[:3]
    ]

    results_nested = await asyncio.gather(*tasks, return_exceptions=True)

    all_results: List[Dict] = []
    seen_urls: set = set()

    for batch in results_nested:
        if isinstance(batch, Exception):
            logger.error(f"[WebSearch] Search task failed: {batch}")
            continue
        for result in batch:
            url = result.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                all_results.append(result)

    logger.info(f"[WebSearch] Found {len(all_results)} unique results.")
    return {**state, "raw_results": all_results}

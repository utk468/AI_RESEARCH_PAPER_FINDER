"""
Search service — orchestrates the LangGraph pipeline and formats the response.
"""

from typing import Any, Dict, List, Optional

from backend.database.mongodb import mongodb
from backend.langgraph.graph import run_pipeline
from backend.schemas.responses import PaperCardResponse, SearchResponse
from backend.utils.logger import logger

class SearchService:
    """
    Business logic layer for the search API endpoint.
    Delegates to LangGraph pipeline and formats results.
    """

    async def run_search(
        self,
        query: str,
        max_results: int = 10,
        year_from: Optional[int] = None,
        year_to: Optional[int] = None,
        force_refresh: bool = False,
    ) -> SearchResponse:
        """
        Run the full research pipeline and return structured results.

        Args:
            query: Natural language research query.
            max_results: Max papers to retrieve.
            year_from: Optional year filter start.
            year_to: Optional year filter end.
            force_refresh: Skip cache and re-run pipeline.

        Returns:
            SearchResponse with papers, gaps, and recommendations.
        """

        if not force_refresh:
            cached = await self._check_cache(query)
            if cached:
                logger.info(f"[SearchService] Cache hit for: {query!r}")
                return cached

        state = await run_pipeline(
            query=query,
            max_results=max_results,
            year_from=year_from,
            year_to=year_to,
        )

        papers = state.get("papers", [])
        parsed_papers = state.get("parsed_papers", [])
        summary_map = {p["paper_id"]: p.get("summary") for p in parsed_papers}

        paper_cards: List[PaperCardResponse] = []
        for paper in papers:
            pid = paper.get("paper_id", "")
            paper_card = PaperCardResponse(
                paper_id=pid,
                title=paper.get("title", ""),
                authors=paper.get("authors", []),
                year=paper.get("year"),
                publisher=paper.get("publisher"),
                conference=paper.get("conference"),
                doi=paper.get("doi"),
                abstract=paper.get("abstract"),
                keywords=paper.get("keywords", []),
                citation_count=paper.get("citation_count"),
                github_url=paper.get("github_url"),
                dataset=paper.get("dataset"),
                pdf_url=paper.get("pdf_url"),
                thumbnail=paper.get("thumbnail"),
                url=paper.get("url", ""),
                source=paper.get("source"),
                similarity_score=paper.get("similarity_score"),
                is_pdf_downloaded=paper.get("is_pdf_downloaded", False),
                summary=summary_map.get(pid),
            )
            paper_cards.append(paper_card)

        paper_cards = paper_cards[:max_results]

        return SearchResponse(
            search_id=state.get("search_id", ""),
            query=query,
            understanding=state.get("understanding"),
            expansion=state.get("expansion"),
            papers=paper_cards,
            total_results=len(paper_cards),
            research_gaps=state.get("research_gaps"),
            recommendations=state.get("recommendations"),
            processing_time_seconds=state.get("processing_time", 0.0),
        )

    async def _check_cache(self, query: str) -> Optional[SearchResponse]:
        """Look for a recent cached search result."""
        try:
            from datetime import datetime, timedelta
            cutoff = datetime.utcnow() - timedelta(hours=1)
            doc = await mongodb.search_history.find_one(
                {"query": query, "created_at": {"$gte": cutoff}},
                sort=[("created_at", -1)],
            )
            if not doc:
                return None

            paper_ids = doc.get("paper_ids", [])
            papers_cursor = mongodb.papers.find({"paper_id": {"$in": paper_ids}})
            papers = await papers_cursor.to_list(length=100)

            paper_cards = [
                PaperCardResponse(
                    paper_id=p.get("paper_id", ""),
                    title=p.get("title", ""),
                    authors=p.get("authors", []),
                    year=p.get("year"),
                    publisher=p.get("publisher"),
                    conference=p.get("conference"),
                    doi=p.get("doi"),
                    abstract=p.get("abstract"),
                    keywords=p.get("keywords", []),
                    citation_count=p.get("citation_count"),
                    github_url=p.get("github_url"),
                    dataset=p.get("dataset"),
                    pdf_url=p.get("pdf_url"),
                    thumbnail=p.get("thumbnail"),
                    url=p.get("url", ""),
                    source=p.get("source"),
                    similarity_score=p.get("similarity_score"),
                    is_pdf_downloaded=p.get("is_pdf_downloaded", False),
                    summary=p.get("summary"),
                )
                for p in papers
            ]

            return SearchResponse(
                search_id=str(doc.get("search_id", "")),
                query=query,
                understanding=doc.get("understanding"),
                expansion=doc.get("expansion"),
                papers=paper_cards,
                total_results=len(paper_cards),
                research_gaps=doc.get("research_gaps"),
                recommendations=doc.get("recommendations"),
                processing_time_seconds=0.0,
            )
        except Exception as exc:
            logger.error(f"[SearchService] Cache lookup error: {exc}")
            return None

    async def get_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Retrieve recent search history."""
        cursor = mongodb.search_history.find(
            {}, {"query": 1, "search_id": 1, "total_results": 1, "created_at": 1}
        ).sort("created_at", -1).limit(limit)
        return await cursor.to_list(length=limit)

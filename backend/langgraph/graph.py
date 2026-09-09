"""
LangGraph main graph — 10-node pipeline (embedding & retrieval removed).

Pipeline:
  query_understanding → query_expansion → web_search →
  academic_filter → metadata_extraction → pdf_fetch →
  pdf_parser → summarization → research_gap → recommendation → END
"""

import time
import uuid
from typing import Any, Dict

from langgraph.graph import StateGraph, END

from backend.langgraph.state import GraphState
from backend.langgraph.nodes.query_understanding import query_understanding_node
from backend.langgraph.nodes.query_expansion import query_expansion_node
from backend.langgraph.nodes.web_search import web_search_node
from backend.langgraph.nodes.academic_filter import academic_filter_node
from backend.langgraph.nodes.metadata import metadata_extraction_node
from backend.langgraph.nodes.pdf_fetch import pdf_fetch_node
from backend.langgraph.nodes.pdf_parser import pdf_parser_node
from backend.langgraph.nodes.summarizer import summarization_node
from backend.langgraph.nodes.research_gap import research_gap_node
from backend.langgraph.nodes.recommendation import recommendation_node
from backend.database.mongodb import mongodb
from backend.utils.logger import logger

def build_graph() -> StateGraph:
    """
    Build and compile the LangGraph StateGraph (10 nodes, no embedding/retrieval).

    Returns:
        Compiled LangGraph app.
    """
    graph = StateGraph(GraphState)

    graph.add_node("query_understanding",  query_understanding_node)
    graph.add_node("query_expansion",      query_expansion_node)
    graph.add_node("web_search",           web_search_node)
    graph.add_node("academic_filter",      academic_filter_node)
    graph.add_node("metadata_extraction",  metadata_extraction_node)
    graph.add_node("pdf_fetch",            pdf_fetch_node)
    graph.add_node("pdf_parser",           pdf_parser_node)
    graph.add_node("summarization",        summarization_node)
    graph.add_node("research_gap",         research_gap_node)
    graph.add_node("recommendation",       recommendation_node)

    graph.set_entry_point("query_understanding")
    graph.add_edge("query_understanding", "query_expansion")
    graph.add_edge("query_expansion",     "web_search")
    graph.add_edge("web_search",          "academic_filter")
    graph.add_edge("academic_filter",     "metadata_extraction")
    graph.add_edge("metadata_extraction", "pdf_fetch")
    graph.add_edge("pdf_fetch",           "pdf_parser")
    graph.add_edge("pdf_parser",          "summarization")
    graph.add_edge("summarization",       "research_gap")
    graph.add_edge("research_gap",        "recommendation")
    graph.add_edge("recommendation",      END)

    return graph.compile()

_compiled_graph = None

def get_compiled_graph():
    """Return the singleton compiled LangGraph (lazy init)."""
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = build_graph()
        logger.info("[Graph] LangGraph 10-node pipeline compiled successfully.")
    return _compiled_graph

async def run_pipeline(
    query: str,
    max_results: int = 10,
    year_from: int = None,
    year_to: int = None,
) -> Dict[str, Any]:
    """
    Execute the full LangGraph research pipeline.

    Args:
        query:       Natural language research query.
        max_results: Maximum number of papers to process.
        year_from:   Filter papers from this year.
        year_to:     Filter papers up to this year.

    Returns:
        Final pipeline state as a dict.
    """
    search_id = str(uuid.uuid4())
    start_time = time.time()

    initial_state: GraphState = {
        "query": query,
        "max_results": max_results,
        "year_from": year_from,
        "year_to": year_to,
        "search_id": search_id,
        "errors": [],
    }

    logger.info(f"[Graph] Starting pipeline. search_id={search_id}, query={query!r}")

    graph = get_compiled_graph()
    final_state = await graph.ainvoke(initial_state)

    elapsed = time.time() - start_time
    final_state["processing_time"] = elapsed

    logger.info(
        f"[Graph] Pipeline completed in {elapsed:.2f}s. "
        f"Papers: {len(final_state.get('papers', []))}. "
        f"Errors: {len(final_state.get('errors', []))}"
    )

    try:
        papers = final_state.get("papers", [])
        parsed_papers = final_state.get("parsed_papers", [])

        parsed_map = {
            p["paper_id"]: p.get("parsed")
            for p in parsed_papers
            if p.get("paper_id")
        }
        summary_map = {
            p["paper_id"]: p.get("summary")
            for p in parsed_papers
            if p.get("paper_id")
        }
        paper_ids = []

        for paper in papers:
            pid = paper.get("paper_id", "")
            if pid:
                paper["summary"] = summary_map.get(pid)
                parsed_data = parsed_map.get(pid)
                if parsed_data:
                    paper["parsed_text"] = parsed_data.get("text", "")
                    paper["sections"] = parsed_data.get("sections", {})

                    paper["references"] = parsed_data.get("references", [])
                    paper["page_count"] = parsed_data.get("page_count", 0)
                paper_ids.append(pid)
                await mongodb.papers.update_one(
                    {"paper_id": pid},
                    {"$set": paper},
                    upsert=True,
                )

        await mongodb.search_history.insert_one({
            "search_id": search_id,
            "query": query,
            "understanding": final_state.get("understanding"),
            "expansion": final_state.get("expansion"),
            "paper_ids": paper_ids,
            "total_results": len(paper_ids),
            "research_gaps": final_state.get("research_gaps"),
            "recommendations": final_state.get("recommendations"),
            "processing_time": elapsed,
        })

        logger.info(f"[Graph] Saved {len(paper_ids)} papers to MongoDB.")
    except Exception as exc:
        logger.error(f"[Graph] MongoDB persistence error: {exc}")

    return final_state

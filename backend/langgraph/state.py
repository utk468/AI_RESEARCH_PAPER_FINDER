from typing import Any, Dict, List, Optional, TypedDict

class GraphState(TypedDict, total=False):

    query: str
    max_results: int
    year_from: Optional[int]
    year_to: Optional[int]

    understanding: Dict[str, Any]

    expansion: Dict[str, Any]
    search_queries: List[str]

    raw_results: List[Dict[str, Any]]

    filtered_results: List[Dict[str, Any]]

    papers: List[Dict[str, Any]]

    parsed_papers: List[Dict[str, Any]]

    research_gaps: Dict[str, Any]

    recommendations: Dict[str, Any]

    search_id: str
    errors: List[str]
    processing_time: float

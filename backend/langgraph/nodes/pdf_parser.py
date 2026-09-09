"""
Node 7 — PDF Processing
Parses downloaded PDFs using PyMuPDF and splits into semantic chunks.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

import re
from backend.config import settings
from backend.langgraph.state import GraphState
from backend.utils.helpers import chunk_text, clean_text, clean_abstract_text
from backend.utils.logger import logger

try:

    import fitz
    FITZ_AVAILABLE = True
except ImportError:
    FITZ_AVAILABLE = False
    logger.warning("PyMuPDF (fitz) not installed. PDF parsing will be limited.")

def _extract_sections(text: str) -> Dict[str, str]:
    """
    Heuristically extract common paper sections from raw text.

    Returns:
        Dict mapping section name → section text.
    """
    section_headers = [
        "abstract", "introduction", "related work", "methodology", "method",
        "approach", "experiments", "results", "discussion", "conclusion",
        "future work", "limitations", "references",
    ]
    sections: Dict[str, str] = {}

    lower_text = text.lower()

    for i, header in enumerate(section_headers):
        start = lower_text.find(header)
        if start == -1:
            continue

        next_start = len(text)
        for other in section_headers[i + 1:]:
            pos = lower_text.find(other, start + len(header))
            if pos != -1:
                next_start = min(next_start, pos)
        sections[header] = clean_text(text[start:next_start])

    return sections

def _extract_page1_abstract(doc: Any) -> str:
    """Extract official author abstract directly from Page 1 of the PDF."""
    try:
        if len(doc) == 0:
            return ""
        page1_text = doc[0].get_text("text")
        if not page1_text:
            return ""

        match = re.search(
            r"(?:Abstract|ABSTRACT)\s*[\:\-\—\.\n]?\s*(.*?)(?=\n\s*(?:1\.?|I\.?|Introduction|INTRODUCTION|Keywords|KEYWORDS|1\s+Introduction|\n\n\n))",
            page1_text,
            re.DOTALL
        )
        if match:
            abs_text = match.group(1).strip()
            if len(abs_text) > 40:
                return clean_abstract_text(abs_text)

        match_fallback = re.search(r"(?:Abstract|ABSTRACT)\s*[\:\-\—\.\n]?\s*(.{100,1500})", page1_text, re.DOTALL)
        if match_fallback:
            return clean_abstract_text(match_fallback.group(1)[:1200])
    except Exception as exc:
        logger.warning(f"[PDFParser] Page 1 abstract extraction warning: {exc}")
    return ""

def _parse_pdf(local_path: str) -> Optional[Dict[str, Any]]:
    """
    Parse a PDF file and return structured content.

    Args:
        local_path: Absolute path to the PDF file.

    Returns:
        Dict with text, sections, references, chunks.
    """
    if not FITZ_AVAILABLE:
        return None

    path = Path(local_path)

    if not path.exists():
        logger.warning(f"[PDFParser] File not found: {local_path}")
        return None

    try:
        doc = fitz.open(local_path)
        full_text = ""

        for page_num, page in enumerate(doc):

            page_text = page.get_text("text")
            full_text += f"\n--- Page {page_num + 1} ---\n{page_text}"

        page_count = len(doc) if hasattr(doc, "__len__") else 0
        official_abstract = _extract_page1_abstract(doc)
        doc.close()

        clean = clean_text(full_text)
        sections = _extract_sections(clean)

        references_text = sections.get("references", "")
        references = [
            line.strip()
            for line in references_text.split("\n")
            if line.strip() and len(line.strip()) > 20
        ][:50]

        chunks = chunk_text(clean, chunk_size=settings.CHUNK_SIZE, overlap=settings.CHUNK_OVERLAP)

        return {
            "text": clean,
            "sections": sections,
            "references": references,
            "chunks": chunks,
            "page_count": page_count,
            "official_abstract": official_abstract,
        }

    except Exception as exc:
        logger.error(f"[PDFParser] Failed to parse {local_path}: {exc}")
        return None

async def pdf_parser_node(state: GraphState) -> GraphState:
    """
    LangGraph Node 7: Parse downloaded PDFs into text, sections, and chunks.

    Input: papers (with pdf_local_path)
    Output: parsed_papers
    """
    papers = state.get("papers", [])
    parsed_papers: List[Dict[str, Any]] = []

    for paper in papers:

        local_path = paper.get("pdf_local_path")

        parsed: Optional[Dict] = None

        if local_path and FITZ_AVAILABLE:
            logger.info(f"[PDFParser] Parsing: {Path(local_path).name}")
            parsed = _parse_pdf(local_path)

        if parsed is None:

            abstract = paper.get("abstract", "")
            chunks = chunk_text(abstract) if abstract else []
            parsed = {
                "text": abstract,
                "references": [],
                "chunks": chunks,
                "page_count": 0,
                "official_abstract": "",
            }

        updated_paper = {**paper, "parsed": parsed}
        if parsed and parsed.get("official_abstract"):
            updated_paper["abstract"] = parsed["official_abstract"]
            logger.info(f"[PDFParser] Extracted official Page 1 PDF abstract for: {paper.get('title', '')[:40]}")

        parsed_papers.append(updated_paper)

    logger.info(f"[PDFParser] Parsed {len(parsed_papers)} papers.")
    return {**state, "parsed_papers": parsed_papers}

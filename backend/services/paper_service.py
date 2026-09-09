"""
Paper service — CRUD, per-paper summary generation, and RAG chat.
All retrieval is done via MongoDB text (no FAISS / no embeddings).
LLM provider: Groq only.
"""

from typing import Any, Dict, List, Optional

from langchain_core.messages import HumanMessage

from backend.database.mongodb import mongodb
from backend.prompts.templates import RAG_CHAT_PROMPT
from backend.services.llm_service import get_llm
from backend.utils.helpers import chunk_text, truncate
from backend.utils.logger import logger

class PaperService:
    """Business logic for paper retrieval, on-demand summary, and RAG chat."""

    async def get_paper(self, paper_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a paper document from MongoDB by paper_id."""
        doc = await mongodb.papers.find_one(
            {"paper_id": paper_id}, {"_id": 0}
        )
        if doc:
            pass
        return doc

    async def get_related_papers(
        self, paper_id: str, limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Find related papers using MongoDB full-text search on keywords + title.
        Falls back to most-recent papers in same conference if no text index hit.
        """
        paper = await self.get_paper(paper_id)
        if not paper:
            return []

        title = paper.get("title", "")
        keywords = paper.get("keywords", [])
        search_terms = " ".join([title] + keywords[:5])

        try:

            cursor = mongodb.papers.find(
                {
                    "$text": {"$search": search_terms},
                    "paper_id": {"$ne": paper_id},
                },
                {"score": {"$meta": "textScore"}, "_id": 0},
            ).sort([("score", {"$meta": "textScore"})]).limit(limit)
            results = await cursor.to_list(length=limit)
        except Exception:
            results = []

        if not results:
            conference = paper.get("conference")
            query = {"paper_id": {"$ne": paper_id}}
            if conference:
                query["conference"] = conference
            cursor = mongodb.papers.find(query, {"_id": 0}).sort("year", -1).limit(limit)
            results = await cursor.to_list(length=limit)

        return results

    async def prepare_paper_rag(self, paper_id: str) -> Dict[str, Any]:
        """
        Check if the paper's FAISS index exists.
        If not, load the paper, extract its chunks, build the index, and save it.
        """
        from backend.rag.vector_store import PaperVectorStore
        from backend.utils.helpers import chunk_text

        store = PaperVectorStore(paper_id)
        if store.exists():
            store.load()
            return {
                "paper_id": paper_id,
                "status": "ready",
                "chunks_count": len(store.chunks),
                "message": "Paper index already prepared and loaded."
            }

        paper = await self.get_paper(paper_id)
        if not paper:
            return {
                "paper_id": paper_id,
                "status": "error",
                "chunks_count": 0,
                "message": "Paper not found in database."
            }

        chunks = []
        parsed_text = paper.get("parsed_text", "")
        if parsed_text:
            chunks = chunk_text(parsed_text, chunk_size=500, overlap=60)
        else:
            abstract = paper.get("abstract", "")
            if abstract:
                chunks = chunk_text(abstract, chunk_size=500, overlap=60)

        if not chunks:
            title = paper.get("title", "")
            abstract = paper.get("abstract", "")
            fallback_text = f"Title: {title}\nAbstract: {abstract}"
            chunks = chunk_text(fallback_text, chunk_size=500, overlap=60)

        success = store.build_and_save(chunks)
        if success:
            return {
                "paper_id": paper_id,
                "status": "ready",
                "chunks_count": len(chunks),
                "message": "Paper index successfully prepared and saved."
            }
        else:
            return {
                "paper_id": paper_id,
                "status": "error",
                "chunks_count": 0,
                "message": "Failed to build or save FAISS index for this paper."
            }

    async def chat_with_paper(
        self,
        paper_id: str,
        question: str,
        top_k: int = 5,
    ) -> Dict[str, Any]:
        """
        Answer a user question about a paper using Groq, grounded on retrieved chunks.

        Args:
            paper_id: Target paper.
            question: User's natural-language question.
            top_k:    Max context passages to include.

        Returns:
            Dict with 'answer' and 'chunks_used'.
        """
        paper = await self.get_paper(paper_id)
        if not paper:
            return {"answer": "Paper not found.", "chunks_used": []}

        title = paper.get("title", "")

        from backend.rag.vector_store import PaperVectorStore
        store = PaperVectorStore(paper_id)

        if not store.exists():
            prep_res = await self.prepare_paper_rag(paper_id)
            if prep_res.get("status") == "error":
                return {
                    "answer": f"Could not prepare RAG context: {prep_res.get('message')}",
                    "chunks_used": []
                }

        if not store.load():
            return {
                "answer": "Failed to load paper index for retrieval.",
                "chunks_used": []
            }

        used_passages = store.search(question, top_k=top_k)

        if not used_passages:

            abstract = paper.get("abstract", "")
            if abstract:
                used_passages = [abstract]

        if not used_passages:
            return {
                "answer": "No content is available for this paper yet.",
                "chunks_used": [],
            }

        context = "\n\n---\n\n".join(used_passages)

        try:
            llm = get_llm()
            prompt = RAG_CHAT_PROMPT.format(
                title=title,
                chunks=context,
                question=question,
            )
            response = await llm.ainvoke([HumanMessage(content=prompt)])
            answer = response.content.strip()

            await mongodb.chat_history.insert_one({
                "paper_id": paper_id,
                "question": question,
                "answer": answer,
                "chunks_used": used_passages,
            })

            return {"answer": answer, "chunks_used": used_passages}

        except Exception as exc:
            logger.error(f"[PaperService] Chat error: {exc}")
            return {
                "answer": f"Could not generate an answer: {exc}",
                "chunks_used": [],
            }

    async def generate_summary(
        self,
        paper_id: str,
        regenerate: bool = False,
    ) -> Optional[Dict[str, Any]]:
        """
        Return existing summary or generate one on-demand via Groq.
        Triggers on-demand PDF download and parsing if not already done.

        Args:
            paper_id:   Target paper.
            regenerate: Force a fresh Groq call even if summary exists.
        """
        paper = await self.get_paper(paper_id)
        if not paper:
            return None

        if paper.get("summary") and not regenerate:
            return paper["summary"]

        from pathlib import Path
        from backend.config import settings
        from backend.langgraph.nodes.pdf_fetch import _download_pdf
        from backend.langgraph.nodes.pdf_parser import _parse_pdf
        from backend.langgraph.nodes.summarizer import _summarize_paper

        parsed = None
        if paper.get("parsed_text"):
            parsed = {
                "text": paper.get("parsed_text"),
                "sections": paper.get("sections", {}),

                "references": paper.get("references", []),
                "page_count": paper.get("page_count", 0),
            }
        else:
            pdf_local_path = paper.get("pdf_local_path")

            if not pdf_local_path and paper.get("pdf_url"):
                pdf_dir = Path(settings.PDF_STORAGE_PATH)
                pdf_dir.mkdir(parents=True, exist_ok=True)
                paper = await _download_pdf(paper, pdf_dir)
                pdf_local_path = paper.get("pdf_local_path")

            if pdf_local_path and Path(pdf_local_path).exists():
                parsed = _parse_pdf(pdf_local_path)
                if parsed:

                    paper_update = {
                        "pdf_local_path": pdf_local_path,
                        "is_pdf_downloaded": True,
                        "parsed_text": parsed.get("text", ""),
                        "sections": parsed.get("sections", {}),

                        "references": parsed.get("references", []),
                        "page_count": parsed.get("page_count", 0),
                    }
                    await mongodb.papers.update_one(
                        {"paper_id": paper_id},
                        {"$set": paper_update},
                    )
                    paper.update(paper_update)

        if not parsed:

            abstract = paper.get("abstract", "")
            parsed = {
                "sections": {"abstract": abstract},
                "text": abstract,
                "chunks": chunk_text(abstract, chunk_size=600) if abstract else [],
            }

        updated = await _summarize_paper({**paper, "parsed": parsed})
        summary = updated.get("summary")

        if summary:
            await mongodb.papers.update_one(
                {"paper_id": paper_id},
                {"$set": {"summary": summary}},
            )

        return summary

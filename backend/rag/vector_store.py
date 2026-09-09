"""
FAISS-based vector store wrapper for handling paper-level indices.
Provides search functionality based on cosine similarity of BAAI/bge-large-en-v1.5 embeddings.
"""

import os
import pickle
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import faiss

import numpy as np

from backend.rag.embedder import embed_texts
from backend.utils.logger import logger

class PaperVectorStore:
    """Manages a single paper's FAISS index and chunk metadata."""

    def __init__(self, paper_id: str, dimension: int = 1024):
        """
        Initialize the vector store for a paper.

        Args:
            paper_id: The unique paper ID.
            dimension: Embedding vector dimension (default 1024, ignored during build).
        """
        self.paper_id = paper_id
        self.dimension = dimension
        self.storage_dir = Path("storage/faiss")
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.index_path = self.storage_dir / f"{paper_id}.index"
        self.meta_path = self.storage_dir / f"{paper_id}.pkl"

        self.index: Optional[faiss.IndexFlatIP] = None
        self.chunks: List[str] = []

    def exists(self) -> bool:
        """Check if both the FAISS index and metadata files exist on disk."""
        return self.index_path.exists() and self.meta_path.exists()

    def build_and_save(self, chunks: List[str]) -> bool:
        """
        Build a FAISS index from text chunks and save both index and chunks to disk.

        Args:
            chunks: List of text chunks extracted from the paper.

        Returns:
            True if successful, False otherwise.
        """
        if not chunks:
            logger.warning(
                f"[VectorStore] No chunks provided to build index for paper {self.paper_id}"
            )
            return False

        try:
            logger.info(
                f"[VectorStore] Building FAISS index for paper {self.paper_id} with {len(chunks)} chunks..."
            )
            embeddings = embed_texts(chunks)

            dimension = embeddings.shape[1]
            self.index = faiss.IndexFlatIP(dimension)
            self.index.add(embeddings)

            faiss.write_index(self.index, str(self.index_path))

            self.chunks = chunks
            with open(self.meta_path, "wb") as f:
                pickle.dump(chunks, f)

            logger.info(
                f"[VectorStore] Successfully built and saved FAISS index for paper {self.paper_id}."
            )
            return True
        except Exception as e:
            logger.error(
                f"[VectorStore] Failed to build or save FAISS index for paper {self.paper_id}: {e}"
            )
            return False

    def load(self) -> bool:
        """
        Load the FAISS index and chunk metadata from disk.

        Returns:
            True if successful, False otherwise.
        """
        if not self.exists():
            logger.warning(
                f"[VectorStore] Cannot load: files do not exist for paper {self.paper_id}"
            )
            return False

        try:
            self.index = faiss.read_index(str(self.index_path))
            with open(self.meta_path, "rb") as f:
                self.chunks = pickle.load(f)
            return True
        except Exception as e:
            logger.error(
                f"[VectorStore] Failed to load index/chunks for paper {self.paper_id}: {e}"
            )
            return False

    def search(self, query: str, top_k: int = 5) -> List[str]:
        """
        Perform a semantic similarity search on the paper's chunks.

        Args:
            query: The natural language search query.
            top_k: Number of matching chunks to return.

        Returns:
            List of top_k most relevant text chunks.
        """
        if self.index is None:
            if not self.load():
                logger.warning(
                    f"[VectorStore] FAISS index not loaded for paper {self.paper_id}."
                )
                return []

        try:
            query_embedding = embed_texts([query])
            k = min(top_k, len(self.chunks))
            if k == 0:
                return []

            scores, indices = self.index.search(query_embedding, k)

            retrieved_chunks = []
            for idx in indices[0]:
                if 0 <= idx < len(self.chunks):
                    retrieved_chunks.append(self.chunks[idx])
            return retrieved_chunks
        except Exception as e:
            logger.error(
                f"[VectorStore] Semantic search failed for paper {self.paper_id}: {e}"
            )
            return []

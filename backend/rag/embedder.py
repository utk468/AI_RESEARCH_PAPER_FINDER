"""
SentenceTransformer embedder wrapper using Hugging Face Inference API for remote embeddings.
"""

import os
import time
from typing import List

import numpy as np

from huggingface_hub import InferenceClient

from backend.config import settings
from backend.utils.logger import logger

def embed_texts(texts: List[str]) -> np.ndarray:
    """
    Generate normalized embeddings for a list of texts using Hugging Face InferenceClient.
    """
    if not texts:

        return np.zeros((0, 1024), dtype=np.float32)

    hf_token = settings.HF_TOKEN or os.getenv("HF_TOKEN")

    if not hf_token:
        raise ValueError("[Embedder] HF_TOKEN is not configured!")

    client = InferenceClient(
        provider="hf-inference",
        api_key=hf_token,
    )

    max_retries = 3
    retry_delay = 5.0

    logger.info(f"[Embedder] Requesting InferenceClient feature_extraction for {len(texts)} chunks...")

    for attempt in range(1, max_retries + 1):
        try:

            result = client.feature_extraction(
                texts,
                model=settings.EMBEDDING_MODEL,
            )
            embeddings = np.array(result, dtype=np.float32)
            return embeddings

        except Exception as e:
            logger.error(f"[Embedder] InferenceClient error (attempt {attempt}): {e}")
            if attempt == max_retries:
                raise

        time.sleep(retry_delay)

    raise RuntimeError("[Embedder] Failed to get embeddings.")

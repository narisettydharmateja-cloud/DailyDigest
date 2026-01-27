"""Embedding generation service using sentence-transformers."""

from __future__ import annotations

from functools import lru_cache
from typing import List

import structlog
from sentence_transformers import SentenceTransformer

log = structlog.get_logger(__name__)

# Using a lightweight model suitable for semantic search
DEFAULT_MODEL = "all-MiniLM-L6-v2"  # 384 dimensions, 80MB


@lru_cache(maxsize=1)
def get_embedding_model(model_name: str = DEFAULT_MODEL) -> SentenceTransformer:
    """Load and cache the embedding model."""
    log.info("loading_embedding_model", model=model_name)
    return SentenceTransformer(model_name)


def generate_embeddings(texts: List[str], model_name: str = DEFAULT_MODEL) -> List[List[float]]:
    """
    Generate embeddings for a list of texts.
    
    Args:
        texts: List of text strings to embed
        model_name: Name of the sentence-transformers model
        
    Returns:
        List of embedding vectors (each is a list of floats)
    """
    if not texts:
        return []
    
    model = get_embedding_model(model_name)
    embeddings = model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
    
    # Convert numpy arrays to lists for JSON serialization
    return [embedding.tolist() for embedding in embeddings]


def generate_single_embedding(text: str, model_name: str = DEFAULT_MODEL) -> List[float]:
    """
    Generate embedding for a single text.
    
    Args:
        text: Text string to embed
        model_name: Name of the sentence-transformers model
        
    Returns:
        Embedding vector as list of floats
    """
    embeddings = generate_embeddings([text], model_name)
    return embeddings[0] if embeddings else []

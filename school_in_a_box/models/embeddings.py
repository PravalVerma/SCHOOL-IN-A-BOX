# models/embeddings.py
"""
Embedding utilities for School in a Box.

Uses the same model as your previous Agentic RAG project:
    sentence-transformers/all-MiniLM-L6-v2

Other modules (ingestion, vector_store, etc.) should call embed_texts()
instead of instantiating their own embedding models.
"""

from typing import List
import numpy as np
from sentence_transformers import SentenceTransformer

from config import EMBEDDING_MODEL_NAME

_model: SentenceTransformer | None = None


def get_embedding_model() -> SentenceTransformer:
    """
    Lazily load and cache the SentenceTransformer model.
    """
    global _model
    if _model is None:
        _model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    return _model


def embed_texts(texts: List[str]) -> np.ndarray:
    """
    Embed a list of texts into a NumPy array of shape (n_texts, dim).
    """
    model = get_embedding_model()
    # convert_to_numpy=True returns a float32 array already
    return model.encode(texts, convert_to_numpy=True)


def embed_text(text: str) -> np.ndarray:
    """
    Convenience helper for a single string. Returns shape (dim,).
    """
    embeddings = embed_texts([text])
    return embeddings[0]

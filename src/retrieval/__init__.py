"""
Retrieval Layer for Librarian Agent.

Provides modular retrieval interfaces and implementations:
- ChromaDBRetriever: Vector store retrieval using ChromaDB
- HybridRetriever: Combines semantic and keyword search
- RetrieverBase: Abstract interface for custom retrievers

Design patterns from:
- langgraph: Retriever as tools
- open-deep-research: Multi-stage retrieval
- local-deep-researcher: Local-first retrieval
"""

from .interfaces import (
    RetrieverBase,
    RetrieverConfig,
    RetrievalResult,
    DocumentChunk,
)
from .chroma import (
    ChromaRetriever,
    get_retriever,
    get_embedding_model,
)

__all__ = [
    "RetrieverBase",
    "RetrieverConfig",
    "RetrievalResult",
    "DocumentChunk",
    "ChromaRetriever",
    "get_retriever",
    "get_embedding_model",
]

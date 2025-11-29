"""
Retrieval Modes for Librarian Agent.

Provides different retrieval strategies:
- Foundation: Standard semantic search with high precision
- Lateral: Cross-domain connections using Context7 dimensions
"""

from .foundation import foundation_retrieval, foundation_response
from .lateral import lateral_retrieval, lateral_response

__all__ = [
    "foundation_retrieval",
    "foundation_response",
    "lateral_retrieval",
    "lateral_response",
]

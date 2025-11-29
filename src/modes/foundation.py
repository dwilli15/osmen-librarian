from typing import List, Dict, Any
try:
    from rag_manager import query_knowledge_base
except ImportError:
    import sys
    import os
    # Add parent directory to path to find rag_manager
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    from rag_manager import query_knowledge_base

def foundation_retrieval(query: str) -> List[Dict[str, Any]]:
    """Retrieves documents using foundation mode."""
    print(f"--- Mode: Foundation ({query}) ---")
    return query_knowledge_base(query, mode="foundation")

def foundation_response(docs: List[Dict[str, Any]]) -> str:
    """Synthesizes a foundation response."""
    summary = f"Found {len(docs)} documents in 'foundation' mode.\n"
    for doc in docs[:3]:
        summary += f"- {doc['content'][:100]}...\n"
    return summary

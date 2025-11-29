from typing import List, Dict, Any
try:
    from lateral_thinking import LateralEngine
    from rag_manager import get_vector_store
except ImportError:
    import sys
    import os
    # Add parent directory to path
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    from lateral_thinking import LateralEngine
    from rag_manager import get_vector_store

def lateral_retrieval(query: str) -> List[Dict[str, Any]]:
    """Retrieves documents using lateral thinking mode."""
    print(f"--- Mode: Lateral ({query}) ---")
    
    # Initialize LateralEngine with vector store
    vector_store = get_vector_store()
    engine = LateralEngine(vector_store=vector_store)
    
    # Weave results
    results = engine.weave_results(query)
    
    # Convert Documents to dicts
    docs = [{"content": d.page_content, "metadata": d.metadata} for d in results]
    return docs

def lateral_response(docs: List[Dict[str, Any]]) -> str:
    """Synthesizes a lateral response."""
    summary = f"Found {len(docs)} documents in 'lateral' mode.\n"
    for doc in docs[:3]:
        summary += f"- {doc['content'][:100]}...\n"
        if "c7_abstract" in doc['metadata']:
             summary += f"  (Context7: {doc['metadata'].get('c7_abstract')})\n"
    return summary

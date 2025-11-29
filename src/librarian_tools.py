from langchain_core.tools import tool
from typing import List, Dict, Any, Optional
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("librarian_tools")

try:
    from rag_manager import query_knowledge_base, ingest_data
except ImportError:
    # Fallback for relative imports if needed
    import sys
    import os
    sys.path.append(os.path.dirname(__file__))
    from rag_manager import query_knowledge_base, ingest_data

@tool
def search_librarian(query: str, mode: str = "foundation") -> str:
    """
    Search the Librarian knowledge base.
    
    Args:
        query: The search query text.
        mode: The retrieval mode. Options:
              - 'foundation': For basic concepts, definitions, and broad understanding.
              - 'lateral': For creative, cross-disciplinary, and 'Context7' connections.
              - 'factcheck': For finding specific evidence or source texts.
    
    Returns:
        A JSON string containing a list of documents with 'content' and 'metadata'.
    """
    try:
        logger.info(f"Searching Librarian: {query} (Mode: {mode})")
        if not query.strip():
            return json.dumps({"error": "Query cannot be empty"})
            
        results = query_knowledge_base(query, mode=mode)
        return json.dumps(results, indent=2)
    except Exception as e:
        logger.error(f"Error in search_librarian: {e}")
        return json.dumps({"error": str(e)})

@tool
def ingest_librarian(force: bool = False) -> str:
    """
    Trigger the ingestion process to update the Librarian knowledge base from the data directory.
    
    Args:
        force: If True, rebuilds the entire database from scratch. Use with caution.
    
    Returns:
        Status message indicating success or failure.
    """
    try:
        logger.info(f"Ingesting Librarian Data (Force={force})")
        ingest_data(force=force)
        return "Ingestion complete successfully."
    except Exception as e:
        logger.error(f"Error in ingest_librarian: {e}")
        return f"Error during ingestion: {e}"

def get_librarian_tools():
    """Returns a list of tools ready for a DeepAgent."""
    return [search_librarian, ingest_librarian]

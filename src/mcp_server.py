from mcp.server.fastmcp import FastMCP
from rag_manager import query_knowledge_base, ingest_data
import json

# Initialize FastMCP server
mcp = FastMCP("Librarian")

@mcp.tool()
def query(text: str, mode: str = "foundation") -> str:
    """
    Query the Librarian knowledge base.
    
    Args:
        text: The query text or question.
        mode: The retrieval mode. 
              - 'foundation': For basic concepts and definitions.
              - 'lateral': For creative, cross-disciplinary connections.
              - 'factcheck': For finding specific evidence.
    """
    try:
        if not text:
            return "Error: Query text cannot be empty."
        
        print(f"MCP Query: {text} (Mode: {mode})")
        results = query_knowledge_base(text, mode=mode)
        return json.dumps(results, indent=2)
    except Exception as e:
        error_msg = f"Error querying knowledge base: {str(e)}"
        print(error_msg)
        return error_msg

@mcp.tool()
def ingest(force: bool = False) -> str:
    """
    Trigger the ingestion process to update the knowledge base from the data directory.
    
    Args:
        force: If True, rebuilds the entire database from scratch.
    """
    try:
        print(f"MCP Ingest: Force={force}")
        ingest_data(force=force)
        return "Ingestion complete."
    except Exception as e:
        error_msg = f"Error during ingestion: {str(e)}"
        print(error_msg)
        return error_msg

if __name__ == "__main__":
    mcp.run()

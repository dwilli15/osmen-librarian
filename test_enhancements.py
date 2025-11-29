import sys
import os
import json

# Add src to path
sys.path.append(os.path.join(os.getcwd(), "src"))

from rag_manager import query_knowledge_base, ingest_data

def test_lateral_thinking():
    print("\n--- Testing Lateral Thinking (ContextWeaver) ---")
    query = "intersubjectivity"
    print(f"Query: {query}")
    
    try:
        results = query_knowledge_base(query, mode="lateral", device="cpu") # Use CPU for test to avoid CUDA issues if not set up
        print(f"Results found: {len(results)}")
        for i, doc in enumerate(results):
            layer = doc.get("metadata", {}).get("retrieval_layer", "unknown")
            print(f"[{i+1}] Layer: {layer} | Content Preview: {doc['content'][:50]}...")
            
        # Check if we have mixed layers
        layers = [doc.get("metadata", {}).get("retrieval_layer") for doc in results]
        if "shadow_context" in layers:
            print("SUCCESS: Shadow context woven into results.")
        else:
            print("WARNING: No shadow context found (might be due to small dataset).")
            
    except Exception as e:
        print(f"FAILED: {e}")
        import traceback
        traceback.print_exc()

def test_mcp_import():
    print("\n--- Testing MCP Server Import ---")
    try:
        import mcp_server
        print("SUCCESS: mcp_server imported successfully.")
    except ImportError as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    # Ensure we have some data
    if not os.path.exists("data/db"):
        print("Ingesting sample data first...")
        ingest_data(device="cpu")
        
    test_lateral_thinking()
    test_mcp_import()

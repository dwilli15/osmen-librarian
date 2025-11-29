import sys
import os
import json
import shutil

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from rag_manager import ingest_data, query_knowledge_base
import rag_manager

def test_lateral_flow():
    print("=== Testing Lateral Thinking Flow ===")
    
    # 1. Setup Temp Data
    print("\n[Step 1] Setting up temp data...")
    temp_dir = os.path.join(os.path.dirname(__file__), "temp_data")
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    os.makedirs(temp_dir, exist_ok=True)
    
    source_file = os.path.join(os.path.dirname(__file__), "data/lateral_test.md")
    shutil.copy(source_file, temp_dir)
    
    # Monkey patch SOURCE_DIRECTORIES in rag_manager
    # We need to patch the global variable in the module
    rag_manager.SOURCE_DIRECTORIES = [temp_dir]
    rag_manager.PERSIST_DIRECTORY = os.path.join(temp_dir, "db")
    
    try:
        # 2. Ingest (should trigger enrichment)
        print("\n[Step 2] Ingesting data...")
        # We force ingestion to ensure our new document is processed
        ingest_data(force=True, device="cpu") # Use CPU for test speed/compatibility
        
        # 3. Query (should trigger weaving)
        print("\n[Step 3] Querying in Lateral Mode...")
        query = "What is the nature of Python?"
        results = query_knowledge_base(query, mode="lateral", device="cpu")
        
        # 4. Verify
        print("\n[Step 4] Verifying Results...")
        
        for i, doc in enumerate(results):
            content = doc['content']
            meta = doc['metadata']
            print(f"\nResult {i+1}:")
            print(f"  Content: {content[:50]}...")
            print(f"  Metadata: {meta}")
            
            if "c7_abstract" in meta and meta["c7_abstract"] == "metaphorical":
                print("  -> Verified: Context7 Enrichment present (Abstract)")
            
            if "c7_domain" in meta:
                 print(f"  -> Verified: Context7 Domain: {meta['c7_domain']}")

    finally:
        # Cleanup
        print("\n[Cleanup] Removing temp data...")
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

    print("\n=== Test Complete ===")

if __name__ == "__main__":
    test_lateral_flow()

import sys
import os
import json

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from librarian_tools import search_librarian, ingest_librarian

def test_tools():
    print("=== Testing DeepAgent Tools ===")
    
    # Test 1: Search (Foundation)
    print("\n[Test 1] Search (Foundation)...")
    result = search_librarian.invoke({"query": "python", "mode": "foundation"})
    print(f"Result type: {type(result)}")
    try:
        data = json.loads(result)
        print(f"Found {len(data)} documents.")
    except:
        print("Failed to parse JSON")

    # Test 2: Search (Lateral)
    print("\n[Test 2] Search (Lateral)...")
    result = search_librarian.invoke({"query": "python", "mode": "lateral"})
    try:
        data = json.loads(result)
        print(f"Found {len(data)} documents.")
        # Check for Context7
        has_c7 = any("c7_domain" in d.get("metadata", {}) for d in data)
        if has_c7:
            print("Verified: Context7 metadata present.")
    except:
        print("Failed to parse JSON")

    print("\n=== Test Complete ===")

if __name__ == "__main__":
    test_tools()

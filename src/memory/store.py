from typing import Any, Dict, Optional
import os
try:
    from rag_manager import get_vector_store
except ImportError:
    import sys
    import os
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    from rag_manager import get_vector_store

class CompositeStore:
    """
    Routes storage requests to the appropriate backend (Vector Store or Ephemeral).
    """
    def __init__(self):
        self.ephemeral_store = {}
        # Lazy load vector store to avoid early init issues
        self._vector_store = None

    @property
    def vector_store(self):
        if self._vector_store is None:
            self._vector_store = get_vector_store(device="cpu")
        return self._vector_store

    def put(self, key: str, value: Any, namespace: str = "ephemeral"):
        """
        Saves data to the specified namespace.
        - 'memories': Persistent Vector Store
        - 'ephemeral': In-Memory Dictionary
        """
        if namespace == "memories":
            # Assume value is a Document or text to be embedded
            # This is a simplification; real implementation would handle doc structure
            self.vector_store.add_texts([str(value)], metadatas=[{"key": key}])
        else:
            self.ephemeral_store[key] = value

    def get(self, key: str, namespace: str = "ephemeral") -> Optional[Any]:
        """Retrieves data from the specified namespace."""
        if namespace == "memories":
            # Search by key metadata
            results = self.vector_store.similarity_search(key, k=1)
            return results[0] if results else None
        else:
            return self.ephemeral_store.get(key)

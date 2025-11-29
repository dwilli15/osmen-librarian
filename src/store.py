"""
Composite Storage for Librarian Agent.

Provides:
- Unified storage interface for persistent and ephemeral data
- Route-based storage selection (/memories/*, /tmp/*, etc.)
- Per-subagent isolated storage
- Long-term memory store for cross-session context
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
import json
import time
import uuid
import os
import logging

logger = logging.getLogger("librarian.store")


# =============================================================================
# Storage Item
# =============================================================================

@dataclass
class StorageItem:
    """A single item in storage."""
    key: str
    value: Any
    namespace: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    ttl: Optional[float] = None  # Time-to-live in seconds

    def is_expired(self) -> bool:
        """Check if item has expired."""
        if self.ttl is None:
            return False
        return time.time() > (self.created_at + self.ttl)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "key": self.key,
            "value": self.value,
            "namespace": self.namespace,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "ttl": self.ttl
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StorageItem":
        return cls(
            key=data["key"],
            value=data["value"],
            namespace=data.get("namespace", ""),
            metadata=data.get("metadata", {}),
            created_at=data.get("created_at", time.time()),
            updated_at=data.get("updated_at", time.time()),
            ttl=data.get("ttl")
        )


# =============================================================================
# Abstract Store
# =============================================================================

class BaseStore(ABC):
    """Abstract base class for storage backends."""

    @abstractmethod
    def get(self, namespace: str, key: str) -> Optional[StorageItem]:
        """Get an item by namespace and key."""
        pass

    @abstractmethod
    def put(
        self,
        namespace: str,
        key: str,
        value: Any,
        metadata: Optional[Dict[str, Any]] = None,
        ttl: Optional[float] = None
    ) -> StorageItem:
        """Store an item."""
        pass

    @abstractmethod
    def delete(self, namespace: str, key: str) -> bool:
        """Delete an item."""
        pass

    @abstractmethod
    def list(
        self,
        namespace: str,
        prefix: str = "",
        limit: int = 100
    ) -> List[StorageItem]:
        """List items in a namespace."""
        pass

    @abstractmethod
    def search(
        self,
        namespace: str,
        query: Dict[str, Any],
        limit: int = 10
    ) -> List[StorageItem]:
        """Search items by metadata query."""
        pass

    def batch_get(
        self,
        items: List[Tuple[str, str]]
    ) -> Dict[Tuple[str, str], Optional[StorageItem]]:
        """Batch get items. Default implementation is sequential."""
        return {(ns, key): self.get(ns, key) for ns, key in items}

    def batch_put(
        self,
        items: List[Tuple[str, str, Any, Optional[Dict], Optional[float]]]
    ) -> List[StorageItem]:
        """Batch put items. Default implementation is sequential."""
        results = []
        for ns, key, value, meta, ttl in items:
            results.append(self.put(ns, key, value, meta, ttl))
        return results


# =============================================================================
# In-Memory Store
# =============================================================================

class InMemoryStore(BaseStore):
    """
    In-memory storage for development and testing.

    Fast but not persistent across restarts.
    """

    def __init__(self):
        self._storage: Dict[str, Dict[str, StorageItem]] = {}

    def _get_namespace(self, namespace: str) -> Dict[str, StorageItem]:
        if namespace not in self._storage:
            self._storage[namespace] = {}
        return self._storage[namespace]

    def get(self, namespace: str, key: str) -> Optional[StorageItem]:
        ns = self._get_namespace(namespace)
        item = ns.get(key)
        if item and item.is_expired():
            del ns[key]
            return None
        return item

    def put(
        self,
        namespace: str,
        key: str,
        value: Any,
        metadata: Optional[Dict[str, Any]] = None,
        ttl: Optional[float] = None
    ) -> StorageItem:
        ns = self._get_namespace(namespace)
        now = time.time()

        # Update if exists, create otherwise
        if key in ns:
            item = ns[key]
            item.value = value
            item.metadata = metadata or item.metadata
            item.updated_at = now
            if ttl is not None:
                item.ttl = ttl
        else:
            item = StorageItem(
                key=key,
                value=value,
                namespace=namespace,
                metadata=metadata or {},
                ttl=ttl
            )
            ns[key] = item

        return item

    def delete(self, namespace: str, key: str) -> bool:
        ns = self._get_namespace(namespace)
        if key in ns:
            del ns[key]
            return True
        return False

    def list(
        self,
        namespace: str,
        prefix: str = "",
        limit: int = 100
    ) -> List[StorageItem]:
        ns = self._get_namespace(namespace)
        items = []
        for key, item in ns.items():
            if item.is_expired():
                continue
            if prefix and not key.startswith(prefix):
                continue
            items.append(item)
            if len(items) >= limit:
                break
        return items

    def search(
        self,
        namespace: str,
        query: Dict[str, Any],
        limit: int = 10
    ) -> List[StorageItem]:
        ns = self._get_namespace(namespace)
        results = []

        for item in ns.values():
            if item.is_expired():
                continue

            # Match all query conditions against metadata
            match = True
            for qk, qv in query.items():
                if qk not in item.metadata or item.metadata[qk] != qv:
                    match = False
                    break

            if match:
                results.append(item)
                if len(results) >= limit:
                    break

        return results

    def clear_namespace(self, namespace: str) -> int:
        """Clear all items in a namespace."""
        if namespace in self._storage:
            count = len(self._storage[namespace])
            self._storage[namespace] = {}
            return count
        return 0

    def clear_all(self) -> None:
        """Clear all storage."""
        self._storage.clear()


# =============================================================================
# Composite Store with Route-Based Selection
# =============================================================================

class CompositeStore(BaseStore):
    """
    Composite storage with route-based backend selection.

    Routes:
    - /memories/* → Persistent store (long-term memory)
    - /tmp/* → Ephemeral store (session-only)
    - /subagent/<name>/* → Isolated per-subagent store
    - Default → Persistent store
    """

    def __init__(
        self,
        persistent: Optional[BaseStore] = None,
        ephemeral: Optional[BaseStore] = None
    ):
        self._persistent = persistent or InMemoryStore()
        self._ephemeral = ephemeral or InMemoryStore()
        self._subagent_stores: Dict[str, BaseStore] = {}

    def _get_store_for_namespace(self, namespace: str) -> Tuple[BaseStore, str]:
        """
        Determine which store to use based on namespace prefix.

        Returns (store, effective_namespace).
        """
        if namespace.startswith("/tmp/"):
            # Ephemeral storage
            effective_ns = namespace[5:]  # Strip /tmp/
            return self._ephemeral, effective_ns

        elif namespace.startswith("/subagent/"):
            # Per-subagent isolated storage
            parts = namespace[10:].split("/", 1)
            subagent_name = parts[0]
            effective_ns = parts[1] if len(parts) > 1 else ""

            if subagent_name not in self._subagent_stores:
                self._subagent_stores[subagent_name] = InMemoryStore()

            return self._subagent_stores[subagent_name], effective_ns

        elif namespace.startswith("/memories/"):
            # Persistent memory storage
            effective_ns = namespace[10:]  # Strip /memories/
            return self._persistent, effective_ns

        else:
            # Default to persistent
            return self._persistent, namespace

    def get(self, namespace: str, key: str) -> Optional[StorageItem]:
        store, effective_ns = self._get_store_for_namespace(namespace)
        return store.get(effective_ns, key)

    def put(
        self,
        namespace: str,
        key: str,
        value: Any,
        metadata: Optional[Dict[str, Any]] = None,
        ttl: Optional[float] = None
    ) -> StorageItem:
        store, effective_ns = self._get_store_for_namespace(namespace)

        # Auto-set TTL for ephemeral storage
        if namespace.startswith("/tmp/") and ttl is None:
            ttl = 3600  # 1 hour default for temp storage

        return store.put(effective_ns, key, value, metadata, ttl)

    def delete(self, namespace: str, key: str) -> bool:
        store, effective_ns = self._get_store_for_namespace(namespace)
        return store.delete(effective_ns, key)

    def list(
        self,
        namespace: str,
        prefix: str = "",
        limit: int = 100
    ) -> List[StorageItem]:
        store, effective_ns = self._get_store_for_namespace(namespace)
        return store.list(effective_ns, prefix, limit)

    def search(
        self,
        namespace: str,
        query: Dict[str, Any],
        limit: int = 10
    ) -> List[StorageItem]:
        store, effective_ns = self._get_store_for_namespace(namespace)
        return store.search(effective_ns, query, limit)

    def get_subagent_store(self, name: str) -> BaseStore:
        """Get or create isolated store for a subagent."""
        if name not in self._subagent_stores:
            self._subagent_stores[name] = InMemoryStore()
        return self._subagent_stores[name]

    def clear_subagent(self, name: str) -> bool:
        """Clear a subagent's isolated storage."""
        if name in self._subagent_stores:
            self._subagent_stores[name] = InMemoryStore()
            return True
        return False

    def clear_ephemeral(self) -> None:
        """Clear all ephemeral storage."""
        if isinstance(self._ephemeral, InMemoryStore):
            self._ephemeral.clear_all()


# =============================================================================
# Long-Term Memory Store (Conversation/Context Memory)
# =============================================================================

class LongTermMemoryStore:
    """
    Specialized store for long-term conversation memory.

    Features:
    - Thread-based organization
    - Automatic summarization hints
    - Context relevance scoring (placeholder)
    """

    def __init__(self, base_store: Optional[BaseStore] = None):
        self._store = base_store or InMemoryStore()

    def add_memory(
        self,
        thread_id: str,
        content: str,
        memory_type: str = "conversation",
        metadata: Optional[Dict[str, Any]] = None
    ) -> StorageItem:
        """Add a memory item for a thread."""
        key = f"{memory_type}:{uuid.uuid4().hex[:8]}"
        meta = metadata or {}
        meta["memory_type"] = memory_type
        meta["thread_id"] = thread_id

        return self._store.put(
            namespace=f"threads/{thread_id}",
            key=key,
            value=content,
            metadata=meta
        )

    def get_thread_memories(
        self,
        thread_id: str,
        memory_type: Optional[str] = None,
        limit: int = 50
    ) -> List[StorageItem]:
        """Get memories for a thread."""
        items = self._store.list(
            namespace=f"threads/{thread_id}",
            prefix=f"{memory_type}:" if memory_type else "",
            limit=limit
        )
        # Sort by creation time
        return sorted(items, key=lambda x: x.created_at)

    def search_memories(
        self,
        thread_id: str,
        query: Dict[str, Any],
        limit: int = 10
    ) -> List[StorageItem]:
        """Search memories by metadata."""
        return self._store.search(
            namespace=f"threads/{thread_id}",
            query=query,
            limit=limit
        )

    def clear_thread(self, thread_id: str) -> bool:
        """Clear all memories for a thread."""
        items = self._store.list(namespace=f"threads/{thread_id}", limit=1000)
        for item in items:
            self._store.delete(f"threads/{thread_id}", item.key)
        return len(items) > 0


# =============================================================================
# Factory Functions
# =============================================================================

def create_store(backend: str = "memory", **kwargs) -> BaseStore:
    """
    Create a storage backend.

    Args:
        backend: "memory" or "sqlite" (sqlite not yet implemented)
        **kwargs: Backend-specific arguments

    Returns:
        Configured store instance
    """
    if backend == "memory":
        return InMemoryStore()
    else:
        raise ValueError(f"Unknown store backend: {backend}")


def create_composite_store(
    persistent_backend: str = "memory",
    ephemeral_backend: str = "memory",
    **kwargs
) -> CompositeStore:
    """
    Create a composite store with route-based selection.

    Args:
        persistent_backend: Backend for persistent storage
        ephemeral_backend: Backend for ephemeral storage
        **kwargs: Backend-specific arguments

    Returns:
        Configured CompositeStore
    """
    persistent = create_store(persistent_backend, **kwargs)
    ephemeral = create_store(ephemeral_backend, **kwargs)
    return CompositeStore(persistent=persistent, ephemeral=ephemeral)


def get_default_store() -> CompositeStore:
    """Get the default composite store based on environment."""
    backend = os.environ.get("LIBRARIAN_STORE_BACKEND", "memory")
    return create_composite_store(persistent_backend=backend)


# =============================================================================
# Aliases and Compatibility
# =============================================================================

@dataclass
class StorageRoute:
    """
    Route configuration for composite store.
    
    Defines which backend handles which namespace patterns.
    """
    pattern: str  # Namespace pattern (e.g., "/tmp/*", "/memories/*")
    backend: str = "persistent"  # "persistent", "ephemeral", or "subagent"
    ttl: Optional[float] = None  # Default TTL for this route

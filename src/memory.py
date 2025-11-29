"""
Memory Management for Librarian Agent.

Provides:
- Checkpointer abstraction with InMemorySaver baseline
- SQLite checkpointer for development
- PostgreSQL checkpointer for production (optional)
- State schemas aligned with LangGraph patterns
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple, Iterator
from dataclasses import dataclass, field
import json
import time
import uuid
import logging
import os

logger = logging.getLogger("librarian.memory")


# =============================================================================
# Checkpoint Data Structures
# =============================================================================

@dataclass
class Checkpoint:
    """A saved checkpoint of agent state."""
    id: str
    thread_id: str
    parent_id: Optional[str]
    state: Dict[str, Any]
    metadata: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "thread_id": self.thread_id,
            "parent_id": self.parent_id,
            "state": self.state,
            "metadata": self.metadata,
            "timestamp": self.timestamp
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Checkpoint":
        return cls(
            id=data["id"],
            thread_id=data["thread_id"],
            parent_id=data.get("parent_id"),
            state=data["state"],
            metadata=data.get("metadata", {}),
            timestamp=data.get("timestamp", time.time())
        )


@dataclass
class CheckpointConfig:
    """Configuration for checkpoint operations."""
    thread_id: str
    checkpoint_id: Optional[str] = None
    checkpoint_ns: str = ""  # Namespace for subgraph isolation


# =============================================================================
# Abstract Checkpointer
# =============================================================================

class BaseCheckpointer(ABC):
    """Abstract base class for checkpoint storage."""

    @abstractmethod
    def put(
        self,
        config: CheckpointConfig,
        checkpoint: Checkpoint
    ) -> Checkpoint:
        """Save a checkpoint."""
        pass

    @abstractmethod
    def get(self, config: CheckpointConfig) -> Optional[Checkpoint]:
        """Get the latest checkpoint for a thread."""
        pass

    @abstractmethod
    def get_by_id(
        self,
        config: CheckpointConfig,
        checkpoint_id: str
    ) -> Optional[Checkpoint]:
        """Get a specific checkpoint by ID."""
        pass

    @abstractmethod
    def list(
        self,
        config: CheckpointConfig,
        limit: int = 10
    ) -> List[Checkpoint]:
        """List checkpoints for a thread."""
        pass

    @abstractmethod
    def delete(self, config: CheckpointConfig) -> bool:
        """Delete all checkpoints for a thread."""
        pass

    def create_checkpoint(
        self,
        config: CheckpointConfig,
        state: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
        parent_id: Optional[str] = None
    ) -> Checkpoint:
        """Helper to create and save a checkpoint."""
        checkpoint = Checkpoint(
            id=str(uuid.uuid4()),
            thread_id=config.thread_id,
            parent_id=parent_id,
            state=state,
            metadata=metadata or {}
        )
        return self.put(config, checkpoint)


# =============================================================================
# In-Memory Checkpointer (Development)
# =============================================================================

class InMemoryCheckpointer(BaseCheckpointer):
    """
    In-memory checkpoint storage for development and testing.

    Fast but not persistent across restarts.
    """

    def __init__(self):
        self._storage: Dict[str, List[Checkpoint]] = {}

    def put(
        self,
        config: CheckpointConfig,
        checkpoint: Checkpoint
    ) -> Checkpoint:
        key = f"{config.checkpoint_ns}:{config.thread_id}"
        if key not in self._storage:
            self._storage[key] = []
        self._storage[key].append(checkpoint)
        logger.debug(f"Saved checkpoint {checkpoint.id} for thread {config.thread_id}")
        return checkpoint

    def get(self, config: CheckpointConfig) -> Optional[Checkpoint]:
        key = f"{config.checkpoint_ns}:{config.thread_id}"
        checkpoints = self._storage.get(key, [])
        if not checkpoints:
            return None
        # Return latest by timestamp
        return max(checkpoints, key=lambda c: c.timestamp)

    def get_by_id(
        self,
        config: CheckpointConfig,
        checkpoint_id: str
    ) -> Optional[Checkpoint]:
        key = f"{config.checkpoint_ns}:{config.thread_id}"
        checkpoints = self._storage.get(key, [])
        for cp in checkpoints:
            if cp.id == checkpoint_id:
                return cp
        return None

    def list(
        self,
        config: CheckpointConfig,
        limit: int = 10
    ) -> List[Checkpoint]:
        key = f"{config.checkpoint_ns}:{config.thread_id}"
        checkpoints = self._storage.get(key, [])
        # Sort by timestamp descending
        sorted_cps = sorted(checkpoints, key=lambda c: c.timestamp, reverse=True)
        return sorted_cps[:limit]

    def delete(self, config: CheckpointConfig) -> bool:
        key = f"{config.checkpoint_ns}:{config.thread_id}"
        if key in self._storage:
            del self._storage[key]
            return True
        return False

    def clear_all(self) -> None:
        """Clear all checkpoints (for testing)."""
        self._storage.clear()


# =============================================================================
# SQLite Checkpointer (Development/Production)
# =============================================================================

class SQLiteCheckpointer(BaseCheckpointer):
    """
    SQLite-based checkpoint storage for persistence.

    Suitable for development and small-scale production.
    """

    def __init__(self, db_path: str = "checkpoints.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        """Initialize the database schema."""
        import sqlite3
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS checkpoints (
                id TEXT PRIMARY KEY,
                thread_id TEXT NOT NULL,
                namespace TEXT DEFAULT '',
                parent_id TEXT,
                state TEXT NOT NULL,
                metadata TEXT,
                timestamp REAL NOT NULL,
                UNIQUE(thread_id, namespace, id)
            )
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_thread_ns
            ON checkpoints(thread_id, namespace, timestamp DESC)
        """)
        conn.commit()
        conn.close()
        logger.info(f"SQLite checkpointer initialized: {self.db_path}")

    def _get_conn(self):
        import sqlite3
        return sqlite3.connect(self.db_path)

    def put(
        self,
        config: CheckpointConfig,
        checkpoint: Checkpoint
    ) -> Checkpoint:
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO checkpoints
            (id, thread_id, namespace, parent_id, state, metadata, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            checkpoint.id,
            config.thread_id,
            config.checkpoint_ns,
            checkpoint.parent_id,
            json.dumps(checkpoint.state),
            json.dumps(checkpoint.metadata),
            checkpoint.timestamp
        ))
        conn.commit()
        conn.close()
        logger.debug(f"Saved checkpoint {checkpoint.id} to SQLite")
        return checkpoint

    def get(self, config: CheckpointConfig) -> Optional[Checkpoint]:
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, thread_id, parent_id, state, metadata, timestamp
            FROM checkpoints
            WHERE thread_id = ? AND namespace = ?
            ORDER BY timestamp DESC
            LIMIT 1
        """, (config.thread_id, config.checkpoint_ns))
        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return Checkpoint(
            id=row[0],
            thread_id=row[1],
            parent_id=row[2],
            state=json.loads(row[3]),
            metadata=json.loads(row[4]) if row[4] else {},
            timestamp=row[5]
        )

    def get_by_id(
        self,
        config: CheckpointConfig,
        checkpoint_id: str
    ) -> Optional[Checkpoint]:
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, thread_id, parent_id, state, metadata, timestamp
            FROM checkpoints
            WHERE id = ? AND thread_id = ? AND namespace = ?
        """, (checkpoint_id, config.thread_id, config.checkpoint_ns))
        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return Checkpoint(
            id=row[0],
            thread_id=row[1],
            parent_id=row[2],
            state=json.loads(row[3]),
            metadata=json.loads(row[4]) if row[4] else {},
            timestamp=row[5]
        )

    def list(
        self,
        config: CheckpointConfig,
        limit: int = 10
    ) -> List[Checkpoint]:
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, thread_id, parent_id, state, metadata, timestamp
            FROM checkpoints
            WHERE thread_id = ? AND namespace = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """, (config.thread_id, config.checkpoint_ns, limit))
        rows = cursor.fetchall()
        conn.close()

        return [
            Checkpoint(
                id=row[0],
                thread_id=row[1],
                parent_id=row[2],
                state=json.loads(row[3]),
                metadata=json.loads(row[4]) if row[4] else {},
                timestamp=row[5]
            )
            for row in rows
        ]

    def delete(self, config: CheckpointConfig) -> bool:
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            DELETE FROM checkpoints
            WHERE thread_id = ? AND namespace = ?
        """, (config.thread_id, config.checkpoint_ns))
        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return deleted


# =============================================================================
# LangGraph Integration Wrapper
# =============================================================================

class LangGraphCheckpointerAdapter:
    """
    Adapter to use our checkpointer with LangGraph's compile().

    Implements the interface expected by langgraph.checkpoint.
    """

    def __init__(self, checkpointer: BaseCheckpointer):
        self._checkpointer = checkpointer
        self._config_cache: Dict[str, CheckpointConfig] = {}

    def _get_config(self, config: Dict[str, Any]) -> CheckpointConfig:
        """Extract CheckpointConfig from LangGraph config."""
        configurable = config.get("configurable", {})
        thread_id = configurable.get("thread_id", "default")
        checkpoint_ns = configurable.get("checkpoint_ns", "")
        checkpoint_id = configurable.get("checkpoint_id")

        return CheckpointConfig(
            thread_id=thread_id,
            checkpoint_ns=checkpoint_ns,
            checkpoint_id=checkpoint_id
        )

    def put(
        self,
        config: Dict[str, Any],
        checkpoint: Dict[str, Any],
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Save checkpoint (LangGraph interface)."""
        cp_config = self._get_config(config)

        cp = Checkpoint(
            id=checkpoint.get("id", str(uuid.uuid4())),
            thread_id=cp_config.thread_id,
            parent_id=checkpoint.get("parent_id"),
            state=checkpoint.get("channel_values", {}),
            metadata=metadata
        )

        self._checkpointer.put(cp_config, cp)
        return {"configurable": {"thread_id": cp_config.thread_id, "checkpoint_id": cp.id}}

    def get_tuple(self, config: Dict[str, Any]) -> Optional[Tuple]:
        """Get checkpoint as tuple (LangGraph interface)."""
        cp_config = self._get_config(config)
        checkpoint = self._checkpointer.get(cp_config)

        if not checkpoint:
            return None

        return (
            {"configurable": {"thread_id": cp_config.thread_id, "checkpoint_id": checkpoint.id}},
            {
                "id": checkpoint.id,
                "channel_values": checkpoint.state,
                "parent_id": checkpoint.parent_id
            },
            checkpoint.metadata
        )

    def list(
        self,
        config: Dict[str, Any],
        *,
        filter: Optional[Dict[str, Any]] = None,
        before: Optional[Dict[str, Any]] = None,
        limit: int = 10
    ) -> Iterator[Tuple]:
        """List checkpoints (LangGraph interface)."""
        cp_config = self._get_config(config)
        checkpoints = self._checkpointer.list(cp_config, limit=limit)

        for cp in checkpoints:
            yield (
                {"configurable": {"thread_id": cp_config.thread_id, "checkpoint_id": cp.id}},
                {
                    "id": cp.id,
                    "channel_values": cp.state,
                    "parent_id": cp.parent_id
                },
                cp.metadata
            )


# =============================================================================
# Factory Functions
# =============================================================================

def create_checkpointer(
    backend: str = "memory",
    **kwargs
) -> BaseCheckpointer:
    """
    Create a checkpointer based on backend type.

    Args:
        backend: "memory", "sqlite", or "postgres"
        **kwargs: Backend-specific arguments

    Returns:
        Configured checkpointer instance
    """
    if backend == "memory":
        return InMemoryCheckpointer()
    elif backend == "sqlite":
        db_path = kwargs.get("db_path", "checkpoints.db")
        return SQLiteCheckpointer(db_path=db_path)
    elif backend == "postgres":
        # Placeholder for PostgreSQL support
        raise NotImplementedError(
            "PostgreSQL checkpointer not yet implemented. "
            "Use langgraph.checkpoint.postgres.PostgresSaver directly."
        )
    else:
        raise ValueError(f"Unknown checkpointer backend: {backend}")


def get_default_checkpointer() -> BaseCheckpointer:
    """
    Get the default checkpointer based on environment.

    Uses:
    - LIBRARIAN_CHECKPOINT_BACKEND env var
    - LIBRARIAN_CHECKPOINT_PATH for SQLite path
    """
    backend = os.environ.get("LIBRARIAN_CHECKPOINT_BACKEND", "memory")
    db_path = os.environ.get("LIBRARIAN_CHECKPOINT_PATH", "data/checkpoints.db")

    return create_checkpointer(backend=backend, db_path=db_path)


# Aliases for backward compatibility with tests
get_checkpointer = create_checkpointer
MemoryConfig = CheckpointConfig

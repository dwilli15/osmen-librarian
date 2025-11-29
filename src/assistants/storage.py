"""
Storage backends for Assistants.

Provides persistent storage for:
- Assistants (definitions)
- Threads (conversations)
- Runs (executions)

Supports:
- In-memory (development)
- SQLite (local persistence)
- File-based JSON (simple persistence)
"""

from typing import Any, Dict, List, Optional, Protocol, Type
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
import json
import logging
import os

from .schema import Assistant, Thread, Run, Message, MessageRole

logger = logging.getLogger("librarian.assistants.storage")


class StorageBackend(Protocol):
    """Protocol for storage backends."""
    
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get item by key."""
        ...
    
    def put(self, key: str, value: Dict[str, Any]) -> None:
        """Put item."""
        ...
    
    def delete(self, key: str) -> bool:
        """Delete item."""
        ...
    
    def list(self, prefix: str = "") -> List[str]:
        """List keys with optional prefix."""
        ...


class InMemoryBackend:
    """In-memory storage backend."""
    
    def __init__(self):
        self._data: Dict[str, Dict[str, Any]] = {}
    
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        return self._data.get(key)
    
    def put(self, key: str, value: Dict[str, Any]) -> None:
        self._data[key] = value
    
    def delete(self, key: str) -> bool:
        if key in self._data:
            del self._data[key]
            return True
        return False
    
    def list(self, prefix: str = "") -> List[str]:
        return [k for k in self._data.keys() if k.startswith(prefix)]


class FileBackend:
    """File-based JSON storage backend."""
    
    def __init__(self, base_path: str = "./data/assistants"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    def _key_to_path(self, key: str) -> Path:
        """Convert key to file path."""
        safe_key = key.replace("/", "_").replace("\\", "_")
        return self.base_path / f"{safe_key}.json"
    
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        path = self._key_to_path(key)
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to read {path}: {e}")
        return None
    
    def put(self, key: str, value: Dict[str, Any]) -> None:
        path = self._key_to_path(key)
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(value, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to write {path}: {e}")
    
    def delete(self, key: str) -> bool:
        path = self._key_to_path(key)
        if path.exists():
            try:
                path.unlink()
                return True
            except Exception as e:
                logger.error(f"Failed to delete {path}: {e}")
        return False
    
    def list(self, prefix: str = "") -> List[str]:
        keys = []
        safe_prefix = prefix.replace("/", "_").replace("\\", "_")
        for path in self.base_path.glob("*.json"):
            key = path.stem
            if key.startswith(safe_prefix):
                keys.append(key)
        return keys


class AssistantStore:
    """
    Store for managing assistants.
    
    Provides CRUD operations for assistant definitions.
    """
    
    def __init__(self, backend: Optional[StorageBackend] = None):
        self.backend = backend or InMemoryBackend()
        self._prefix = "assistant:"
    
    def _key(self, assistant_id: str) -> str:
        """Generate storage key for assistant."""
        return f"{self._prefix}{assistant_id}"
    
    def create(self, assistant: Assistant) -> Assistant:
        """Create a new assistant."""
        key = self._key(assistant.id)
        self.backend.put(key, assistant.to_dict())
        logger.info(f"Created assistant: {assistant.id}")
        return assistant
    
    def get(self, assistant_id: str) -> Optional[Assistant]:
        """Get assistant by ID."""
        key = self._key(assistant_id)
        data = self.backend.get(key)
        if data:
            return Assistant.from_dict(data)
        return None
    
    def update(self, assistant: Assistant) -> Assistant:
        """Update an existing assistant."""
        assistant.updated_at = datetime.utcnow()
        key = self._key(assistant.id)
        self.backend.put(key, assistant.to_dict())
        logger.info(f"Updated assistant: {assistant.id}")
        return assistant
    
    def delete(self, assistant_id: str) -> bool:
        """Delete an assistant."""
        key = self._key(assistant_id)
        result = self.backend.delete(key)
        if result:
            logger.info(f"Deleted assistant: {assistant_id}")
        return result
    
    def list(self) -> List[Assistant]:
        """List all assistants."""
        keys = self.backend.list(self._prefix)
        assistants = []
        for key in keys:
            data = self.backend.get(key)
            if data:
                assistants.append(Assistant.from_dict(data))
        return assistants
    
    def get_or_create_default(self, preset: str = "librarian") -> Assistant:
        """Get or create a default assistant from presets."""
        from .schema import PRESET_ASSISTANTS, Assistant
        
        if preset in PRESET_ASSISTANTS:
            config = PRESET_ASSISTANTS[preset]
            existing = self.get(config.id)
            if existing:
                return existing
            assistant = Assistant.from_config(config)
            return self.create(assistant)
        
        # Return first available or create default
        assistants = self.list()
        if assistants:
            return assistants[0]
        
        config = PRESET_ASSISTANTS["librarian"]
        assistant = Assistant.from_config(config)
        return self.create(assistant)


class ThreadStore:
    """
    Store for managing threads.
    
    Provides CRUD operations for conversation threads.
    """
    
    def __init__(self, backend: Optional[StorageBackend] = None):
        self.backend = backend or InMemoryBackend()
        self._prefix = "thread:"
    
    def _key(self, thread_id: str) -> str:
        """Generate storage key for thread."""
        return f"{self._prefix}{thread_id}"
    
    def create(self, thread: Optional[Thread] = None) -> Thread:
        """Create a new thread."""
        thread = thread or Thread()
        key = self._key(thread.id)
        self.backend.put(key, thread.to_dict())
        logger.info(f"Created thread: {thread.id}")
        return thread
    
    def get(self, thread_id: str) -> Optional[Thread]:
        """Get thread by ID."""
        key = self._key(thread_id)
        data = self.backend.get(key)
        if data:
            return Thread.from_dict(data)
        return None
    
    def update(self, thread: Thread) -> Thread:
        """Update an existing thread."""
        thread.updated_at = datetime.utcnow()
        key = self._key(thread.id)
        self.backend.put(key, thread.to_dict())
        return thread
    
    def delete(self, thread_id: str) -> bool:
        """Delete a thread."""
        key = self._key(thread_id)
        result = self.backend.delete(key)
        if result:
            logger.info(f"Deleted thread: {thread_id}")
        return result
    
    def list(self, assistant_id: Optional[str] = None) -> List[Thread]:
        """List threads, optionally filtered by assistant."""
        keys = self.backend.list(self._prefix)
        threads = []
        for key in keys:
            data = self.backend.get(key)
            if data:
                thread = Thread.from_dict(data)
                if assistant_id is None or thread.assistant_id == assistant_id:
                    threads.append(thread)
        return threads
    
    def add_message(
        self,
        thread_id: str,
        role: MessageRole,
        content: str
    ) -> Optional[Message]:
        """Add a message to a thread."""
        thread = self.get(thread_id)
        if not thread:
            return None
        
        msg = thread.add_message(role, content)
        self.update(thread)
        return msg
    
    def get_messages(self, thread_id: str) -> List[Message]:
        """Get all messages in a thread."""
        thread = self.get(thread_id)
        if thread:
            return thread.messages
        return []


class RunStore:
    """
    Store for managing runs.
    
    Provides CRUD operations for execution runs.
    """
    
    def __init__(self, backend: Optional[StorageBackend] = None):
        self.backend = backend or InMemoryBackend()
        self._prefix = "run:"
    
    def _key(self, run_id: str) -> str:
        """Generate storage key for run."""
        return f"{self._prefix}{run_id}"
    
    def create(self, run: Run) -> Run:
        """Create a new run."""
        key = self._key(run.id)
        self.backend.put(key, run.to_dict())
        logger.info(f"Created run: {run.id}")
        return run
    
    def get(self, run_id: str) -> Optional[Run]:
        """Get run by ID."""
        key = self._key(run_id)
        data = self.backend.get(key)
        if data:
            return Run.from_dict(data)
        return None
    
    def update(self, run: Run) -> Run:
        """Update an existing run."""
        key = self._key(run.id)
        self.backend.put(key, run.to_dict())
        return run
    
    def delete(self, run_id: str) -> bool:
        """Delete a run."""
        key = self._key(run_id)
        return self.backend.delete(key)
    
    def list_by_thread(self, thread_id: str) -> List[Run]:
        """List runs for a thread."""
        keys = self.backend.list(self._prefix)
        runs = []
        for key in keys:
            data = self.backend.get(key)
            if data and data.get("thread_id") == thread_id:
                runs.append(Run.from_dict(data))
        return runs


# Global store instances
_assistant_store: Optional[AssistantStore] = None
_thread_store: Optional[ThreadStore] = None
_run_store: Optional[RunStore] = None


def get_assistant_store(
    backend: Optional[StorageBackend] = None,
    persist_path: Optional[str] = None
) -> AssistantStore:
    """
    Get or create the global assistant store.
    
    Args:
        backend: Optional custom backend
        persist_path: If provided, use file-based persistence
    
    Returns:
        AssistantStore instance
    """
    global _assistant_store
    
    if _assistant_store is None:
        if persist_path:
            backend = FileBackend(persist_path)
        _assistant_store = AssistantStore(backend)
    
    return _assistant_store


def get_thread_store(
    backend: Optional[StorageBackend] = None,
    persist_path: Optional[str] = None
) -> ThreadStore:
    """
    Get or create the global thread store.
    
    Args:
        backend: Optional custom backend
        persist_path: If provided, use file-based persistence
    
    Returns:
        ThreadStore instance
    """
    global _thread_store
    
    if _thread_store is None:
        if persist_path:
            backend = FileBackend(persist_path)
        _thread_store = ThreadStore(backend)
    
    return _thread_store


def get_run_store(
    backend: Optional[StorageBackend] = None,
    persist_path: Optional[str] = None
) -> RunStore:
    """
    Get or create the global run store.
    
    Args:
        backend: Optional custom backend
        persist_path: If provided, use file-based persistence
    
    Returns:
        RunStore instance
    """
    global _run_store
    
    if _run_store is None:
        if persist_path:
            backend = FileBackend(persist_path)
        _run_store = RunStore(backend)
    
    return _run_store


def reset_stores():
    """Reset all global store instances."""
    global _assistant_store, _thread_store, _run_store
    _assistant_store = None
    _thread_store = None
    _run_store = None

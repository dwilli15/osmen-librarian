from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Tuple
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.base import BaseCheckpointSaver, Checkpoint, CheckpointMetadata, CheckpointTuple

class CustomCheckpointSaver(BaseCheckpointSaver):
    """
    Abstract base class for custom checkpoint savers.
    Wraps LangGraph's BaseCheckpointSaver for future extensibility.
    """
    pass

class InMemorySaver(CustomCheckpointSaver):
    """
    In-memory implementation of checkpoint saver.
    Useful for testing and ephemeral sessions.
    """
    def __init__(self):
        super().__init__()
        self.storage = {}

    def get_tuple(self, config: RunnableConfig) -> Optional[CheckpointTuple]:
        thread_id = config["configurable"]["thread_id"]
        if thread_id not in self.storage:
            return None
        return self.storage[thread_id]

    def list(self, config: Optional[RunnableConfig], *, filter: Optional[Dict[str, Any]] = None, before: Optional[RunnableConfig] = None, limit: Optional[int] = None) -> Any:
        # Simplified list implementation
        return list(self.storage.values())

    def put(self, config: RunnableConfig, checkpoint: Checkpoint, metadata: CheckpointMetadata, new_versions: Dict[str, Any]) -> RunnableConfig:
        thread_id = config["configurable"]["thread_id"]
        self.storage[thread_id] = CheckpointTuple(config, checkpoint, metadata, (checkpoint["id"], 0)) # Mock parent_ts
        return config

    def put_writes(self, config: RunnableConfig, writes: Any, task_id: str) -> None:
        pass # No-op for now

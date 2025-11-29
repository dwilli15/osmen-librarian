"""
Base classes and utilities for Subagents.

Provides:
- SubagentBase: Abstract base class for all subagents
- SubagentConfig: Configuration dataclass
- SubagentResult: Result container
- Lifecycle management
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type
from dataclasses import dataclass, field
from enum import Enum
import uuid
import time
import logging

from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, AIMessage

logger = logging.getLogger("librarian.subagents")


class SubagentStatus(Enum):
    """Status of a subagent execution."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    INTERRUPTED = "interrupted"


@dataclass
class SubagentConfig:
    """Configuration for a subagent."""
    name: str = ""
    prompt: str = ""
    tools: List[str] = field(default_factory=list)
    backend_config: Dict[str, Any] = field(default_factory=dict)
    max_iterations: int = 5
    isolated_memory: bool = True
    isolation_level: str = "isolated"  # for compatibility with tests
    parent_thread_id: Optional[str] = None  # for compatibility with tests
    timeout: Optional[float] = None  # seconds
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SubagentResult:
    """Result from a subagent execution."""
    task_id: str
    subagent_name: str
    status: SubagentStatus
    result: Optional[str] = None
    error: Optional[str] = None
    messages: List[BaseMessage] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    duration_ms: float = 0
    iterations: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "subagent_name": self.subagent_name,
            "status": self.status.value,
            "result": self.result,
            "error": self.error,
            "metadata": self.metadata,
            "duration_ms": self.duration_ms,
            "iterations": self.iterations
        }


class SubagentBase(ABC):
    """
    Abstract base class for subagents.
    
    Subagents are specialized, focused agents that:
    - Run with isolated state/memory
    - Have a specific purpose (fact-checking, lateral thinking, etc.)
    - Return structured results
    - Can be spawned and managed by the parent agent
    """

    name: str = "base"
    description: str = "Base subagent"
    default_tools: List[str] = []

    def __init__(self, config: SubagentConfig):
        self.config = config
        self.task_id = str(uuid.uuid4())[:8]
        self._graph: Optional[StateGraph] = None
        self._compiled = None
        self._checkpointer = None

    @abstractmethod
    def get_system_prompt(self) -> str:
        """Return the system prompt for this subagent."""
        pass

    @abstractmethod
    def build_graph(self) -> StateGraph:
        """Build the subagent's state graph."""
        pass

    def get_tools(self) -> List[str]:
        """Get tools for this subagent."""
        if self.config.tools:
            return self.config.tools
        return self.default_tools

    def compile(self, checkpointer=None):
        """Compile the subagent graph."""
        if self._compiled is None:
            self._graph = self.build_graph()
            compile_kwargs = {}
            if checkpointer and self.config.isolated_memory:
                compile_kwargs["checkpointer"] = checkpointer
                self._checkpointer = checkpointer
            self._compiled = self._graph.compile(**compile_kwargs)
        return self._compiled

    def run(
        self,
        input_data: Dict[str, Any],
        checkpointer=None
    ) -> SubagentResult:
        """
        Execute the subagent.
        
        Args:
            input_data: Initial state/input for the subagent
            checkpointer: Optional checkpointer for state persistence
        
        Returns:
            SubagentResult with execution outcome
        """
        start_time = time.time()
        
        try:
            logger.info(f"[{self.name}:{self.task_id}] Starting execution")
            
            graph = self.compile(checkpointer)
            
            # Run the graph
            config = {}
            if self._checkpointer:
                config["configurable"] = {
                    "thread_id": f"{self.name}:{self.task_id}"
                }
            
            final_state = graph.invoke(input_data, config=config)
            
            duration_ms = (time.time() - start_time) * 1000
            
            # Extract result from final state
            result_text = self._extract_result(final_state)
            
            logger.info(
                f"[{self.name}:{self.task_id}] Completed in {duration_ms:.0f}ms"
            )
            
            return SubagentResult(
                task_id=self.task_id,
                subagent_name=self.name,
                status=SubagentStatus.COMPLETED,
                result=result_text,
                messages=final_state.get("messages", []),
                metadata=final_state.get("metadata", {}),
                duration_ms=duration_ms,
                iterations=final_state.get("iteration", 0)
            )
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(f"[{self.name}:{self.task_id}] Failed: {e}")
            
            return SubagentResult(
                task_id=self.task_id,
                subagent_name=self.name,
                status=SubagentStatus.FAILED,
                error=str(e),
                duration_ms=duration_ms
            )

    def _extract_result(self, final_state: Dict[str, Any]) -> str:
        """Extract result string from final state."""
        # Try common result fields
        if "result" in final_state:
            return str(final_state["result"])
        if "answer" in final_state:
            return str(final_state["answer"])
        if "output" in final_state:
            return str(final_state["output"])
        
        # Try last message
        messages = final_state.get("messages", [])
        if messages:
            last_msg = messages[-1]
            if hasattr(last_msg, "content"):
                return str(last_msg.content)
        
        return "No result extracted"


# =============================================================================
# Registry and Factory
# =============================================================================

_SUBAGENT_REGISTRY: Dict[str, Type[SubagentBase]] = {}

# Alias for tests to access registry directly
SUBAGENT_REGISTRY = _SUBAGENT_REGISTRY


def register_subagent(name: str):
    """Decorator to register a subagent class."""
    def decorator(cls: Type[SubagentBase]):
        _SUBAGENT_REGISTRY[name] = cls
        cls.name = name
        return cls
    return decorator


def create_subagent(name: str, config: SubagentConfig) -> SubagentBase:
    """Create a subagent instance by name."""
    if name not in _SUBAGENT_REGISTRY:
        available = ", ".join(_SUBAGENT_REGISTRY.keys())
        raise ValueError(f"Unknown subagent: {name}. Available: {available}")
    
    return _SUBAGENT_REGISTRY[name](config)


def get_registered_subagents() -> List[str]:
    """Get list of registered subagent names."""
    return list(_SUBAGENT_REGISTRY.keys())

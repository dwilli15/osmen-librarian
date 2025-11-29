"""
Subagents Module for Librarian Agent.

Provides spawnable, instrumented subagent graphs:
- FactChecker: Verify claims against source documents
- LateralResearcher: Find creative cross-domain connections
- Summarizer: Synthesize document summaries
- Executor: Execute file operations and commands

Each subagent:
- Runs as an isolated graph
- Has its own memory/checkpointer
- Reports via structured results
"""

from .base import (
    SubagentBase,
    SubagentConfig,
    SubagentResult,
    SubagentStatus,
    create_subagent,
    register_subagent
)
from .fact_checker import FactCheckerSubagent
from .lateral_researcher import LateralResearcherSubagent
from .summarizer import SummarizerSubagent
from .executor import ExecutorSubagent

__all__ = [
    "SubagentBase",
    "SubagentConfig",
    "SubagentResult",
    "SubagentStatus",
    "create_subagent",
    "register_subagent",
    "FactCheckerSubagent",
    "LateralResearcherSubagent",
    "SummarizerSubagent",
    "ExecutorSubagent",
]

# Registry of available subagents
SUBAGENT_REGISTRY = {
    "fact_checker": FactCheckerSubagent,
    "lateral_researcher": LateralResearcherSubagent,
    "summarizer": SummarizerSubagent,
    "executor": ExecutorSubagent,
}


def get_available_subagents():
    """Get list of registered subagent names."""
    return list(SUBAGENT_REGISTRY.keys())


def spawn_subagent(name: str, config: SubagentConfig) -> "SubagentBase":
    """
    Spawn a subagent by name.
    
    Args:
        name: Registered subagent name
        config: Subagent configuration
    
    Returns:
        Instantiated subagent
    """
    if name not in SUBAGENT_REGISTRY:
        raise ValueError(f"Unknown subagent: {name}. Available: {list(SUBAGENT_REGISTRY.keys())}")
    
    subagent_class = SUBAGENT_REGISTRY[name]
    return subagent_class(config)

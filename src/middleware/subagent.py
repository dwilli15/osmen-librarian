from typing import List
from langchain_core.tools import Tool
from .base import BaseMiddleware

class SubAgentMiddleware(BaseMiddleware):
    """Middleware for spawning subagents."""

    def spawn_subagent(self, name: str, task: str) -> str:
        """Spawns a subagent to handle a specific task."""
        # This is where the complex logic of pausing the main graph and invoking a subgraph would go.
        # For Phase 2, we mock this interaction.
        print(f"--- Spawning Subagent: {name} for task: {task} ---")
        return f"Subagent {name} spawned. Result: [Mock Result for '{task}']"

    def register_tools(self) -> List[Tool]:
        return [
            Tool(name="spawn_subagent", func=self.spawn_subagent, description="Spawn a subagent (fact_checker, lateral_researcher) for a task")
        ]

from typing import List
from langchain_core.tools import Tool
from langgraph.errors import GraphInterrupt
from .base import BaseMiddleware

class HITLMiddleware(BaseMiddleware):
    """Middleware for Human-in-the-Loop interactions."""

    def request_approval(self, action: str) -> str:
        """Pauses execution to request human approval."""
        print(f"--- HITL: Requesting approval for '{action}' ---")
        # In LangGraph, raising GraphInterrupt pauses the graph.
        # The value passed to GraphInterrupt is available to the client.
        raise GraphInterrupt(f"Approval required for: {action}")

    def register_tools(self) -> List[Tool]:
        return [
            Tool(name="request_approval", func=self.request_approval, description="Request human approval for a critical action")
        ]

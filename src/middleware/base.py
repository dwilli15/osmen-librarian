from abc import ABC, abstractmethod
from typing import List, Any
from langchain_core.tools import Tool

class BaseMiddleware(ABC):
    """Base class for all middleware components."""
    
    @abstractmethod
    def register_tools(self) -> List[Tool]:
        """Returns a list of tools to be registered with the agent."""
        pass

    def on_step_start(self, state: Any):
        """Hook called before a graph step execution."""
        pass

    def on_step_end(self, state: Any):
        """Hook called after a graph step execution."""
        pass

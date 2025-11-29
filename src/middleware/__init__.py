"""
Middleware System for Librarian Agent.

Provides extensible middleware architecture for:
- Tool registration and lifecycle management
- Prompt injection and patching
- State manipulation
- HITL (Human-in-the-Loop) interrupts
- Backend selection and routing
"""

from .base import (
    AgentMiddleware,
    BaseMiddleware,
    MiddlewareChain,
    MiddlewareStack,
    MiddlewareContext,
)
from .filesystem import FilesystemMiddleware
from .todo import TodoMiddleware, TodoListMiddleware
from .subagent import SubagentMiddleware, SubAgentMiddleware
from .hitl import HITLMiddleware

__all__ = [
    "AgentMiddleware",
    "BaseMiddleware",
    "MiddlewareChain",
    "MiddlewareStack",
    "MiddlewareContext",
    "FilesystemMiddleware",
    "TodoMiddleware",
    "TodoListMiddleware",
    "SubagentMiddleware",
    "SubAgentMiddleware",
    "HITLMiddleware",
]

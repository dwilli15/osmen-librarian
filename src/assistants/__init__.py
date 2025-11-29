"""
Assistants Module for Librarian Agent.

Provides OpenAI Assistants API-compatible abstractions:
- Assistant definitions (configurable presets)
- Thread management (conversation persistence)
- Run execution (graph invocations)

Patterns from:
- opengpts: Assistant/Thread/Run model
- langchain: Runnable interface
"""

from .schema import (
    Assistant,
    Thread,
    Run,
    Message,
    MessageRole,
    AssistantConfig,
    RunStatus,
)
from .storage import (
    AssistantStore,
    ThreadStore,
    get_assistant_store,
    get_thread_store,
)

__all__ = [
    "Assistant",
    "Thread",
    "Run",
    "Message",
    "MessageRole",
    "AssistantConfig",
    "RunStatus",
    "AssistantStore",
    "ThreadStore",
    "get_assistant_store",
    "get_thread_store",
]

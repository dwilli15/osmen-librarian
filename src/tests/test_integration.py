"""
Integration Tests for Librarian Agent.

These tests verify end-to-end functionality.
Run with: pytest tests/test_integration.py -v
"""

import pytest
import tempfile
import os


class TestGraphIntegration:
    """Integration tests for LangGraph agent."""
    
    def test_graph_compilation(self):
        """Test graph compiles successfully."""
        try:
            from graph import build_librarian_graph
            
            graph = build_librarian_graph()
            assert graph is not None
        except ImportError as e:
            pytest.skip(f"Graph module not available: {e}")
    
    def test_graph_with_checkpointer(self):
        """Test graph compilation with checkpointer."""
        try:
            from graph import compile_graph
            
            graph = compile_graph(checkpointer_type="memory")
            assert graph is not None
        except ImportError as e:
            pytest.skip(f"Graph module not available: {e}")


class TestTracingIntegration:
    """Integration tests for tracing module."""
    
    def test_traceable_decorator(self):
        """Test @traceable decorator works."""
        from tracing import traceable
        
        @traceable(name="test_function")
        def test_func(x, y):
            return x + y
        
        result = test_func(1, 2)
        assert result == 3
    
    def test_tracer_initialization(self):
        """Test tracer initializes from env."""
        from tracing import get_tracer, TracingConfig
        
        config = TracingConfig(backend="console")
        tracer = get_tracer(config)
        
        assert tracer is not None
    
    def test_span_lifecycle(self):
        """Test span start/end lifecycle."""
        from tracing import TracingConfig, ConsoleTracer
        
        tracer = ConsoleTracer(TracingConfig())
        
        span_id = tracer.start_span("test_span", inputs={"key": "value"})
        assert span_id is not None
        
        tracer.end_span(span_id, outputs={"result": "success"})
        
        # Verify span was removed from active spans
        assert span_id not in tracer._spans


class TestMemoryIntegration:
    """Integration tests for memory module."""
    
    def test_checkpointer_factory(self):
        """Test get_checkpointer returns correct type."""
        from memory import get_checkpointer
        
        checkpointer = get_checkpointer(backend="memory")
        
        assert checkpointer is not None
    
    def test_memory_persistence(self):
        """Test memory checkpointer persistence."""
        from memory import get_checkpointer, CheckpointConfig
        
        checkpointer = get_checkpointer(backend="memory")
        
        # Create a checkpoint
        config = CheckpointConfig(thread_id="test_thread")
        checkpoint = checkpointer.create_checkpoint(
            config=config,
            state={"messages": ["hello"]},
            metadata={"step": 1}
        )
        
        # Retrieve it
        retrieved = checkpointer.get(config)
        assert retrieved is not None
        assert retrieved.state["messages"] == ["hello"]


class TestStoreIntegration:
    """Integration tests for store module."""
    
    def test_composite_store(self):
        """Test CompositeStore routing."""
        from store import CompositeStore, StorageRoute
        
        store = CompositeStore()
        assert store is not None
    
    def test_store_put_get(self):
        """Test store put/get operations."""
        from store import CompositeStore
        
        store = CompositeStore()
        
        # Put a value using namespace and key
        store.put("/tmp", "test_key", {"data": "value"})
        
        # Get it back
        result = store.get("/tmp", "test_key")
        assert result is not None
        assert result.value == {"data": "value"}


class TestEndToEndWorkflow:
    """End-to-end workflow tests."""
    
    def test_assistant_thread_workflow(self):
        """Test complete assistant -> thread -> message workflow."""
        from assistants import (
            AssistantStore,
            ThreadStore,
            Assistant,
            Thread,
            MessageRole
        )
        from assistants.storage import InMemoryBackend
        
        # Create stores with fresh backends
        asst_store = AssistantStore(InMemoryBackend())
        thread_store = ThreadStore(InMemoryBackend())
        
        # Create assistant
        assistant = asst_store.create(Assistant(name="Test Assistant"))
        
        # Create thread
        thread = Thread(assistant_id=assistant.id)
        thread_store.create(thread)
        
        # Add messages
        thread_store.add_message(thread.id, MessageRole.USER, "Hello")
        thread_store.add_message(thread.id, MessageRole.ASSISTANT, "Hi there!")
        
        # Verify
        messages = thread_store.get_messages(thread.id)
        assert len(messages) == 2
        assert messages[0].role == MessageRole.USER
        assert messages[1].role == MessageRole.ASSISTANT
    
    def test_middleware_integration(self):
        """Test middleware stack integration."""
        from middleware.base import MiddlewareStack
        from middleware.todo import TodoMiddleware
        from middleware.filesystem import FilesystemMiddleware
        
        stack = MiddlewareStack()
        stack.add(TodoMiddleware({}))
        stack.add(FilesystemMiddleware({"root_dir": "."}))
        
        tools = stack.get_all_tools()
        
        # Should have tools from both middleware
        assert len(tools) > 0
    
    def test_subagent_spawning(self):
        """Test subagent can be spawned and configured."""
        from subagents import spawn_subagent, get_available_subagents
        from subagents.base import SubagentConfig
        
        available = get_available_subagents()
        assert len(available) >= 4
        
        config = SubagentConfig(parent_thread_id="test_thread")
        agent = spawn_subagent("fact_checker", config)
        
        assert agent is not None
        assert agent.config.parent_thread_id == "test_thread"


class TestModuleImports:
    """Test all modules can be imported."""
    
    def test_import_graph(self):
        """Test graph module imports."""
        try:
            from graph import AgentState, build_librarian_graph, compile_graph
            assert True
        except ImportError as e:
            pytest.skip(f"Dependency not installed: {e}")
    
    def test_import_middleware(self):
        """Test middleware module imports."""
        from middleware import (
            AgentMiddleware,
            MiddlewareStack,
            FilesystemMiddleware,
            TodoMiddleware,
            SubagentMiddleware,
            HITLMiddleware
        )
        assert AgentMiddleware is not None
    
    def test_import_subagents(self):
        """Test subagents module imports."""
        from subagents import (
            SubagentBase,
            SubagentConfig,
            SubagentResult,
            create_subagent,
            get_available_subagents
        )
        assert SubagentBase is not None
    
    def test_import_retrieval(self):
        """Test retrieval module imports."""
        from retrieval import (
            RetrieverBase,
            RetrieverConfig,
            RetrievalResult,
            DocumentChunk,
            ChromaRetriever
        )
        assert RetrieverBase is not None
    
    def test_import_assistants(self):
        """Test assistants module imports."""
        from assistants import (
            Assistant,
            Thread,
            Run,
            Message,
            AssistantConfig,
            RunStatus
        )
        assert Assistant is not None
    
    def test_import_tracing(self):
        """Test tracing module imports."""
        from tracing import (
            traceable,
            get_tracer,
            setup_tracing,
            TracingConfig,
            ConsoleTracer
        )
        assert traceable is not None
    
    def test_import_memory(self):
        """Test memory module imports."""
        from memory import get_checkpointer, MemoryConfig
        assert get_checkpointer is not None
    
    def test_import_store(self):
        """Test store module imports."""
        from store import CompositeStore, StorageRoute
        assert CompositeStore is not None

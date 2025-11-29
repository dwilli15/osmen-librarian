"""
Tests for Assistants Module.
"""

import pytest
from datetime import datetime


class TestAssistantSchema:
    """Tests for Assistant schema."""
    
    def test_assistant_creation(self):
        """Test Assistant dataclass creation."""
        from assistants.schema import Assistant
        
        assistant = Assistant(
            name="Test Assistant",
            instructions="Be helpful"
        )
        
        assert assistant.name == "Test Assistant"
        assert assistant.id.startswith("asst_")
        assert assistant.instructions == "Be helpful"
    
    def test_assistant_config_defaults(self):
        """Test AssistantConfig default values."""
        from assistants.schema import AssistantConfig
        
        config = AssistantConfig()
        
        assert config.model == "gpt-4o"
        assert config.name == "Librarian"
        assert config.id.startswith("asst_")
    
    def test_assistant_serialization(self):
        """Test Assistant to_dict/from_dict."""
        from assistants.schema import Assistant
        
        original = Assistant(name="Test", instructions="Instructions")
        data = original.to_dict()
        restored = Assistant.from_dict(data)
        
        assert restored.name == original.name
        assert restored.id == original.id
        assert restored.instructions == original.instructions


class TestThreadSchema:
    """Tests for Thread schema."""
    
    def test_thread_creation(self):
        """Test Thread dataclass creation."""
        from assistants.schema import Thread
        
        thread = Thread()
        
        assert thread.id.startswith("thread_")
        assert thread.messages == []
    
    def test_thread_add_message(self):
        """Test adding messages to thread."""
        from assistants.schema import Thread, MessageRole
        
        thread = Thread()
        msg = thread.add_message(MessageRole.USER, "Hello")
        
        assert len(thread.messages) == 1
        assert thread.messages[0].content == "Hello"
        assert msg.role == MessageRole.USER
    
    def test_thread_serialization(self):
        """Test Thread to_dict/from_dict."""
        from assistants.schema import Thread, MessageRole
        
        original = Thread()
        original.add_message(MessageRole.USER, "Test message")
        
        data = original.to_dict()
        restored = Thread.from_dict(data)
        
        assert restored.id == original.id
        assert len(restored.messages) == 1
        assert restored.messages[0].content == "Test message"


class TestRunSchema:
    """Tests for Run schema."""
    
    def test_run_creation(self):
        """Test Run dataclass creation."""
        from assistants.schema import Run, RunStatus
        
        run = Run(thread_id="thread_123", assistant_id="asst_456")
        
        assert run.id.startswith("run_")
        assert run.status == RunStatus.QUEUED
        assert run.thread_id == "thread_123"
    
    def test_run_lifecycle(self):
        """Test Run status transitions."""
        from assistants.schema import Run, RunStatus
        
        run = Run(thread_id="t1", assistant_id="a1")
        
        # Start
        run.start()
        assert run.status == RunStatus.IN_PROGRESS
        assert run.started_at is not None
        
        # Complete
        run.complete()
        assert run.status == RunStatus.COMPLETED
        assert run.completed_at is not None
    
    def test_run_failure(self):
        """Test Run failure handling."""
        from assistants.schema import Run, RunStatus
        
        run = Run(thread_id="t1", assistant_id="a1")
        run.start()
        run.fail("Error message")
        
        assert run.status == RunStatus.FAILED
        assert run.error == "Error message"
    
    def test_run_duration(self):
        """Test Run duration calculation."""
        from assistants.schema import Run
        import time
        
        run = Run(thread_id="t1", assistant_id="a1")
        run.start()
        time.sleep(0.01)  # Small delay
        run.complete()
        
        duration = run.get_duration()
        assert duration is not None
        assert duration > 0


class TestAssistantStore:
    """Tests for AssistantStore."""
    
    def test_create_and_get(self):
        """Test creating and retrieving assistant."""
        from assistants.storage import AssistantStore, InMemoryBackend
        from assistants.schema import Assistant
        
        backend = InMemoryBackend()
        store = AssistantStore(backend)
        
        assistant = Assistant(name="Test")
        created = store.create(assistant)
        
        retrieved = store.get(created.id)
        assert retrieved is not None
        assert retrieved.name == "Test"
    
    def test_list_assistants(self):
        """Test listing assistants."""
        from assistants.storage import AssistantStore, InMemoryBackend
        from assistants.schema import Assistant
        
        backend = InMemoryBackend()
        store = AssistantStore(backend)
        
        store.create(Assistant(name="Asst1"))
        store.create(Assistant(name="Asst2"))
        
        all_assistants = store.list()
        assert len(all_assistants) == 2
    
    def test_delete_assistant(self):
        """Test deleting assistant."""
        from assistants.storage import AssistantStore, InMemoryBackend
        from assistants.schema import Assistant
        
        backend = InMemoryBackend()
        store = AssistantStore(backend)
        
        assistant = store.create(Assistant(name="ToDelete"))
        assert store.get(assistant.id) is not None
        
        store.delete(assistant.id)
        assert store.get(assistant.id) is None


class TestThreadStore:
    """Tests for ThreadStore."""
    
    def test_create_thread(self):
        """Test creating thread."""
        from assistants.storage import ThreadStore, InMemoryBackend
        from assistants.schema import Thread
        
        backend = InMemoryBackend()
        store = ThreadStore(backend)
        
        thread = store.create()
        assert thread is not None
        assert thread.id.startswith("thread_")
    
    def test_add_message_to_thread(self):
        """Test adding message via store."""
        from assistants.storage import ThreadStore, InMemoryBackend
        from assistants.schema import MessageRole
        
        backend = InMemoryBackend()
        store = ThreadStore(backend)
        
        thread = store.create()
        msg = store.add_message(thread.id, MessageRole.USER, "Hello")
        
        assert msg is not None
        
        # Verify persisted
        retrieved = store.get(thread.id)
        assert len(retrieved.messages) == 1
    
    def test_get_messages(self):
        """Test getting messages from thread."""
        from assistants.storage import ThreadStore, InMemoryBackend
        from assistants.schema import MessageRole
        
        backend = InMemoryBackend()
        store = ThreadStore(backend)
        
        thread = store.create()
        store.add_message(thread.id, MessageRole.USER, "Message 1")
        store.add_message(thread.id, MessageRole.ASSISTANT, "Message 2")
        
        messages = store.get_messages(thread.id)
        assert len(messages) == 2


class TestPresetAssistants:
    """Tests for preset assistants."""
    
    def test_preset_assistants_exist(self):
        """Test preset assistants are defined."""
        from assistants.schema import PRESET_ASSISTANTS
        
        assert "librarian" in PRESET_ASSISTANTS
        assert "researcher" in PRESET_ASSISTANTS
        assert "analyst" in PRESET_ASSISTANTS
    
    def test_preset_configs(self):
        """Test preset assistant configurations."""
        from assistants.schema import PRESET_ASSISTANTS, AssistantConfig
        
        librarian = PRESET_ASSISTANTS["librarian"]
        assert isinstance(librarian, AssistantConfig)
        assert librarian.name == "Librarian"
        assert "query_library" in librarian.tools
        
        researcher = PRESET_ASSISTANTS["researcher"]
        assert researcher.name == "Researcher"

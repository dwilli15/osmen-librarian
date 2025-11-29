"""
Tests for Middleware System.
"""

import pytest
from unittest.mock import MagicMock, patch
import tempfile
import os


class TestMiddlewareBase:
    """Tests for AgentMiddleware base class."""
    
    def test_middleware_registration(self):
        """Test middleware can be registered in stack."""
        from middleware.base import BaseMiddleware, MiddlewareStack
        from langchain_core.tools import Tool
        
        class TestMiddleware(BaseMiddleware):
            def register_tools(self):
                return [
                    Tool(
                        name="test_tool",
                        func=lambda x: x,
                        description="A test tool"
                    )
                ]
        
        stack = MiddlewareStack()
        mw = TestMiddleware()
        stack.add(mw)
        
        assert len(stack) == 1
    
    def test_middleware_stack_composition(self):
        """Test middleware stack composes tools."""
        from middleware.base import BaseMiddleware, MiddlewareStack
        from langchain_core.tools import Tool
        
        class MW1(BaseMiddleware):
            def register_tools(self):
                return [Tool(name="tool1", func=lambda: 1, description="T1")]
        
        class MW2(BaseMiddleware):
            def register_tools(self):
                return [Tool(name="tool2", func=lambda: 2, description="T2")]
        
        stack = MiddlewareStack()
        stack.add(MW1())
        stack.add(MW2())
        
        tools = stack.get_all_tools()
        tool_names = [t.name for t in tools]
        
        assert "tool1" in tool_names
        assert "tool2" in tool_names


class TestFilesystemMiddleware:
    """Tests for FilesystemMiddleware."""
    
    def test_ls_tool(self):
        """Test directory listing."""
        from middleware.filesystem import FilesystemMiddleware
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files
            open(os.path.join(tmpdir, "test1.txt"), "w").close()
            open(os.path.join(tmpdir, "test2.txt"), "w").close()
            
            mw = FilesystemMiddleware(root_dir=tmpdir)
            tools = mw.register_tools()
            
            # Find ls tool
            ls_tool = next((t for t in tools if t.name == "fs_ls"), None)
            assert ls_tool is not None
            
            # Test it works
            result = mw.list_files(".")
            assert "test1.txt" in result
            assert "test2.txt" in result
    
    def test_sandbox_enforcement(self):
        """Test sandbox prevents access outside root."""
        from middleware.filesystem import FilesystemMiddleware
        
        with tempfile.TemporaryDirectory() as tmpdir:
            mw = FilesystemMiddleware(root_dir=tmpdir)
            
            # Try to escape sandbox - should raise error
            with pytest.raises(ValueError) as exc_info:
                mw._validate_path("../../../etc/passwd")
            
            assert "Access denied" in str(exc_info.value)


class TestTodoMiddleware:
    """Tests for TodoMiddleware."""
    
    def test_write_todos(self):
        """Test writing todos."""
        from middleware.todo import TodoMiddleware
        
        mw = TodoMiddleware({})
        
        # Add a todo
        result = mw.add_todo("Test task")
        assert "TODO ADDED" in result
        
        # List todos
        list_result = mw.list_todos()
        assert "Test task" in list_result
    
    def test_prompt_injection(self):
        """Test todo list injects into prompt."""
        from middleware.todo import TodoMiddleware
        
        mw = TodoMiddleware({})
        mw.add_todo("Important task")
        
        prompt = mw.get_prompt_injection()
        assert "Important task" in prompt


class TestSubagentMiddleware:
    """Tests for SubagentMiddleware."""
    
    def test_task_tool_available(self):
        """Test task() tool is available."""
        from middleware.subagent import SubagentMiddleware
        
        mw = SubagentMiddleware({})
        tools = mw.register_tools()
        
        task_tool = next((t for t in tools if t.name == "task"), None)
        assert task_tool is not None


class TestHITLMiddleware:
    """Tests for HITLMiddleware."""
    
    def test_interrupt_config(self):
        """Test interrupt configuration."""
        from middleware.hitl import HITLMiddleware
        
        config = {"interrupt_patterns": ["delete", "execute"]}
        mw = HITLMiddleware(config)
        
        assert "delete" in mw.interrupt_patterns
        assert "execute" in mw.interrupt_patterns
    
    def test_should_interrupt(self):
        """Test interrupt decision."""
        from middleware.hitl import HITLMiddleware
        
        config = {"interrupt_patterns": ["delete", "execute"]}
        mw = HITLMiddleware(config)
        
        # Should interrupt on delete
        assert mw.should_interrupt("delete file") is True
        # Should not interrupt on read
        assert mw.should_interrupt("read file") is False

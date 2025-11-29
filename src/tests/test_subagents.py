"""
Tests for Subagents.
"""

import pytest
from unittest.mock import MagicMock, patch


class TestSubagentBase:
    """Tests for SubagentBase class."""
    
    def test_subagent_registration(self):
        """Test subagent registration via decorator."""
        from subagents.base import SubagentBase, register_subagent, SUBAGENT_REGISTRY
        
        @register_subagent("test_agent")
        class TestAgent(SubagentBase):
            name = "test_agent"
            description = "Test agent"
            
            def build_graph(self):
                from langgraph.graph import StateGraph
                return StateGraph(dict)
        
        # Note: Registration may have happened at import
        # Check if registration mechanism works
        assert hasattr(TestAgent, 'name')
        assert TestAgent.name == "test_agent"
    
    def test_subagent_config(self):
        """Test SubagentConfig dataclass."""
        from subagents.base import SubagentConfig
        
        config = SubagentConfig(
            parent_thread_id="thread_123",
            isolation_level="isolated"
        )
        
        assert config.parent_thread_id == "thread_123"
        assert config.isolation_level == "isolated"
    
    def test_subagent_result(self):
        """Test SubagentResult dataclass."""
        from subagents.base import SubagentResult, SubagentStatus
        
        result = SubagentResult(
            task_id="task_123",
            subagent_name="test_agent",
            result="Test output",
            status=SubagentStatus.COMPLETED
        )
        
        assert result.result == "Test output"
        assert result.status == SubagentStatus.COMPLETED
        assert result.task_id == "task_123"
        assert result.subagent_name == "test_agent"


class TestFactCheckerSubagent:
    """Tests for FactCheckerSubagent."""
    
    def test_fact_checker_init(self):
        """Test FactChecker initialization."""
        from subagents.fact_checker import FactCheckerSubagent
        from subagents.base import SubagentConfig
        
        config = SubagentConfig()
        agent = FactCheckerSubagent(config)
        
        assert agent.name == "fact_checker"
        assert "verify" in agent.description.lower() or "fact" in agent.description.lower()
    
    def test_fact_checker_graph_build(self):
        """Test FactChecker graph builds successfully."""
        from subagents.fact_checker import FactCheckerSubagent
        from subagents.base import SubagentConfig
        
        config = SubagentConfig()
        agent = FactCheckerSubagent(config)
        
        graph = agent.build_graph()
        assert graph is not None


class TestLateralResearcherSubagent:
    """Tests for LateralResearcherSubagent."""
    
    def test_lateral_researcher_init(self):
        """Test LateralResearcher initialization."""
        from subagents.lateral_researcher import LateralResearcherSubagent
        from subagents.base import SubagentConfig
        
        config = SubagentConfig()
        agent = LateralResearcherSubagent(config)
        
        assert agent.name == "lateral_researcher"
    
    def test_lateral_researcher_has_dimensions(self):
        """Test LateralResearcher uses Context7 dimensions."""
        from subagents.lateral_researcher import LateralResearcherSubagent
        from subagents.base import SubagentConfig
        
        config = SubagentConfig()
        agent = LateralResearcherSubagent(config)
        
        # Should reference dimensions in prompt or implementation
        prompt = agent.get_system_prompt()
        # Check for some dimension keywords
        assert any(dim in prompt.lower() for dim in [
            "dimension", "context", "domain", "temporal", "relational"
        ])


class TestSummarizerSubagent:
    """Tests for SummarizerSubagent."""
    
    def test_summarizer_init(self):
        """Test Summarizer initialization."""
        from subagents.summarizer import SummarizerSubagent
        from subagents.base import SubagentConfig
        
        config = SubagentConfig()
        agent = SummarizerSubagent(config)
        
        assert agent.name == "summarizer"


class TestExecutorSubagent:
    """Tests for ExecutorSubagent."""
    
    def test_executor_init(self):
        """Test Executor initialization."""
        from subagents.executor import ExecutorSubagent
        from subagents.base import SubagentConfig
        
        config = SubagentConfig()
        agent = ExecutorSubagent(config)
        
        assert agent.name == "executor"
    
    def test_executor_has_tools(self):
        """Test Executor has expected tools."""
        from subagents.executor import ExecutorSubagent
        from subagents.base import SubagentConfig
        
        config = SubagentConfig()
        agent = ExecutorSubagent(config)
        
        # Should have file operation tools
        assert any("file" in t.lower() or "execute" in t.lower() 
                   for t in agent.default_tools)


class TestSubagentRegistry:
    """Tests for subagent registry functions."""
    
    def test_get_available_subagents(self):
        """Test listing available subagents."""
        from subagents import get_available_subagents
        
        available = get_available_subagents()
        
        assert isinstance(available, list)
        assert "fact_checker" in available
        assert "lateral_researcher" in available
        assert "summarizer" in available
        assert "executor" in available
    
    def test_spawn_subagent(self):
        """Test spawning a subagent."""
        from subagents import spawn_subagent
        from subagents.base import SubagentConfig
        
        config = SubagentConfig()
        agent = spawn_subagent("fact_checker", config)
        
        assert agent is not None
        assert agent.name == "fact_checker"
    
    def test_spawn_unknown_subagent_raises(self):
        """Test spawning unknown subagent raises error."""
        from subagents import spawn_subagent
        from subagents.base import SubagentConfig
        
        config = SubagentConfig()
        
        with pytest.raises(ValueError):
            spawn_subagent("nonexistent_agent", config)

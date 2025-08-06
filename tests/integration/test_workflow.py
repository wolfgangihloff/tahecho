"""
Integration tests for LangGraph workflow.
"""

from unittest.mock import Mock, patch

import pytest

from tahecho.agents.langgraph_workflow import LangGraphWorkflow
from tahecho.agents.state import create_initial_state


class TestLangGraphWorkflow:
    """Test LangGraph workflow integration."""

    @patch("agents.langgraph_workflow.ChatOpenAI")
    @patch("agents.langgraph_workflow.MemorySaver")
    def test_workflow_initialization(self, mock_memory, mock_chat_openai):
        """Test workflow initialization."""
        # Arrange
        mock_llm = Mock()
        mock_chat_openai.return_value = mock_llm
        mock_memory_instance = Mock()
        mock_memory.return_value = mock_memory_instance

        # Act
        workflow = LangGraphWorkflow()

        # Assert
        assert workflow.llm is not None
        assert workflow.workflow is not None
        assert workflow.memory is not None
        assert workflow.app is not None

    @patch("agents.langgraph_workflow.ChatOpenAI")
    @patch("agents.langgraph_workflow.MemorySaver")
    @patch("agents.task_classifier.task_classifier")
    @patch("agents.langchain_mcp_agent.langchain_mcp_agent")
    def test_workflow_mcp_execution(
        self, mock_mcp_agent, mock_classifier, mock_memory, mock_chat_openai
    ):
        """Test workflow execution for MCP tasks."""
        # Arrange
        mock_llm = Mock()
        mock_chat_openai.return_value = mock_llm
        mock_memory_instance = Mock()
        mock_memory.return_value = mock_memory_instance

        # Mock task classifier
        mock_classifier_instance = Mock()
        mock_classifier_instance.classify_task.return_value = create_initial_state(
            "test"
        )
        mock_classifier_instance.classify_task.return_value.task_type = "mcp"
        mock_classifier.return_value = mock_classifier_instance

        # Mock MCP agent
        mock_mcp_instance = Mock()
        mock_mcp_instance.execute.return_value = create_initial_state("test")
        mock_mcp_instance.execute.return_value.agent_results = {
            "mcp_agent": "MCP result"
        }
        mock_mcp_instance.execute.return_value.final_answer = "Final MCP result"
        mock_mcp_agent.return_value = mock_mcp_instance

        # Mock final response generation
        mock_llm.invoke.return_value.content = "Final response"

        workflow = LangGraphWorkflow()

        # Act
        result = workflow.execute("Show me all open bugs", "test_conv")

        # Assert
        assert result is not None
        assert "Final response" in result

    # Graph agent test removed - functionality disabled

    @patch("agents.langgraph_workflow.ChatOpenAI")
    @patch("agents.langgraph_workflow.MemorySaver")
    @patch("agents.task_classifier.task_classifier")
    def test_workflow_general_execution(
        self, mock_classifier, mock_memory, mock_chat_openai
    ):
        """Test workflow execution for general tasks."""
        # Arrange
        mock_llm = Mock()
        mock_chat_openai.return_value = mock_llm
        mock_memory_instance = Mock()
        mock_memory.return_value = mock_memory_instance

        # Mock task classifier
        mock_classifier_instance = Mock()
        mock_classifier_instance.classify_task.return_value = create_initial_state(
            "test"
        )
        mock_classifier_instance.classify_task.return_value.task_type = "general"
        mock_classifier.return_value = mock_classifier_instance

        # Mock final response generation
        mock_llm.invoke.return_value.content = "General response"

        workflow = LangGraphWorkflow()

        # Act
        result = workflow.execute("Hello, how are you?", "test_conv")

        # Assert
        assert result is not None
        assert "General response" in result

    @patch("agents.langgraph_workflow.ChatOpenAI")
    @patch("agents.langgraph_workflow.MemorySaver")
    def test_workflow_error_handling(self, mock_memory, mock_chat_openai):
        """Test workflow error handling."""
        # Arrange
        mock_llm = Mock()
        mock_chat_openai.return_value = mock_llm
        mock_memory_instance = Mock()
        mock_memory.return_value = mock_memory_instance

        # Mock workflow to raise exception
        mock_app = Mock()
        mock_app.invoke.side_effect = Exception("Workflow error")
        mock_memory_instance.compile.return_value = mock_app

        workflow = LangGraphWorkflow()
        workflow.app = mock_app

        # Act
        result = workflow.execute("Test input", "test_conv")

        # Assert
        assert "Workflow execution failed" in result

    @patch("agents.langgraph_workflow.ChatOpenAI")
    @patch("agents.langgraph_workflow.MemorySaver")
    def test_workflow_conversation_persistence(self, mock_memory, mock_chat_openai):
        """Test that conversation state is persisted."""
        # Arrange
        mock_llm = Mock()
        mock_chat_openai.return_value = mock_llm
        mock_memory_instance = Mock()
        mock_memory.return_value = mock_memory_instance

        # Mock app to return state with conversation ID
        mock_app = Mock()
        mock_result = Mock()
        mock_result.final_answer = "Test response"
        mock_app.invoke.return_value = mock_result
        mock_memory_instance.compile.return_value = mock_app

        workflow = LangGraphWorkflow()
        workflow.app = mock_app

        conversation_id = "persistent_conv_123"

        # Act
        result = workflow.execute("Test input", conversation_id)

        # Assert
        assert result == "Test response"
        # Verify that the conversation ID was passed to the workflow
        mock_app.invoke.assert_called_once()
        call_args = mock_app.invoke.call_args
        assert call_args[1]["config"]["configurable"]["thread_id"] == conversation_id


class TestWorkflowRouting:
    """Test workflow routing logic."""

    @patch("agents.langgraph_workflow.ChatOpenAI")
    @patch("agents.langgraph_workflow.MemorySaver")
    def test_should_continue_mcp(self, mock_memory, mock_chat_openai):
        """Test routing to MCP agent."""
        # Arrange
        mock_llm = Mock()
        mock_chat_openai.return_value = mock_llm
        mock_memory_instance = Mock()
        mock_memory.return_value = mock_memory_instance

        workflow = LangGraphWorkflow()
        state = create_initial_state("test")
        state.task_type = "mcp"

        # Act
        result = workflow._should_continue(state)

        # Assert
        assert result == "mcp"

    @patch("agents.langgraph_workflow.ChatOpenAI")
    @patch("agents.langgraph_workflow.MemorySaver")
    def test_should_continue_graph(self, mock_memory, mock_chat_openai):
        """Test routing to Graph agent."""
        # Arrange
        mock_llm = Mock()
        mock_chat_openai.return_value = mock_llm
        mock_memory_instance = Mock()
        mock_memory.return_value = mock_memory_instance

        workflow = LangGraphWorkflow()
        state = create_initial_state("test")
        state.task_type = "graph"

        # Act
        result = workflow._should_continue(state)

        # Assert
        assert result == "graph"

    @patch("agents.langgraph_workflow.ChatOpenAI")
    @patch("agents.langgraph_workflow.MemorySaver")
    def test_should_continue_general(self, mock_memory, mock_chat_openai):
        """Test routing to general response."""
        # Arrange
        mock_llm = Mock()
        mock_chat_openai.return_value = mock_llm
        mock_memory_instance = Mock()
        mock_memory.return_value = mock_memory_instance

        workflow = LangGraphWorkflow()
        state = create_initial_state("test")
        state.task_type = "general"

        # Act
        result = workflow._should_continue(state)

        # Assert
        assert result == "general"

    @patch("agents.langgraph_workflow.ChatOpenAI")
    @patch("agents.langgraph_workflow.MemorySaver")
    def test_should_continue_unknown(self, mock_memory, mock_chat_openai):
        """Test routing for unknown task type."""
        # Arrange
        mock_llm = Mock()
        mock_chat_openai.return_value = mock_llm
        mock_memory_instance = Mock()
        mock_memory.return_value = mock_memory_instance

        workflow = LangGraphWorkflow()
        state = create_initial_state("test")
        state.task_type = "unknown"

        # Act
        result = workflow._should_continue(state)

        # Assert
        assert result == "end"

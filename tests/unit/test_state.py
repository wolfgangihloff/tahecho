"""
Unit tests for state management module.
"""

import pytest
from langchain_core.messages import AIMessage, HumanMessage

from tahecho.agents.state import AgentState, create_initial_state


class TestAgentState:
    """Test AgentState class."""

    def test_agent_state_creation(self):
        """Test creating a new AgentState instance."""
        # Arrange & Act
        state = AgentState(user_input="Test input", conversation_id="test_conv")

        # Assert
        assert state.user_input == "Test input"
        assert state.conversation_id == "test_conv"
        assert state.messages == []
        assert state.agent_results == {}
        assert state.task_type is None
        assert state.final_answer is None

    def test_agent_state_with_messages(self):
        """Test AgentState with initial messages."""
        # Arrange
        messages = [HumanMessage(content="Hello")]

        # Act
        state = AgentState(messages=messages)

        # Assert
        assert len(state.messages) == 1
        assert state.messages[0].content == "Hello"

    def test_agent_state_update(self):
        """Test updating AgentState fields."""
        # Arrange
        state = AgentState()

        # Act
        state.task_type = "mcp"
        state.agent_results["test_agent"] = "Test result"
        state.final_answer = "Final answer"

        # Assert
        assert state.task_type == "mcp"
        assert state.agent_results["test_agent"] == "Test result"
        assert state.final_answer == "Final answer"


class TestCreateInitialState:
    """Test create_initial_state function."""

    def test_create_initial_state_basic(self):
        """Test creating initial state with basic input."""
        # Arrange
        user_input = "Show me my Jira issues"

        # Act
        state = create_initial_state(user_input)

        # Assert
        assert state.user_input == user_input
        assert len(state.messages) == 1
        assert isinstance(state.messages[0], HumanMessage)
        assert state.messages[0].content == user_input
        assert state.conversation_id is None

    def test_create_initial_state_with_conversation_id(self):
        """Test creating initial state with conversation ID."""
        # Arrange
        user_input = "Create a new task"
        conversation_id = "conv_123"

        # Act
        state = create_initial_state(user_input, conversation_id)

        # Assert
        assert state.user_input == user_input
        assert state.conversation_id == conversation_id
        assert len(state.messages) == 1

    def test_create_initial_state_empty_input(self):
        """Test creating initial state with empty input."""
        # Arrange
        user_input = ""

        # Act
        state = create_initial_state(user_input)

        # Assert
        assert state.user_input == ""
        assert len(state.messages) == 1
        assert state.messages[0].content == ""


class TestAgentStateIntegration:
    """Test AgentState integration scenarios."""

    def test_state_message_flow(self):
        """Test the flow of messages through state."""
        # Arrange
        state = create_initial_state("Initial message")

        # Act - Add AI response
        ai_message = AIMessage(content="AI response")
        state.messages.append(ai_message)

        # Assert
        assert len(state.messages) == 2
        assert isinstance(state.messages[0], HumanMessage)
        assert isinstance(state.messages[1], AIMessage)
        assert state.messages[1].content == "AI response"

    def test_state_agent_results_flow(self):
        """Test the flow of agent results through state."""
        # Arrange
        state = AgentState()

        # Act
        state.agent_results["mcp_agent"] = "MCP result"
        state.agent_results["graph_agent"] = "Graph result"

        # Assert
        assert len(state.agent_results) == 2
        assert state.agent_results["mcp_agent"] == "MCP result"
        assert state.agent_results["graph_agent"] == "Graph result"

    def test_state_task_classification_flow(self):
        """Test task classification flow through state."""
        # Arrange
        state = create_initial_state("Show me all bugs")

        # Act
        state.task_type = "mcp"
        state.current_agent = "mcp_agent"

        # Assert
        assert state.task_type == "mcp"
        assert state.current_agent == "mcp_agent"

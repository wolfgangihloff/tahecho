#!/usr/bin/env python3
"""
Basic component test for the LangChain implementation.
This test focuses on the core components without requiring external APIs.
"""

import os
import sys
from unittest.mock import Mock, patch

# Mock the config to avoid API key issues
mock_config = {
    "OPENAI_API_KEY": "test_key",
    "OPENAI_SETTINGS": {
        "model": "gpt-4o",
        "temperature": 0.1,
        "max_tokens": 1000,
        "top_p": 1,
        "frequency_penalty": 0,
        "presence_penalty": 0,
        "stream": False,
    },
}

# Mock the config module
sys.modules['config'] = Mock()
sys.modules['config'].CONFIG = mock_config


def test_state_management():
    """Test the state management component."""
    from agents.state import AgentState, create_initial_state
    
    # Test state creation
    state = create_initial_state("Test message", "test_conversation")
    assert state.user_input == "Test message"
    assert state.conversation_id == "test_conversation"
    assert len(state.messages) == 1
    assert state.messages[0].content == "Test message"
    
    # Test state updates
    state.task_type = "mcp"
    state.agent_results["test_agent"] = "Test result"
    assert state.task_type == "mcp"
    assert state.agent_results["test_agent"] == "Test result"


def test_imports():
    """Test that all components can be imported."""
    # Test basic imports
    from agents.state import AgentState, create_initial_state
    
    # Test workflow imports (without initialization)
    from agents.langgraph_workflow import LangGraphWorkflow
    
    # Test manager agent imports (without initialization)
    from agents.langchain_manager_agent import LangChainManagerAgent


def test_workflow_structure():
    """Test the workflow structure without executing it."""
    from agents.langgraph_workflow import LangGraphWorkflow
    
    # Create workflow instance
    workflow = LangGraphWorkflow()
    
    # Check that workflow has required components
    assert hasattr(workflow, 'workflow')
    assert hasattr(workflow, 'memory')
    assert hasattr(workflow, 'app')


def test_manager_agent_structure():
    """Test the manager agent structure without executing it."""
    from agents.langchain_manager_agent import LangChainManagerAgent
    
    # Create manager agent instance
    manager = LangChainManagerAgent()
    
    # Check that manager has required components
    assert hasattr(manager, 'workflow')
    assert hasattr(manager, 'run')


 
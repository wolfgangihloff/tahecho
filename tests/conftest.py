"""
Pytest configuration and fixtures for Tahecho tests.
"""

import os
import sys
from typing import Any, Dict
from unittest.mock import Mock, patch

import pytest

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# Mock configuration for testing
@pytest.fixture(scope="session")
def mock_config():
    """Mock configuration for testing."""
    return {
        "OPENAI_API_KEY": "test_openai_key",
        "JIRA_INSTANCE_URL": "https://test.atlassian.net",
        "JIRA_USERNAME": "test@example.com",
        "JIRA_API_TOKEN": "test_jira_token",
        "JIRA_CLOUD": True,
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


@pytest.fixture(autouse=True)
def mock_env_vars(mock_config):
    """Mock environment variables for all tests."""
    with patch.dict(
        os.environ,
        {
            "OPENAI_API_KEY": mock_config["OPENAI_API_KEY"],
            "JIRA_INSTANCE_URL": mock_config["JIRA_INSTANCE_URL"],
            "JIRA_USERNAME": mock_config["JIRA_USERNAME"],
            "JIRA_API_TOKEN": mock_config["JIRA_API_TOKEN"],
            "JIRA_CLOUD": str(mock_config["JIRA_CLOUD"]).lower(),
        },
    ):
        yield


@pytest.fixture(autouse=True)
def mock_config_module(mock_config):
    """Mock the config module for all tests."""
    with patch("config.CONFIG", mock_config):
        yield


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client."""
    with patch("openai.OpenAI") as mock_client:
        mock_instance = Mock()
        mock_client.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_jira_client():
    """Mock Jira client."""
    with patch("jira_integration.jira_client.jira_client") as mock_client:
        mock_instance = Mock()
        mock_client.instance = mock_instance
        yield mock_client


@pytest.fixture
def sample_jira_issue():
    """Sample Jira issue data for testing."""
    return {
        "id": "12345",
        "key": "DTS-123",
        "self": "https://test.atlassian.net/rest/api/2/issue/12345",
        "fields": {
            "summary": "Test Issue",
            "description": "This is a test issue",
            "status": {"name": "To Do", "statusCategory": {"name": "To Do"}},
            "priority": {"name": "Medium"},
            "issuetype": {
                "name": "Task",
                "description": "A task that needs to be done",
            },
            "project": {"key": "DTS", "name": "Data Transfer System"},
            "assignee": None,
            "reporter": {
                "displayName": "Test User",
                "emailAddress": "test@example.com",
            },
            "created": "2024-01-01T10:00:00.000+0000",
            "updated": "2024-01-01T10:00:00.000+0000",
            "labels": ["test", "documentation"],
            "issuelinks": [],
        },
    }


@pytest.fixture
def mock_agent_state():
    """Create a mock agent state for testing."""
    from langchain_core.messages import HumanMessage

    from tahecho.agents.state import AgentState

    return AgentState(
        user_input="Test user input",
        messages=[HumanMessage(content="Test user input")],
        conversation_id="test_conversation",
    )

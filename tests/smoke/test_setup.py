#!/usr/bin/env python3
"""
Diagnostic script to test Tahecho setup and configuration.
Tests both full mode (with Neo4j) and limited mode (without Neo4j).
"""

import os
import sys
from pathlib import Path

import pytest
from dotenv import load_dotenv

# Add the project root to Python path to enable imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


@pytest.mark.unit
def test_environment_variables() -> None:
    """Test required environment variables."""
    print("🔍 Testing Environment Variables...")

    load_dotenv()

    required_vars = {
        "OPENAI_API_KEY": "OpenAI API Key",
        "JIRA_INSTANCE_URL": "Jira Instance URL", 
        "JIRA_USERNAME": "Jira Username",
        "JIRA_API_TOKEN": "Jira API Token",
    }

    missing_required = []

    for var, description in required_vars.items():
        value = os.getenv(var)
        if not value:
            missing_required.append(f"{description} ({var})")
        else:
            print(f"✅ {description}: {'*' * len(value)}")

    if missing_required:
        pytest.fail(f"Missing required environment variables: {', '.join(missing_required)}")

    print("✅ Environment variables test completed")


@pytest.mark.unit
def test_langchain_setup() -> None:
    """Test LangChain 0.3.x setup."""
    print("\n🔍 Testing LangChain Setup...")

    from langchain.chat_models import init_chat_model
    from config import CONFIG

    # Test chat model initialization
    llm = init_chat_model(
        CONFIG["OPENAI_SETTINGS"]["model"], model_provider="openai", temperature=0.1
    )

    # Test a simple completion
    response = llm.invoke("Hello, this is a test message.")
    print(f"✅ LangChain chat model working: {response.content[:50]}...")
    
    assert response.content, "LangChain should return a response"


@pytest.mark.unit
def test_chainlit_setup() -> None:
    """Test Chainlit setup."""
    print("\n🔍 Testing Chainlit Setup...")

    import chainlit as cl

    print("✅ Chainlit import successful")
    assert cl is not None, "Chainlit should be importable"



@pytest.mark.unit  
def test_jira_integration() -> None:
    """Test Jira integration setup."""
    print("\n🔍 Testing Jira Integration...")

    from tahecho.jira_integration.jira_client import JiraClient

    # Test client creation (without making actual requests)
    client = JiraClient()
    print("✅ Jira client creation successful")
    assert client is not None, "Jira client should be created successfully"


@pytest.mark.unit
def test_agent_setup() -> None:
    """Test agent setup."""
    print("\n🔍 Testing Agent Setup...")

    from tahecho.agents.state import AgentState, create_initial_state
    from tahecho.agents.task_classifier import get_task_classifier

    # Test state creation
    state = create_initial_state("Test message", "test_conversation")
    print("✅ State management working")
    assert state.user_input == "Test message", "State should be created with correct input"

    # Test task classifier - use the correct function
    classifier = get_task_classifier()
    result_state = classifier.classify_task(state)
    print("✅ Task classifier working")
    assert result_state.task_type in ["jira", "general"], "Task should be classified"


# Legacy compatibility - keep for now but tests should be run via pytest
if __name__ == "__main__":
    print("🧪 Tahecho Setup Test Suite")
    print("=" * 50)
    print("ℹ️  Please run tests using pytest:")
    print("   poetry run pytest tests/smoke/test_setup.py -v")
    print("=" * 50)

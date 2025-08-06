#!/usr/bin/env python3
"""
Diagnostic script to test Tahecho setup and configuration.
Tests both full mode (with Neo4j) and limited mode (without Neo4j).
"""

import os
import sys

from dotenv import load_dotenv


def test_environment_variables():
    """Test required environment variables."""
    print("🔍 Testing Environment Variables...")

    load_dotenv()

    required_vars = {
        "OPENAI_API_KEY": "OpenAI API Key",
        "JIRA_INSTANCE_URL": "Jira Instance URL",
        "JIRA_USERNAME": "Jira Username",
        "JIRA_API_TOKEN": "Jira API Token",
    }

    optional_vars = {
        "GRAPH_DB_ENABLED": "Graph Database Enabled",
        "NEO4J_URI": "Neo4j URI",
        "NEO4J_USERNAME": "Neo4j Username",
        "NEO4J_PASSWORD": "Neo4j Password",
    }

    missing_required = []
    missing_optional = []

    for var, description in required_vars.items():
        value = os.getenv(var)
        if not value:
            missing_required.append(f"❌ {description} ({var})")
        else:
            print(f"✅ {description}: {'*' * len(value)}")

    for var, description in optional_vars.items():
        value = os.getenv(var)
        if not value:
            missing_optional.append(f"⚠️  {description} ({var}) - Optional")
        else:
            print(f"✅ {description}: {value}")

    if missing_required:
        print("\n❌ Missing Required Environment Variables:")
        for var in missing_required:
            print(f"  {var}")
        return False

    if missing_optional:
        print("\n⚠️  Missing Optional Environment Variables:")
        for var in missing_optional:
            print(f"  {var}")

    print("✅ Environment variables test completed")
    return True


def test_langchain_setup():
    """Test LangChain 0.3.x setup."""
    print("\n🔍 Testing LangChain Setup...")

    try:
        from langchain.chat_models import init_chat_model

        from config import CONFIG

        # Test chat model initialization
        llm = init_chat_model(
            CONFIG["OPENAI_SETTINGS"]["model"], model_provider="openai", temperature=0.1
        )

        # Test a simple completion
        response = llm.invoke("Hello, this is a test message.")
        print(f"✅ LangChain chat model working: {response.content[:50]}...")
        return True

    except Exception as e:
        print(f"❌ LangChain setup failed: {str(e)}")
        return False


def test_chainlit_setup():
    """Test Chainlit setup."""
    print("\n🔍 Testing Chainlit Setup...")

    try:
        import chainlit as cl

        print("✅ Chainlit import successful")
        return True
    except Exception as e:
        print(f"❌ Chainlit setup failed: {str(e)}")
        return False


def test_graph_database():
    """Test optional graph database connection."""
    print("\n🔍 Testing Graph Database Connection...")

    try:
        from tahecho.utils.graph_db import GraphDatabase

        # Check if graph database is enabled
        graph_enabled = os.getenv("GRAPH_DB_ENABLED", "false").lower() == "true"

        if not graph_enabled:
            print("⚠️  Graph database disabled - skipping test")
            return True

        # Test connection
        graph_db = GraphDatabase()
        if graph_db.is_connected():
            print("✅ Graph database connection successful")
            return True
        else:
            print("❌ Graph database connection failed")
            return False

    except Exception as e:
        print(f"❌ Graph database test failed: {str(e)}")
        return False


def test_jira_integration():
    """Test Jira integration setup."""
    print("\n🔍 Testing Jira Integration...")

    try:
        from tahecho.jira_integration.jira_client import JiraClient

        # Test client creation (without making actual requests)
        client = JiraClient()
        print("✅ Jira client creation successful")
        return True

    except Exception as e:
        print(f"❌ Jira integration test failed: {str(e)}")
        return False


def test_agent_setup():
    """Test agent setup."""
    print("\n🔍 Testing Agent Setup...")

    try:
        from tahecho.agents.state import AgentState, create_initial_state
        from tahecho.agents.task_classifier import task_classifier

        # Test state creation
        state = create_initial_state("Test message", "test_conversation")
        print("✅ State management working")

        # Test task classifier
        result_state = task_classifier.classify_task(state)
        print("✅ Task classifier working")

        return True

    except Exception as e:
        print(f"❌ Agent setup test failed: {str(e)}")
        return False


def main():
    """Run all setup tests."""
    print("🧪 Tahecho Setup Test Suite")
    print("=" * 50)

    tests = [
        ("Environment Variables", test_environment_variables),
        ("LangChain Setup", test_langchain_setup),
        ("Chainlit Setup", test_chainlit_setup),
        ("Graph Database", test_graph_database),
        ("Jira Integration", test_jira_integration),
        ("Agent Setup", test_agent_setup),
    ]

    results = []

    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {str(e)}")
            results.append((test_name, False))

    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)

    passed = 0
    failed = 0

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
        if result:
            passed += 1
        else:
            failed += 1

    print(f"\nTotal: {passed + failed} tests")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")

    if failed == 0:
        print("\n🎉 All tests passed! Tahecho is ready to use.")
        return True
    else:
        print(f"\n⚠️  {failed} test(s) failed. Please check the configuration.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

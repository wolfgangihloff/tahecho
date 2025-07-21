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
        "JIRA_API_TOKEN": "Jira API Token"
    }
    
    optional_vars = {
        "GRAPH_DB_ENABLED": "Graph Database Enabled",
        "NEO4J_URI": "Neo4j URI",
        "NEO4J_USERNAME": "Neo4j Username", 
        "NEO4J_PASSWORD": "Neo4j Password"
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
            CONFIG["OPENAI_SETTINGS"]["model"],
            model_provider="openai",
            temperature=0.1
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
        from utils.graph_db import graph_db_manager
        
        # Test connection
        connected = graph_db_manager.connect()
        
        if connected:
            print("✅ Neo4j connection successful")
            print("✅ Running in FULL MODE - all features available")
            return True
        else:
            print("⚠️  Neo4j not available")
            print("✅ Running in LIMITED MODE - basic features only")
            return True  # This is not an error, just limited functionality
            
    except Exception as e:
        print(f"❌ Graph database test failed: {str(e)}")
        return False

def test_jira_integration():
    """Test Jira integration."""
    print("\n🔍 Testing Jira Integration...")
    
    try:
        from jira_integration.jira_client import jira_client
        
        # Test basic Jira connection
        issues = jira_client.get_all_jira_issues()
        print(f"✅ Jira connection successful - found {len(issues)} issues")
        return True
        
    except Exception as e:
        print(f"❌ Jira integration failed: {str(e)}")
        return False

def test_agent_setup():
    """Test agent setup."""
    print("\n🔍 Testing Agent Setup...")
    
    try:
        from agents.langchain_manager_agent import langchain_manager_agent
        from agents.langchain_mcp_agent import langchain_mcp_agent
        from agents.langchain_graph_agent import langchain_graph_agent
        
        print("✅ All agents imported successfully")
        return True
        
    except Exception as e:
        print(f"❌ Agent setup failed: {str(e)}")
        return False

def main():
    """Run all diagnostic tests."""
    print("🚀 Tahecho Setup Diagnostic")
    print("=" * 50)
    
    tests = [
        ("Environment Variables", test_environment_variables),
        ("LangChain Setup", test_langchain_setup),
        ("Chainlit Setup", test_chainlit_setup),
        ("Graph Database", test_graph_database),
        ("Jira Integration", test_jira_integration),
        ("Agent Setup", test_agent_setup)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {str(e)}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Your setup is ready.")
        print("\nYou can now run:")
        print("  chainlit run app.py")
    elif passed >= 4:  # At least basic functionality works
        print("⚠️  Basic functionality available, but some features may be limited.")
        print("\nYou can still run:")
        print("  chainlit run app.py")
    else:
        print("❌ Setup has issues. Please check the errors above.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 
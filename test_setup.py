#!/usr/bin/env python3
"""
Test script to diagnose Tahecho setup issues
"""

import os
import sys
from dotenv import load_dotenv

def test_env_vars():
    """Test environment variables"""
    print("🔍 Testing environment variables...")
    load_dotenv()
    
    required_vars = ["OPENAI_API_KEY"]
    optional_vars = ["JIRA_INSTANCE_URL", "JIRA_USERNAME", "JIRA_API_TOKEN", "JIRA_CLOUD"]
    
    missing_required = []
    for var in required_vars:
        if not os.getenv(var):
            missing_required.append(var)
    
    if missing_required:
        print(f"❌ Missing required environment variables: {missing_required}")
        print("   Please set these in your .env file")
        return False
    else:
        print("✅ Required environment variables are set")
    
    # Check optional vars
    missing_optional = []
    for var in optional_vars:
        if not os.getenv(var):
            missing_optional.append(var)
    
    if missing_optional:
        print(f"⚠️  Missing optional environment variables: {missing_optional}")
        print("   Jira functionality will be limited")
    else:
        print("✅ All environment variables are set")
    
    return True

def test_langchain():
    """Test LangChain setup"""
    print("\n🔍 Testing LangChain setup...")
    try:
        from langchain.chat_models import init_chat_model
        model = init_chat_model("gpt-4o-mini", model_provider="openai")
        print("✅ LangChain setup successful")
        return True
    except Exception as e:
        print(f"❌ LangChain setup failed: {e}")
        return False

def test_neo4j():
    """Test Neo4j connection"""
    print("\n🔍 Testing Neo4j connection...")
    try:
        from py2neo import Graph
        # Try to connect to Neo4j
        graph = Graph("bolt://localhost:7687", auth=("neo4j", "test1234"))
        # Test a simple query
        result = graph.run("RETURN 1 as test").data()
        print("✅ Neo4j connection successful")
        return True
    except Exception as e:
        print(f"❌ Neo4j connection failed: {e}")
        print("   Make sure Neo4j is running at bolt://localhost:7687")
        print("   You can start it with: docker run -d --name neo4j -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/test1234 neo4j:latest")
        return False

def test_chainlit():
    """Test Chainlit setup"""
    print("\n🔍 Testing Chainlit setup...")
    try:
        import chainlit as cl
        print("✅ Chainlit setup successful")
        return True
    except Exception as e:
        print(f"❌ Chainlit setup failed: {e}")
        return False

def main():
    print("🚀 Tahecho Setup Diagnostic Tool\n")
    
    tests = [
        test_env_vars,
        test_langchain,
        test_chainlit,
        test_neo4j,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            results.append(False)
    
    print("\n" + "="*50)
    print("📊 SUMMARY")
    print("="*50)
    
    if all(results):
        print("🎉 All tests passed! Your setup is ready.")
        print("   You can now run: poetry run python app.py")
    else:
        print("⚠️  Some tests failed. Please fix the issues above before running the app.")
        print("\n💡 Quick fixes:")
        print("   1. Create a .env file with OPENAI_API_KEY")
        print("   2. Start Neo4j: docker run -d --name neo4j -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/test1234 neo4j:latest")
        print("   3. Install dependencies: poetry install")

if __name__ == "__main__":
    main() 
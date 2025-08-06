#!/usr/bin/env python3
"""
Test script to validate Jira MCP integration in the main app.
"""

import asyncio
import logging
import sys
import os
from unittest.mock import patch, MagicMock

# Add src and root to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from tahecho.agents.langchain_manager_agent import langchain_manager_agent
from tahecho.agents.state import AgentState

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_jira_integration():
    """Test the Jira MCP integration in the main workflow."""
    
    # Test queries that should trigger the Jira MCP agent
    test_queries = [
        "What tickets are assigned to me?",
        "Please create a new ticket in project PGA with the content: Implement user authentication feature",
        "Show me all tickets in the PGA project",
        "Get details for ticket PGA-123"
    ]
    
    print("🧪 Testing Jira MCP Integration")
    print("=" * 50)
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n📝 Test {i}: {query}")
        print("-" * 30)
        
        try:
            # Mock the task classifier to return "jira"
            with patch('tahecho.agents.task_classifier.TaskClassifier.classify_task') as mock_classify:
                mock_classify.return_value = AgentState(
                    user_input=query,
                    task_type="jira"
                )
                
                # Mock the Jira MCP agent
                with patch('tahecho.agents.jira_mcp_agent.jira_mcp_agent') as mock_jira_agent:
                    mock_jira_agent.execute.return_value = AgentState(
                        user_input=query,
                        task_type="jira",
                        current_agent="jira_mcp_agent",
                        agent_results={"jira_mcp_agent": f"Mock response for: {query}"}
                    )
                    
                    # Execute the workflow
                    result = langchain_manager_agent.run(query)
                    
                    print(f"✅ Response: {result}")
                    
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print()


def test_real_integration():
    """Test with real agent execution (requires proper configuration)."""
    
    print("\n🔧 Testing Real Integration (requires Jira config)")
    print("=" * 50)
    
    # Check if Jira credentials are configured
    required_vars = ["JIRA_INSTANCE_URL", "JIRA_USERNAME", "JIRA_API_TOKEN"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"⚠️  Missing Jira configuration: {', '.join(missing_vars)}")
        print("Skipping real integration test")
        return
    
    # Test with a simple query
    query = "What tickets are assigned to me?"
    
    try:
        print(f"📝 Testing: {query}")
        result = langchain_manager_agent.run(query)
        print(f"✅ Response: {result}")
    except Exception as e:
        print(f"❌ Error: {e}")


def main():
    """Main test function."""
    print("🚀 Starting Jira MCP Integration Tests")
    
    # Test with mocked components
    test_jira_integration()
    
    # Test with real integration (if configured)
    test_real_integration()
    
    print("\n🎉 Integration tests completed!")
    return 0


if __name__ == "__main__":
    sys.exit(main())

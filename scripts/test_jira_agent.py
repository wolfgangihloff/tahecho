#!/usr/bin/env python3
"""
Test script for the Jira MCP agent.
"""

import asyncio
import logging
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tahecho.agents.jira_mcp_agent import jira_mcp_agent
from tahecho.agents.state import AgentState

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_jira_agent():
    """Test the Jira MCP agent with sample queries."""
    
    # Test queries
    test_queries = [
        "What tickets are assigned to me?",
        "Please create a new ticket in project PGA with the content: Implement user authentication feature",
        "Show me all tickets in the PGA project",
        "Get details for ticket PGA-123"
    ]
    
    print("🧪 Testing Jira MCP Agent")
    print("=" * 50)
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n📝 Test {i}: {query}")
        print("-" * 30)
        
        try:
            # Create a new state for each query
            state = AgentState(user_input=query)
            
            # Execute the agent
            result_state = jira_mcp_agent.execute(state)
            
            # Print the result
            print(f"✅ Response: {result_state.agent_results.get('jira_mcp_agent', 'No response')}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print()


def main():
    """Main test function."""
    try:
        test_jira_agent()
        print("\n🎉 All tests completed!")
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
    except Exception as e:
        print(f"\n💥 Test failed with error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

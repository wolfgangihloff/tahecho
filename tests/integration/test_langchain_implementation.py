#!/usr/bin/env python3
"""
Test script for the new LangChain implementation.
This script tests the basic functionality without requiring the full infrastructure.
"""

import asyncio
from agents.state import create_initial_state
from agents.task_classifier import task_classifier
from agents.langchain_manager_agent import langchain_manager_agent


def test_task_classification():
    """Test the task classifier."""
    print("Testing task classification...")
    
    test_cases = [
        "Show me all open bugs in the DTS project",
        "Why is task DTS-53 blocked?",
        "Create a new task for testing",
        "What changed this week in project DTS?",
        "Hello, how are you?"
    ]
    
    for test_input in test_cases:
        print(f"\nInput: {test_input}")
        state = create_initial_state(test_input)
        result_state = task_classifier.classify_task(state)
        print(f"Classified as: {result_state.task_type}")
        print(f"Reasoning: {result_state.messages[-1].content}")


def test_manager_agent():
    """Test the manager agent (without actual tool execution)."""
    print("\n\nTesting manager agent...")
    
    test_input = "Show me all open bugs in the DTS project"
    print(f"Input: {test_input}")
    
    try:
        result = langchain_manager_agent.run(test_input, conversation_id="test_conversation")
        print(f"Result: {result}")
    except Exception as e:
        print(f"Error: {str(e)}")


def test_state_management():
    """Test state management."""
    print("\n\nTesting state management...")
    
    # Create initial state
    state = create_initial_state("Test message", "test_conversation")
    print(f"Initial state: {state.user_input}")
    print(f"Conversation ID: {state.conversation_id}")
    print(f"Messages count: {len(state.messages)}")
    
    # Test state updates
    state.task_type = "mcp"
    state.agent_results["test_agent"] = "Test result"
    print(f"Updated task type: {state.task_type}")
    print(f"Agent results: {state.agent_results}")


if __name__ == "__main__":
    print("Testing LangChain Implementation for Tahecho")
    print("=" * 50)
    
    try:
        test_state_management()
        test_task_classification()
        test_manager_agent()
        
        print("\n" + "=" * 50)
        print("All tests completed!")
        
    except Exception as e:
        print(f"\nTest failed with error: {str(e)}")
        import traceback
        traceback.print_exc() 
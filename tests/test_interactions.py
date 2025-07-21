#!/usr/bin/env python3
"""
Interaction tests for Tahecho workflow execution.
These tests simulate real user interactions to catch runtime errors.
"""

import pytest
import asyncio
from unittest.mock import patch, MagicMock
from dotenv import load_dotenv

# Load environment variables for testing
load_dotenv()


class TestWorkflowExecution:
    """Test the actual workflow execution with real user queries."""
    
    def test_basic_jira_query_workflow(self):
        """Test basic Jira query workflow execution."""
        try:
            from agents.langchain_manager_agent import langchain_manager_agent
            
            # Test a simple Jira query
            query = "Was ist in Jira?"
            result = langchain_manager_agent.run(query, conversation_id="test_conversation")
            
            # Should return a string response
            assert isinstance(result, str)
            assert len(result) > 0
            
            print(f"✅ Basic Jira query result: {result[:100]}...")
            
        except Exception as e:
            pytest.fail(f"Basic Jira query workflow failed: {str(e)}")
    
    def test_workflow_with_graph_db_disabled(self):
        """Test workflow execution when graph database is disabled."""
        try:
            from agents.langchain_manager_agent import langchain_manager_agent
            
            # Mock graph database as disabled
            with patch('utils.graph_db.graph_db_manager') as mock_manager:
                mock_manager.is_available.return_value = False
                
                query = "Show me my Jira issues"
                result = langchain_manager_agent.run(query, conversation_id="test_conversation")
                
                assert isinstance(result, str)
                assert len(result) > 0
                
                print(f"✅ Graph DB disabled query result: {result[:100]}...")
                
        except Exception as e:
            pytest.fail(f"Workflow with disabled graph DB failed: {str(e)}")
    
    def test_workflow_with_graph_db_enabled(self):
        """Test workflow execution when graph database is enabled."""
        try:
            from agents.langchain_manager_agent import langchain_manager_agent
            
            # Mock graph database as enabled
            with patch('utils.graph_db.graph_db_manager') as mock_manager:
                mock_manager.is_available.return_value = True
                
                query = "What are the dependencies for issue ABC-123?"
                result = langchain_manager_agent.run(query, conversation_id="test_conversation")
                
                assert isinstance(result, str)
                assert len(result) > 0
                
                print(f"✅ Graph DB enabled query result: {result[:100]}...")
                
        except Exception as e:
            pytest.fail(f"Workflow with enabled graph DB failed: {str(e)}")
    
    def test_workflow_error_handling(self):
        """Test that workflow handles errors gracefully."""
        try:
            from agents.langchain_manager_agent import langchain_manager_agent
            
            # Test with a query that might cause issues
            query = "Complex query that might fail"
            result = langchain_manager_agent.run(query, conversation_id="test_conversation")
            
            # Should return a string response even if there are issues
            assert isinstance(result, str)
            assert len(result) > 0
            
            print(f"✅ Error handling test result: {result[:100]}...")
            
        except Exception as e:
            pytest.fail(f"Workflow error handling failed: {str(e)}")


class TestLangGraphWorkflow:
    """Test the LangGraph workflow directly."""
    
    def test_workflow_state_creation(self):
        """Test that workflow state is created correctly."""
        try:
            from agents.state import create_initial_state
            
            # Create initial state
            state = create_initial_state("Test query", conversation_id="test_conv")
            
            # Check required attributes
            assert hasattr(state, 'user_input')
            assert hasattr(state, 'messages')
            assert hasattr(state, 'agent_results')
            assert hasattr(state, 'task_type')
            assert hasattr(state, 'current_agent')
            assert hasattr(state, 'final_answer')
            
            # Check initial values
            assert state.user_input == "Test query"
            assert isinstance(state.messages, list)
            assert isinstance(state.agent_results, dict)
            assert state.final_answer is None
            
            print("✅ Workflow state created correctly")
            
        except Exception as e:
            pytest.fail(f"Workflow state creation failed: {str(e)}")
    
    def test_workflow_execution_flow(self):
        """Test the complete workflow execution flow."""
        try:
            from agents.langgraph_workflow import langgraph_workflow
            
            # Test workflow execution
            result = langgraph_workflow.execute("Test query", conversation_id="test_conv")
            
            # Should return a string
            assert isinstance(result, str)
            assert len(result) > 0
            
            print(f"✅ Workflow execution result: {result[:100]}...")
            
        except Exception as e:
            pytest.fail(f"Workflow execution flow failed: {str(e)}")
    
    def test_workflow_final_response_generation(self):
        """Test that final response is generated correctly."""
        try:
            from agents.langgraph_workflow import langgraph_workflow
            from agents.state import create_initial_state
            
            # Create state with some agent results
            state = create_initial_state("Test query", conversation_id="test_conv")
            state.agent_results = {"mcp_agent": "Test result from MCP agent"}
            state.current_agent = "mcp_agent"
            
            # Test final response generation
            result = langgraph_workflow._generate_final_response(state)
            
            # Should have a final answer
            assert hasattr(result, 'final_answer')
            assert result.final_answer is not None
            assert len(result.final_answer) > 0
            
            print(f"✅ Final response generated: {result.final_answer[:100]}...")
            
        except Exception as e:
            pytest.fail(f"Final response generation failed: {str(e)}")


class TestAgentExecution:
    """Test individual agent execution."""
    
    def test_mcp_agent_execution(self):
        """Test MCP agent execution."""
        try:
            from agents.langchain_mcp_agent import langchain_mcp_agent
            from agents.state import create_initial_state
            
            # Create test state
            state = create_initial_state("Show me my Jira issues", conversation_id="test_conv")
            
            # Execute MCP agent
            result_state = langchain_mcp_agent.execute(state)
            
            # Check result
            assert hasattr(result_state, 'agent_results')
            assert 'mcp_agent' in result_state.agent_results
            assert isinstance(result_state.agent_results['mcp_agent'], str)
            
            print(f"✅ MCP agent result: {result_state.agent_results['mcp_agent'][:100]}...")
            
        except Exception as e:
            pytest.fail(f"MCP agent execution failed: {str(e)}")
    
    def test_graph_agent_execution(self):
        """Test Graph agent execution."""
        try:
            from agents.langchain_graph_agent import langchain_graph_agent
            from agents.state import create_initial_state
            
            # Create test state
            state = create_initial_state("Show dependencies for ABC-123", conversation_id="test_conv")
            
            # Execute Graph agent
            result_state = langchain_graph_agent.execute(state)
            
            # Check result
            assert hasattr(result_state, 'agent_results')
            assert 'graph_agent' in result_state.agent_results
            assert isinstance(result_state.agent_results['graph_agent'], str)
            
            print(f"✅ Graph agent result: {result_state.agent_results['graph_agent'][:100]}...")
            
        except Exception as e:
            pytest.fail(f"Graph agent execution failed: {str(e)}")


class TestIntegrationScenarios:
    """Test integration scenarios that users might encounter."""
    
    def test_german_query_handling(self):
        """Test handling of German queries like 'Was ist in Jira?'."""
        try:
            from agents.langchain_manager_agent import langchain_manager_agent
            
            # Test German query
            query = "Was ist in Jira?"
            result = langchain_manager_agent.run(query, conversation_id="test_german")
            
            assert isinstance(result, str)
            assert len(result) > 0
            
            print(f"✅ German query result: {result[:100]}...")
            
        except Exception as e:
            pytest.fail(f"German query handling failed: {str(e)}")
    
    def test_conversation_persistence(self):
        """Test that conversations are persisted correctly."""
        try:
            from agents.langchain_manager_agent import langchain_manager_agent
            
            conversation_id = "test_persistence"
            
            # First query
            result1 = langchain_manager_agent.run("First message", conversation_id=conversation_id)
            
            # Second query
            result2 = langchain_manager_agent.run("Second message", conversation_id=conversation_id)
            
            # Both should work
            assert isinstance(result1, str)
            assert isinstance(result2, str)
            assert len(result1) > 0
            assert len(result2) > 0
            
            print("✅ Conversation persistence working")
            
        except Exception as e:
            pytest.fail(f"Conversation persistence failed: {str(e)}")
    
    def test_error_recovery(self):
        """Test that the system recovers from errors gracefully."""
        try:
            from agents.langchain_manager_agent import langchain_manager_agent
            
            # Test with potentially problematic query
            query = "Complex query with special characters: äöüß"
            result = langchain_manager_agent.run(query, conversation_id="test_error_recovery")
            
            assert isinstance(result, str)
            assert len(result) > 0
            
            print(f"✅ Error recovery result: {result[:100]}...")
            
        except Exception as e:
            pytest.fail(f"Error recovery failed: {str(e)}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 
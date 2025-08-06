"""
End-to-end integration tests for Jira MCP agent functionality.
"""

import pytest
import os
import sys
from unittest.mock import patch, MagicMock

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from tahecho.agents.jira_mcp_agent import JiraMCPAgent
from tahecho.agents.state import AgentState
from tahecho.agents.langgraph_workflow import LangGraphWorkflow


class TestJiraMCPIntegration:
    """Test Jira MCP agent integration with the workflow."""

    @pytest.fixture
    def jira_agent(self):
        """Create a Jira MCP agent instance."""
        return JiraMCPAgent()

    @pytest.fixture
    def workflow(self):
        """Create a LangGraph workflow instance."""
        return LangGraphWorkflow()

    @pytest.fixture
    def mock_env_vars(self):
        """Mock environment variables for testing."""
        with patch.dict(os.environ, {
            'JIRA_INSTANCE_URL': 'https://test.atlassian.net',
            'JIRA_USERNAME': 'test@example.com',
            'JIRA_API_TOKEN': 'test_token',
            'JIRA_CLOUD': 'true',
            'OPENAI_API_KEY': 'test_openai_key'
        }):
            yield

    def test_jira_agent_initialization(self, jira_agent):
        """Test that the Jira MCP agent initializes correctly."""
        assert jira_agent is not None
        assert hasattr(jira_agent, 'llm')
        assert hasattr(jira_agent, 'mcp_tools')
        assert hasattr(jira_agent, 'agent_executor')

    def test_jira_agent_tools_creation(self, jira_agent):
        """Test that the Jira MCP agent creates the expected tools."""
        tools = jira_agent.mcp_tools
        tool_names = [tool.name for tool in tools]
        
        expected_tools = ['search_my_tickets', 'search_tickets', 'create_ticket', 'get_ticket_details']
        for tool_name in expected_tools:
            assert tool_name in tool_names

    @patch('subprocess.Popen')
    def test_mcp_server_startup(self, mock_popen, jira_agent):
        """Test MCP server startup functionality."""
        # Mock the subprocess to return a running process
        mock_process = MagicMock()
        mock_process.poll.return_value = None  # Process is running
        mock_popen.return_value = mock_process
        
        result = jira_agent._start_mcp_server()
        assert result is True
        mock_popen.assert_called_once()

    @patch('subprocess.Popen')
    def test_mcp_server_startup_failure(self, mock_popen, jira_agent):
        """Test MCP server startup failure handling."""
        # Mock the subprocess to return a failed process
        mock_process = MagicMock()
        mock_process.poll.return_value = 1  # Process failed
        mock_process.communicate.return_value = ("stdout", "stderr")
        mock_popen.return_value = mock_process
        
        result = jira_agent._start_mcp_server()
        assert result is False

    def test_search_my_tickets_tool(self, jira_agent):
        """Test the search_my_tickets tool functionality."""
        with patch.object(jira_agent, '_start_mcp_server', return_value=True):
            # Get the search_my_tickets tool
            search_tool = next(tool for tool in jira_agent.mcp_tools if tool.name == 'search_my_tickets')
            
            result = search_tool.func()
            assert "Found 3 tickets assigned to you" in result
            assert "PGA-123" in result
            assert "PGA-456" in result
            assert "PGA-789" in result

    def test_create_ticket_tool(self, jira_agent):
        """Test the create_ticket tool functionality."""
        with patch.object(jira_agent, '_start_mcp_server', return_value=True):
            # Get the create_ticket tool
            create_tool = next(tool for tool in jira_agent.mcp_tools if tool.name == 'create_ticket')
            
            result = create_tool.func("PGA", "Test ticket", "Test description", "Task")
            assert "Successfully created ticket" in result
            assert "Test ticket" in result

    def test_search_tickets_tool(self, jira_agent):
        """Test the search_tickets tool functionality."""
        with patch.object(jira_agent, '_start_mcp_server', return_value=True):
            # Get the search_tickets tool
            search_tool = next(tool for tool in jira_agent.mcp_tools if tool.name == 'search_tickets')
            
            # Test currentUser query
            result = search_tool.func("assignee = currentUser()")
            assert "Found 3 tickets assigned to you" in result
            
            # Test project query
            result = search_tool.func("project = 'PGA'")
            assert "Found 5 tickets in PGA project" in result

    def test_get_ticket_details_tool(self, jira_agent):
        """Test the get_ticket_details tool functionality."""
        with patch.object(jira_agent, '_start_mcp_server', return_value=True):
            # Get the get_ticket_details tool
            details_tool = next(tool for tool in jira_agent.mcp_tools if tool.name == 'get_ticket_details')
            
            result = details_tool.func("PGA-123")
            assert "Ticket PGA-123 details" in result
            assert "Status: In Progress" in result

    def test_jira_agent_execution_success(self, jira_agent):
        """Test successful Jira agent execution."""
        state = AgentState(user_input="What tickets are assigned to me?")
        
        with patch.object(jira_agent, '_start_mcp_server', return_value=True):
            result_state = jira_agent.execute(state)
            
            assert result_state.current_agent == "jira_mcp_agent"
            assert "jira_mcp_agent" in result_state.agent_results
            assert len(result_state.messages) > 0

    def test_jira_agent_execution_failure(self, jira_agent):
        """Test Jira agent execution failure handling."""
        state = AgentState(user_input="What tickets are assigned to me?")
        
        with patch.object(jira_agent, '_start_mcp_server', return_value=False):
            result_state = jira_agent.execute(state)
            
            assert result_state.current_agent == "jira_mcp_agent"
            assert "jira_mcp_agent" in result_state.agent_results
            assert "Error" in result_state.agent_results["jira_mcp_agent"]

    def test_workflow_integration_jira_task(self, workflow):
        """Test workflow integration with Jira tasks."""
        # Test queries that should be classified as Jira tasks
        jira_queries = [
            "What tickets are assigned to me?",
            "Please create a new ticket in project PGA with the content: Implement user authentication feature",
            "Show me all tickets in the PGA project",
            "Get details for ticket PGA-123"
        ]
        
        for query in jira_queries:
            with patch.object(workflow, '_classify_task') as mock_classify:
                # Mock the task classifier to return "jira"
                mock_classify.return_value = AgentState(
                    user_input=query,
                    task_type="jira"
                )
                
                # Mock the Jira agent execution
                with patch('tahecho.agents.jira_mcp_agent.jira_mcp_agent') as mock_jira_agent:
                    mock_jira_agent.execute.return_value = AgentState(
                        user_input=query,
                        task_type="jira",
                        current_agent="jira_mcp_agent",
                        agent_results={"jira_mcp_agent": "Test response"}
                    )
                    
                    result = workflow.execute(query)
                    assert "Test response" in result

    def test_task_classification_jira_queries(self):
        """Test that Jira-specific queries are correctly classified."""
        from tahecho.agents.task_classifier import TaskClassifier
        
        classifier = TaskClassifier()
        
        jira_queries = [
            "What tickets are assigned to me?",
            "Create a new ticket in project PGA",
            "Show me tickets in PGA project",
            "Get details for ticket ABC-123"
        ]
        
        for query in jira_queries:
            state = AgentState(user_input=query)
            
            with patch.object(classifier, 'llm') as mock_llm:
                # Mock the LLM to return "jira" classification
                mock_llm.invoke.return_value.content = '{"task_type": "jira", "reasoning": "Jira-specific query"}'
                
                result_state = classifier.classify_task(state)
                assert result_state.task_type == "jira"

    def test_error_handling_user_friendly_messages(self, jira_agent):
        """Test that error messages are user-friendly."""
        error_tests = [
            ("invalid api key", "I'm having trouble connecting to Jira"),
            ("401 unauthorized", "I'm unable to access your Jira information"),
            ("connection timeout", "I'm experiencing connection issues with Jira"),
            ("project not found", "The specified project was not found"),
            ("unknown error", "I encountered an issue while accessing Jira")
        ]
        
        for error_input, expected_phrase in error_tests:
            result = jira_agent._create_user_friendly_error_message(error_input)
            assert expected_phrase in result

    def test_agent_cleanup(self, jira_agent):
        """Test that the agent properly cleans up resources."""
        with patch.object(jira_agent, '_stop_mcp_server') as mock_stop:
            # Simulate agent destruction
            jira_agent.__del__()
            mock_stop.assert_called_once()


class TestJiraMCPEndToEnd:
    """End-to-end tests for complete Jira MCP functionality."""

    @pytest.fixture
    def mock_mcp_server(self):
        """Mock the MCP server for end-to-end testing."""
        with patch('subprocess.Popen') as mock_popen:
            mock_process = MagicMock()
            mock_process.poll.return_value = None  # Server is running
            mock_popen.return_value = mock_process
            yield mock_popen

    def test_complete_jira_workflow(self, mock_mcp_server):
        """Test complete Jira workflow from user input to response."""
        from tahecho.agents.langchain_manager_agent import langchain_manager_agent
        
        # Test the complete workflow
        test_queries = [
            "What tickets are assigned to me?",
            "Please create a new ticket in project PGA with the content: Test feature",
            "Show me all tickets in the PGA project"
        ]
        
        for query in test_queries:
            with patch('tahecho.agents.task_classifier.TaskClassifier.classify_task') as mock_classify:
                # Mock task classification
                mock_classify.return_value = AgentState(
                    user_input=query,
                    task_type="jira"
                )
                
                # Execute the workflow
                result = langchain_manager_agent.run(query)
                
                # Verify we get a response
                assert result is not None
                assert len(result) > 0
                assert "Error" not in result or "I'm having trouble" in result  # User-friendly error

    def test_jira_agent_in_workflow_context(self, mock_mcp_server):
        """Test Jira agent within the full workflow context."""
        workflow = LangGraphWorkflow()
        
        # Test with a Jira query
        query = "What tickets are assigned to me?"
        
        with patch.object(workflow, '_classify_task') as mock_classify:
            mock_classify.return_value = AgentState(
                user_input=query,
                task_type="jira"
            )
            
            # Mock the Jira agent to return a successful response
            with patch('tahecho.agents.jira_mcp_agent.jira_mcp_agent') as mock_jira_agent:
                mock_jira_agent.execute.return_value = AgentState(
                    user_input=query,
                    task_type="jira",
                    current_agent="jira_mcp_agent",
                    agent_results={"jira_mcp_agent": "Found 3 tickets assigned to you"}
                )
                
                result = workflow.execute(query)
                assert "Found 3 tickets assigned to you" in result

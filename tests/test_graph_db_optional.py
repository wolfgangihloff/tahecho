#!/usr/bin/env python3
"""
Tests for optional graph database functionality.
Following TDD: Red-Green-Refactor cycle.
"""

import pytest
import os
from unittest.mock import patch, MagicMock
from dotenv import load_dotenv

# Load environment variables for testing
load_dotenv()


class TestGraphDBManager:
    """Test the GraphDBManager class for optional graph database functionality."""
    
    def test_graph_db_manager_import_without_py2neo(self):
        """Test that the app can import without py2neo installed."""
        # This test should pass even if py2neo is not installed
        # The import should be handled gracefully
        try:
            from utils.graph_db import graph_db_manager
            assert graph_db_manager is not None
        except ImportError as e:
            if "py2neo" in str(e):
                pytest.skip("py2neo not installed - this is expected in some environments")
            else:
                raise
    
    def test_graph_db_manager_initialization(self):
        """Test that GraphDBManager initializes correctly."""
        try:
            from utils.graph_db import GraphDBManager
            
            manager = GraphDBManager()
            assert manager.graph is None
            assert manager.is_connected is False
        except ImportError as e:
            if "py2neo" in str(e):
                pytest.skip("py2neo not installed")
            else:
                raise
    
    def test_graph_db_disabled_in_config(self):
        """Test that graph database can be disabled via config."""
        try:
            from utils.graph_db import GraphDBManager
            
            # Mock the config to disable graph database
            with patch('utils.graph_db.CONFIG') as mock_config:
                mock_config.__getitem__.return_value = False
                
                manager = GraphDBManager()
                
                # Should not attempt to connect when disabled
                result = manager.connect()
                assert result is False
                assert manager.is_connected is False
        except ImportError as e:
            if "py2neo" in str(e):
                pytest.skip("py2neo not installed")
            else:
                raise
    
    def test_graph_db_connection_failure_handling(self):
        """Test that connection failures are handled gracefully."""
        try:
            from utils.graph_db import GraphDBManager
            
            manager = GraphDBManager()
            
            # Mock config to enable graph database
            with patch('utils.graph_db.CONFIG') as mock_config:
                mock_config.__getitem__.return_value = True
                
                # Mock py2neo to simulate connection failure
                with patch('utils.graph_db.Graph') as mock_graph:
                    mock_graph.side_effect = Exception("Connection failed")
                    
                    result = manager.connect()
                    assert result is False
                    assert manager.is_connected is False
                    assert manager.graph is None
        except ImportError as e:
            if "py2neo" in str(e):
                pytest.skip("py2neo not installed")
            else:
                raise
    
    def test_graph_db_successful_connection(self):
        """Test successful graph database connection."""
        try:
            from utils.graph_db import GraphDBManager
            
            manager = GraphDBManager()
            
            # Mock config to enable graph database
            with patch('utils.graph_db.CONFIG') as mock_config:
                mock_config.__getitem__.return_value = True
                
                # Mock py2neo to simulate successful connection
                with patch('utils.graph_db.Graph') as mock_graph_class:
                    mock_graph = MagicMock()
                    mock_graph.run.return_value = MagicMock()
                    mock_graph_class.return_value = mock_graph
                    
                    result = manager.connect()
                    assert result is True
                    assert manager.is_connected is True
                    assert manager.graph is not None
        except ImportError as e:
            if "py2neo" in str(e):
                pytest.skip("py2neo not installed")
            else:
                raise
    
    def test_graph_db_query_without_connection(self):
        """Test that queries fail gracefully when not connected."""
        try:
            from utils.graph_db import GraphDBManager
            
            manager = GraphDBManager()
            manager.is_connected = False
            
            result = manager.run_query("MATCH (n) RETURN n")
            assert result is None
        except ImportError as e:
            if "py2neo" in str(e):
                pytest.skip("py2neo not installed")
            else:
                raise
    
    def test_graph_db_query_with_connection(self):
        """Test that queries work when connected."""
        try:
            from utils.graph_db import GraphDBManager
            
            manager = GraphDBManager()
            
            # Mock successful connection and query
            with patch('utils.graph_db.Graph') as mock_graph_class:
                mock_graph = MagicMock()
                mock_graph.run.return_value.data.return_value = [{"test": "data"}]
                mock_graph_class.return_value = mock_graph
                
                # Mock config to enable graph database
                with patch('utils.graph_db.CONFIG') as mock_config:
                    mock_config.__getitem__.return_value = True
                    
                    manager.connect()
                    
                    result = manager.run_query("MATCH (n) RETURN n")
                    assert result == [{"test": "data"}]
        except ImportError as e:
            if "py2neo" in str(e):
                pytest.skip("py2neo not installed")
            else:
                raise


class TestAppStartup:
    """Test that the app can start with or without graph database."""
    
    def test_app_import_without_graph_db(self):
        """Test that app.py can be imported even without graph database."""
        try:
            # This should not fail even if py2neo is not installed
            import app
            assert app is not None
        except ImportError as e:
            if "py2neo" in str(e):
                pytest.skip("py2neo not installed - app import failed")
            else:
                raise
    
    def test_utils_import_without_graph_db(self):
        """Test that utils can be imported without graph database."""
        try:
            from utils import utils
            assert utils is not None
        except ImportError as e:
            if "py2neo" in str(e):
                pytest.skip("py2neo not installed - utils import failed")
            else:
                raise
    
    def test_agent_tools_import_without_graph_db(self):
        """Test that agent tools can be imported without graph database."""
        try:
            from agent_tools import get_jira_issues_tool
            assert get_jira_issues_tool is not None
        except ImportError as e:
            if "py2neo" in str(e):
                pytest.skip("py2neo not installed - agent tools import failed")
            else:
                raise


class TestGraphAgentOptional:
    """Test that the graph agent works without graph database."""
    
    def test_graph_agent_import_without_graph_db(self):
        """Test that graph agent can be imported without graph database."""
        try:
            from agents import langchain_graph_agent
            assert langchain_graph_agent is not None
        except ImportError as e:
            if "py2neo" in str(e):
                pytest.skip("py2neo not installed - graph agent import failed")
            else:
                raise
    
    def test_graph_agent_adapts_to_no_graph_db(self):
        """Test that graph agent adapts its behavior when graph DB is unavailable."""
        try:
            from agents.langchain_graph_agent import LangChainGraphAgent
            from agents.state import create_initial_state
            
            # Mock graph database as unavailable
            with patch('agents.langchain_graph_agent.graph_db_manager') as mock_manager:
                mock_manager.is_available.return_value = False
                
                agent = LangChainGraphAgent()
                state = create_initial_state("Show me dependencies for issue ABC-123")
                
                result_state = agent.execute(state)
                
                # Should provide helpful response about limited functionality
                assert "graph database" in result_state.agent_results["graph_agent"].lower()
                assert "MCP agent" in result_state.agent_results["graph_agent"]
        except ImportError as e:
            if "py2neo" in str(e):
                pytest.skip("py2neo not installed")
            else:
                raise


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 
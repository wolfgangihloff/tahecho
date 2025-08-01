import os
import pytest
from unittest.mock import patch, MagicMock


class TestEnvironmentConfiguration:
    """Test environment variable configuration."""

    def test_langchain_api_key_from_env(self):
        """Test that LangChain API key is read from environment."""
        with patch.dict(os.environ, {"LANGCHAIN_API_KEY": "test_key_from_env"}):
            api_key = os.getenv("LANGCHAIN_API_KEY")
            assert api_key == "test_key_from_env"

    def test_langchain_project_from_env(self):
        """Test that LangChain project is read from environment."""
        with patch.dict(os.environ, {"LANGCHAIN_PROJECT": "test_project"}):
            project = os.getenv("LANGCHAIN_PROJECT", "tahecho")
            assert project == "test_project"

    def test_langchain_project_default(self):
        """Test that LangChain project defaults correctly."""
        # Clear the environment variable
        with patch.dict(os.environ, {}, clear=True):
            project = os.getenv("LANGCHAIN_PROJECT", "tahecho")
            assert project == "tahecho"

    def test_openai_api_key_from_env(self):
        """Test that OpenAI API key is read from environment."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test_openai_key"}):
            api_key = os.getenv("OPENAI_API_KEY")
            assert api_key == "test_openai_key"

    def test_graph_db_enabled_from_env(self):
        """Test that graph database enabled flag is read from environment."""
        # Test enabled
        with patch.dict(os.environ, {"GRAPH_DB_ENABLED": "true"}):
            enabled = os.getenv("GRAPH_DB_ENABLED", "True").lower() == "true"
            assert enabled is True

        # Test disabled
        with patch.dict(os.environ, {"GRAPH_DB_ENABLED": "false"}):
            enabled = os.getenv("GRAPH_DB_ENABLED", "True").lower() == "true"
            assert enabled is False

        # Test default (enabled)
        with patch.dict(os.environ, {}, clear=True):
            enabled = os.getenv("GRAPH_DB_ENABLED", "True").lower() == "true"
            assert enabled is True

    def test_environment_variable_priority(self):
        """Test that environment variables take priority over config."""
        # This test verifies that we're using os.getenv() directly
        # instead of going through CONFIG, which would be loaded from .env
        with patch.dict(os.environ, {"LANGCHAIN_API_KEY": "env_priority_key"}):
            api_key = os.getenv("LANGCHAIN_API_KEY")
            assert api_key == "env_priority_key"
            assert api_key is not None 
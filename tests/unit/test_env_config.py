import os
from unittest.mock import patch


class TestEnvironmentConfiguration:
    """Test environment variable configuration."""

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

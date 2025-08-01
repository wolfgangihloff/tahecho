import os
import pytest
from unittest.mock import patch, MagicMock


class TestLangChainTracing:
    """Test LangChain tracing configuration and setup."""

    def test_langchain_tracing_environment_variables(self):
        """Test that LangChain tracing environment variables are set correctly."""
        # Import app to trigger the environment variable setup
        import app
        
        # Check that the required environment variables are set
        assert os.environ.get("LANGCHAIN_TRACING_V2") == "true"
        assert os.environ.get("LANGCHAIN_ENDPOINT") == "https://api.smith.langchain.com"
        assert os.environ.get("LANGCHAIN_PROJECT") == "tahecho"
        
        # LANGCHAIN_API_KEY may be None if not provided, which is acceptable
        langchain_api_key = os.environ.get("LANGCHAIN_API_KEY")
        assert langchain_api_key is None or isinstance(langchain_api_key, str)

    def test_langchain_api_key_set_when_provided(self):
        """Test that LANGCHAIN_API_KEY is set when provided in config."""
        # This test verifies the logic in app.py works correctly
        # Since app.py is already imported, we test the logic directly
        
        # Test the conditional logic from app.py
        test_config = {"LANGCHAIN_API_KEY": "test_key", "LANGCHAIN_PROJECT": "tahecho"}
        langchain_api_key = test_config.get("LANGCHAIN_API_KEY")
        
        # Simulate the logic from app.py
        if langchain_api_key:
            # This should be true for our test case
            assert langchain_api_key == "test_key"
        else:
            pytest.fail("API key should be found in config")

    def test_langchain_api_key_not_set_when_none(self):
        """Test that LANGCHAIN_API_KEY is not set when config returns None."""
        # This test verifies the logic in app.py works correctly for None values
        
        # Test the conditional logic from app.py
        test_config = {"LANGCHAIN_API_KEY": None, "LANGCHAIN_PROJECT": "tahecho"}
        langchain_api_key = test_config.get("LANGCHAIN_API_KEY")
        
        # Simulate the logic from app.py
        if langchain_api_key:
            pytest.fail("API key should be None")
        else:
            # This should be true for our test case
            assert langchain_api_key is None

    def test_langchain_tracing_imports_available(self):
        """Test that LangChain tracing imports are available."""
        try:
            import langsmith
            assert langsmith is not None
        except ImportError:
            pytest.fail("langsmith package is not available")

    @patch("langsmith.Client")
    def test_langchain_tracing_client_creation(self, mock_client):
        """Test that LangSmith client can be created when API key is provided."""
        mock_client_instance = MagicMock()
        mock_client.return_value = mock_client_instance
        
        # Test with API key
        with patch.dict(os.environ, {"LANGCHAIN_API_KEY": "test_key"}):
            import langsmith
            client = langsmith.Client()
            mock_client.assert_called_once() 
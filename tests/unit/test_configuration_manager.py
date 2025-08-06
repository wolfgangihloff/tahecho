import json
import os
from unittest.mock import patch

from tahecho.sitemap.configuration_manager import ConfigurationManager


class TestConfigurationManager:
    """Test cases for ConfigurationManager."""

    def test_initialization_disabled(self):
        """Test ConfigurationManager when sitemap agents are disabled."""
        with patch.dict(os.environ, {"SITEMAP_AGENTS_ENABLED": "false"}), patch("dotenv.load_dotenv"):
            config_manager = ConfigurationManager()
            assert config_manager.is_enabled() is False

    def test_get_sitemap_config(self):
        """Test getting sitemap-specific configurations."""
        sitemap_config = {
            "https://docs.aleph-alpha.com/sitemap.xml": {
                "filters": ["/docs/api", "/docs/tutorial"],
                "max_pages": 200,
                "requests_per_second": 1,
            }
        }

        with patch.dict(
            os.environ,
            {
                "SITEMAP_AGENTS_ENABLED": "true",
                "SUPABASE_URL": "https://test.supabase.co",
                "SUPABASE_ANON_KEY": "test_key",
                "SITEMAP_CONFIG": json.dumps(sitemap_config),
            },
        ), patch("dotenv.load_dotenv"):
            config_manager = ConfigurationManager()
            config = config_manager.get_sitemap_config(
                "https://docs.aleph-alpha.com/sitemap.xml"
            )

            assert config is not None
            assert config.get("filters") == ["/docs/api", "/docs/tutorial"]
            assert config.get("max_pages") == 200

    def test_get_embedding_config(self):
        """Test getting embedding configuration."""
        with patch.dict(
            os.environ,
            {
                "SITEMAP_AGENTS_ENABLED": "true",
                "SUPABASE_URL": "https://test.supabase.co",
                "SUPABASE_ANON_KEY": "test_key",
                "EMBEDDING_MODEL": "text-embedding-3-small",
                "EMBEDDING_DIMENSION": "1536",
            },
        ), patch("dotenv.load_dotenv"):
            config_manager = ConfigurationManager()
            embedding_config = config_manager.get_embedding_config()

            assert embedding_config["model"] == "text-embedding-3-small"
            assert embedding_config["dimension"] == 1536

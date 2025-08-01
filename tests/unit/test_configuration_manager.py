import pytest
import json
from unittest.mock import patch, MagicMock
import os
from typing import Dict, Any

# Import the class we'll implement
from src.tahecho.sitemap.configuration_manager import ConfigurationManager


class TestConfigurationManager:
    """Test cases for ConfigurationManager."""
    
    def test_initialization_with_valid_config(self):
        """Test ConfigurationManager initialization with valid environment variables."""
        with patch.dict(os.environ, {
            'SITEMAP_AGENTS_ENABLED': 'true',
            'SITEMAP_URLS': 'https://docs.aleph-alpha.com/sitemap.xml,https://example.com/sitemap.xml',
            'SITEMAP_REQUESTS_PER_SECOND': '2',
            'SITEMAP_MAX_PAGES': '100',
            'SUPABASE_URL': 'https://test.supabase.co',
            'SUPABASE_ANON_KEY': 'test_key',
            'EMBEDDING_MODEL': 'text-embedding-3-small'
        }):
            config_manager = ConfigurationManager()
            
            assert config_manager.is_enabled() is True
            assert len(config_manager.get_sitemap_urls()) == 2
            assert config_manager.get_requests_per_second() == 2
            assert config_manager.get_max_pages() == 100
            assert config_manager.get_supabase_url() == 'https://test.supabase.co'
    
    def test_initialization_disabled(self):
        """Test ConfigurationManager when sitemap agents are disabled."""
        with patch.dict(os.environ, {
            'SITEMAP_AGENTS_ENABLED': 'false'
        }):
            config_manager = ConfigurationManager()
            assert config_manager.is_enabled() is False
    
    def test_get_sitemap_config(self):
        """Test getting sitemap-specific configurations."""
        sitemap_config = {
            "https://docs.aleph-alpha.com/sitemap.xml": {
                "filters": ["/docs/api", "/docs/tutorial"],
                "max_pages": 200,
                "requests_per_second": 1
            }
        }
        
        with patch.dict(os.environ, {
            'SITEMAP_AGENTS_ENABLED': 'true',
            'SUPABASE_URL': 'https://test.supabase.co',
            'SUPABASE_ANON_KEY': 'test_key',
            'SITEMAP_CONFIG': json.dumps(sitemap_config)
        }):
            config_manager = ConfigurationManager()
            config = config_manager.get_sitemap_config("https://docs.aleph-alpha.com/sitemap.xml")
            
            assert config is not None
            assert config.get("filters") == ["/docs/api", "/docs/tutorial"]
            assert config.get("max_pages") == 200
    
    def test_validation_missing_required_config(self):
        """Test validation when required configuration is missing."""
        with patch.dict(os.environ, {
            'SITEMAP_AGENTS_ENABLED': 'true'
            # Missing SUPABASE_URL and other required config
        }):
            with pytest.raises(ValueError, match="Missing required configuration"):
                ConfigurationManager()
    
    def test_get_embedding_config(self):
        """Test getting embedding configuration."""
        with patch.dict(os.environ, {
            'SITEMAP_AGENTS_ENABLED': 'true',
            'SUPABASE_URL': 'https://test.supabase.co',
            'SUPABASE_ANON_KEY': 'test_key',
            'EMBEDDING_MODEL': 'text-embedding-3-small',
            'EMBEDDING_DIMENSION': '1536'
        }):
            config_manager = ConfigurationManager()
            embedding_config = config_manager.get_embedding_config()
            
            assert embedding_config["model"] == "text-embedding-3-small"
            assert embedding_config["dimension"] == 1536
    
    def test_load_yaml_config(self):
        """Test loading configuration from YAML file."""
        yaml_content = """
        sitemaps:
          aleph_alpha:
            url: https://docs.aleph-alpha.com/sitemap.xml
            filters:
              - /docs/api
              - /docs/tutorial
            max_pages: 200
            requests_per_second: 1
        """
        
        with patch('builtins.open', create=True) as mock_open:
            mock_open.return_value.__enter__.return_value.read.return_value = yaml_content
            
            config_manager = ConfigurationManager()
            config_manager.load_yaml_config("test_config.yaml")
            
            # Test that YAML config is loaded
            assert "aleph_alpha" in config_manager._yaml_config.get("sitemaps", {})
    
    def test_get_processing_config(self):
        """Test getting processing configuration."""
        with patch.dict(os.environ, {
            'SITEMAP_AGENTS_ENABLED': 'true',
            'SUPABASE_URL': 'https://test.supabase.co',
            'SUPABASE_ANON_KEY': 'test_key',
            'ASYNC_PROCESSING_ENABLED': 'true',
            'PROCESSING_BATCH_SIZE': '10',
            'CLEANUP_AFTER_UPLOAD': 'true'
        }):
            config_manager = ConfigurationManager()
            processing_config = config_manager.get_processing_config()
            
            assert processing_config["async_enabled"] is True
            assert processing_config["batch_size"] == 10
            assert processing_config["cleanup_after_upload"] is True 
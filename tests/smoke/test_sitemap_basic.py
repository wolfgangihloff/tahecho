"""Basic smoke test for sitemap components."""

import pytest
from unittest.mock import patch, MagicMock
import os

# Import the components
from src.tahecho.sitemap.configuration_manager import ConfigurationManager
from src.tahecho.sitemap.supabase_integration import SupabaseIntegration
from src.tahecho.sitemap.embedding_generator import EmbeddingGenerator


class TestSitemapBasic:
    """Basic smoke tests for sitemap components."""
    
    def test_configuration_manager_basic(self):
        """Test basic configuration manager functionality."""
        with patch.dict(os.environ, {
            'SITEMAP_AGENTS_ENABLED': 'true',
            'SUPABASE_URL': 'https://test.supabase.co',
            'SUPABASE_ANON_KEY': 'test_key',
            'SITEMAP_URLS': 'https://docs.aleph-alpha.com/sitemap.xml'
        }):
            config_manager = ConfigurationManager()
            
            assert config_manager.is_enabled() is True
            assert len(config_manager.get_sitemap_urls()) == 1
            assert config_manager.get_supabase_url() == 'https://test.supabase.co'
    
    def test_supabase_integration_basic(self):
        """Test basic Supabase integration functionality."""
        with patch('src.tahecho.sitemap.supabase_integration.create_client') as mock_create:
            mock_client = MagicMock()
            mock_create.return_value = mock_client
            
            integration = SupabaseIntegration(
                url='https://test.supabase.co',
                anon_key='test_key'
            )
            
            assert integration.url == 'https://test.supabase.co'
            assert integration.anon_key == 'test_key'
            assert integration.embedding_dimension == 1536
    
    def test_embedding_generator_basic(self):
        """Test basic embedding generator functionality."""
        with patch('openai.AsyncOpenAI') as mock_openai:
            mock_client = MagicMock()
            mock_openai.return_value = mock_client
            
            config = {
                'model': 'text-embedding-3-small',
                'dimension': 1536
            }
            
            generator = EmbeddingGenerator(config)
            
            assert generator.model == 'text-embedding-3-small'
            assert generator.dimension == 1536
    
    def test_content_hash_generation(self):
        """Test content hash generation."""
        with patch('src.tahecho.sitemap.supabase_integration.create_client') as mock_create:
            mock_client = MagicMock()
            mock_create.return_value = mock_client
            
            integration = SupabaseIntegration(
                url='https://test.supabase.co',
                anon_key='test_key'
            )
            
            content = "This is test content"
            hash1 = integration.generate_content_hash(content)
            hash2 = integration.generate_content_hash(content)
            
            # Same content should generate same hash
            assert hash1 == hash2
            
            # Different content should generate different hash
            hash3 = integration.generate_content_hash("Different content")
            assert hash1 != hash3
    
    def test_embedding_validation(self):
        """Test embedding dimension validation."""
        with patch('src.tahecho.sitemap.supabase_integration.create_client') as mock_create:
            mock_client = MagicMock()
            mock_create.return_value = mock_client
            
            integration = SupabaseIntegration(
                url='https://test.supabase.co',
                anon_key='test_key'
            )
            
            # Valid embedding
            valid_embedding = [0.1] * 1536
            assert integration.validate_embedding_dimension(valid_embedding) is True
            
            # Invalid embedding
            invalid_embedding = [0.1] * 100
            assert integration.validate_embedding_dimension(invalid_embedding) is False
    
    def test_sitemap_url_validation(self):
        """Test sitemap URL validation."""
        with patch.dict(os.environ, {
            'SITEMAP_AGENTS_ENABLED': 'true',
            'SUPABASE_URL': 'https://test.supabase.co',
            'SUPABASE_ANON_KEY': 'test_key'
        }):
            config_manager = ConfigurationManager()
            
            # Valid URLs
            assert config_manager.validate_sitemap_url('https://docs.aleph-alpha.com/sitemap.xml') is True
            assert config_manager.validate_sitemap_url('https://example.com/sitemap.xml') is True
            
            # Invalid URLs
            assert config_manager.validate_sitemap_url('not-a-url') is False
            assert config_manager.validate_sitemap_url('') is False
    
    def test_domain_extraction(self):
        """Test domain extraction from URLs."""
        with patch.dict(os.environ, {
            'SITEMAP_AGENTS_ENABLED': 'true',
            'SUPABASE_URL': 'https://test.supabase.co',
            'SUPABASE_ANON_KEY': 'test_key'
        }):
            config_manager = ConfigurationManager()
            
            domain = config_manager.get_sitemap_domain('https://docs.aleph-alpha.com/sitemap.xml')
            assert domain == 'docs.aleph-alpha.com'
            
            domain = config_manager.get_sitemap_domain('https://example.com/sitemap.xml')
            assert domain == 'example.com' 
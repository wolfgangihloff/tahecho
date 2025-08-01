import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import os
from typing import Dict, Any, List

# Import the class we'll implement
from src.tahecho.sitemap.supabase_integration import SupabaseIntegration


class TestSupabaseIntegration:
    """Test cases for Supabase integration."""
    
    @pytest.fixture
    def mock_supabase_client(self):
        """Mock Supabase client."""
        with patch('src.tahecho.sitemap.supabase_integration.create_client') as mock_create:
            mock_client = MagicMock()
            mock_create.return_value = mock_client
            yield mock_client
    
    @pytest.fixture
    def supabase_config(self):
        """Supabase configuration for testing."""
        return {
            'url': 'https://test.supabase.co',
            'anon_key': 'test_anon_key',
            'service_key': 'test_service_key'
        }
    
    def test_initialization(self, mock_supabase_client, supabase_config):
        """Test SupabaseIntegration initialization."""
        integration = SupabaseIntegration(**supabase_config)
        
        assert integration.url == supabase_config['url']
        assert integration.anon_key == supabase_config['anon_key']
        assert integration.service_key == supabase_config['service_key']
    
    @pytest.mark.asyncio
    async def test_create_sitemap_record(self, mock_supabase_client, supabase_config):
        """Test creating a sitemap record."""
        integration = SupabaseIntegration(**supabase_config)
        
        sitemap_data = {
            'url': 'https://docs.aleph-alpha.com/sitemap.xml',
            'domain': 'docs.aleph-alpha.com',
            'total_pages': 150,
            'config': {'filters': ['/docs/api']}
        }
        
        mock_supabase_client.table.return_value.insert.return_value.execute.return_value.data = [{'id': 'test-uuid'}]
        
        result = await integration.create_sitemap_record(sitemap_data)
        
        assert result['id'] == 'test-uuid'
        mock_supabase_client.table.assert_called_with('sitemaps')
    
    @pytest.mark.asyncio
    async def test_create_web_page_record(self, mock_supabase_client, supabase_config):
        """Test creating a web page record with embedding."""
        integration = SupabaseIntegration(**supabase_config)
        
        page_data = {
            'sitemap_id': 'test-sitemap-id',
            'url': 'https://docs.aleph-alpha.com/docs/api',
            'title': 'API Documentation',
            'content': 'This is the API documentation content...',
            'content_preview': 'This is the API documentation...',
            'embedding': [0.1, 0.2, 0.3] * 512  # 1536 dimensions
        }
        
        mock_supabase_client.table.return_value.insert.return_value.execute.return_value.data = [{'id': 'test-page-uuid'}]
        
        result = await integration.create_web_page_record(page_data)
        
        assert result['id'] == 'test-page-uuid'
        mock_supabase_client.table.assert_called_with('web_pages')
    
    @pytest.mark.asyncio
    async def test_search_similar_content(self, mock_supabase_client, supabase_config):
        """Test searching for similar content using vector similarity."""
        integration = SupabaseIntegration(**supabase_config)
        
        query_embedding = [0.1, 0.2, 0.3] * 512
        mock_supabase_client.rpc.return_value.execute.return_value.data = [
            {
                'id': 'test-page-1',
                'url': 'https://docs.aleph-alpha.com/docs/api',
                'title': 'API Documentation',
                'content_preview': 'API documentation content...',
                'similarity': 0.95
            }
        ]
        
        results = await integration.search_similar_content(query_embedding, limit=5)
        
        assert len(results) == 1
        assert results[0]['similarity'] == 0.95
        mock_supabase_client.rpc.assert_called()
    
    @pytest.mark.asyncio
    async def test_get_sitemap_by_url(self, mock_supabase_client, supabase_config):
        """Test getting sitemap by URL."""
        integration = SupabaseIntegration(**supabase_config)
        
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
            {
                'id': 'test-sitemap-id',
                'url': 'https://docs.aleph-alpha.com/sitemap.xml',
                'domain': 'docs.aleph-alpha.com',
                'total_pages': 150
            }
        ]
        
        result = await integration.get_sitemap_by_url('https://docs.aleph-alpha.com/sitemap.xml')
        
        assert result['id'] == 'test-sitemap-id'
        assert result['url'] == 'https://docs.aleph-alpha.com/sitemap.xml'
    
    @pytest.mark.asyncio
    async def test_get_web_page_by_url(self, mock_supabase_client, supabase_config):
        """Test getting web page by URL."""
        integration = SupabaseIntegration(**supabase_config)
        
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
            {
                'id': 'test-page-id',
                'url': 'https://docs.aleph-alpha.com/docs/api',
                'title': 'API Documentation',
                'content': 'API content...',
                'content_hash': 'abc123'
            }
        ]
        
        result = await integration.get_web_page_by_url('https://docs.aleph-alpha.com/docs/api')
        
        assert result['id'] == 'test-page-id'
        assert result['url'] == 'https://docs.aleph-alpha.com/docs/api'
    
    @pytest.mark.asyncio
    async def test_update_web_page_content(self, mock_supabase_client, supabase_config):
        """Test updating web page content."""
        integration = SupabaseIntegration(**supabase_config)
        
        page_id = 'test-page-id'
        new_content = 'Updated content...'
        new_embedding = [0.4, 0.5, 0.6] * 512
        
        mock_supabase_client.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [
            {'id': page_id, 'content': new_content}
        ]
        
        result = await integration.update_web_page_content(page_id, new_content, new_embedding)
        
        assert result['id'] == page_id
        assert result['content'] == new_content
    
    @pytest.mark.asyncio
    async def test_delete_old_sitemap_data(self, mock_supabase_client, supabase_config):
        """Test deleting old sitemap data."""
        integration = SupabaseIntegration(**supabase_config)
        
        sitemap_id = 'test-sitemap-id'
        mock_supabase_client.table.return_value.delete.return_value.eq.return_value.execute.return_value.data = []
        
        await integration.delete_old_sitemap_data(sitemap_id)
        
        mock_supabase_client.table.assert_called_with('web_pages')
    
    def test_validate_embedding_dimension(self, supabase_config):
        """Test embedding dimension validation."""
        integration = SupabaseIntegration(**supabase_config)
        
        # Valid embedding
        valid_embedding = [0.1] * 1536
        assert integration.validate_embedding_dimension(valid_embedding) is True
        
        # Invalid embedding
        invalid_embedding = [0.1] * 100
        assert integration.validate_embedding_dimension(invalid_embedding) is False 
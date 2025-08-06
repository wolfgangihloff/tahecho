import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tahecho.sitemap.supabase_integration import SupabaseIntegration


class TestSupabaseIntegration:
    """Test cases for SupabaseIntegration."""

    def test_initialization(self):
        """Test SupabaseIntegration initialization."""
        with patch("tahecho.sitemap.supabase_integration.create_client") as mock_create_client:
            mock_client = MagicMock()
            mock_create_client.return_value = mock_client

            integration = SupabaseIntegration("https://test.supabase.co", "test_key")

            assert integration.url == "https://test.supabase.co"
            assert integration.anon_key == "test_key"
            assert integration.client == mock_client
            assert integration.embedding_dimension == 1536

    @pytest.mark.asyncio
    async def test_create_document(self):
        """Test creating a document record."""
        with patch("tahecho.sitemap.supabase_integration.create_client") as mock_create_client:
            mock_client = MagicMock()
            mock_create_client.return_value = mock_client

            # Mock the table and insert operations
            mock_table = MagicMock()
            mock_insert = MagicMock()
            mock_execute = MagicMock()
            mock_client.table.return_value = mock_table
            mock_table.insert.return_value = mock_insert
            mock_insert.execute.return_value = mock_execute
            mock_execute.data = [{"id": "test_id", "content": "test content"}]

            integration = SupabaseIntegration("https://test.supabase.co", "test_key")

            document_data = {"content": "test content", "url": "https://example.com"}
            result = await integration.create_document(document_data)

            assert result["id"] == "test_id"
            assert result["content"] == "test content"
            mock_client.table.assert_called_with("documents")

    @pytest.mark.asyncio
    async def test_get_sitemap_by_url(self):
        """Test getting sitemap by URL."""
        with patch("tahecho.sitemap.supabase_integration.create_client") as mock_create_client:
            mock_client = MagicMock()
            mock_create_client.return_value = mock_client

            # Mock the table and select operations
            mock_table = MagicMock()
            mock_select = MagicMock()
            mock_eq = MagicMock()
            mock_execute = MagicMock()
            mock_client.table.return_value = mock_table
            mock_table.select.return_value = mock_select
            mock_select.eq.return_value = mock_eq
            mock_eq.execute.return_value = mock_execute
            mock_execute.data = [{"id": "test_id", "url": "https://example.com/sitemap.xml"}]

            integration = SupabaseIntegration("https://test.supabase.co", "test_key")

            result = await integration.get_sitemap_by_url("https://example.com/sitemap.xml")

            assert result["id"] == "test_id"
            assert result["url"] == "https://example.com/sitemap.xml"

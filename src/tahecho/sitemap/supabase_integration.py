"""Supabase integration for sitemap data storage."""

import asyncio
import hashlib
import logging
import warnings
from typing import Any, Dict, List, Optional

from supabase import Client, create_client

# Suppress GoTrue client cleanup warnings
warnings.filterwarnings("ignore", message=".*_refresh_token_timer.*")

logger = logging.getLogger(__name__)


class SupabaseIntegration:
    """Handles Supabase operations for sitemap data."""

    def __init__(self, url: str, anon_key: str, service_key: Optional[str] = None):
        """Initialize Supabase integration."""
        self.url = url
        self.anon_key = anon_key
        self.service_key = service_key
        self.client = None  # Initialize client as None by default (mock mode)

        try:
            import warnings

            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                self.client: Client = create_client(url, anon_key)
                logger.info("Supabase client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {e}")
            logger.warning("Using mock mode for Supabase operations")
            logger.info(
                "This is normal if Supabase is not configured or there are library compatibility issues"
            )
            self.client = None

        self.embedding_dimension = 1536  # OpenAI text-embedding-3-small dimension

    async def create_document(self, document_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new document record."""
        if self.client is None:
            import uuid

            mock_id = str(uuid.uuid4())
            logger.info(f"Mock: Created document record: {mock_id}")
            return {"id": mock_id, **document_data}

        try:
            # Validate embedding dimension if present
            if "embedding" in document_data:
                embedding = document_data["embedding"]
                if len(embedding) != self.embedding_dimension:
                    raise ValueError(
                        f"Embedding dimension {len(embedding)} does not match expected {self.embedding_dimension}"
                    )

            response = self.client.table("documents").insert(document_data).execute()

            if response.data:
                logger.info(f"Created document: {response.data[0]['id']}")
                return response.data[0]
            else:
                raise Exception("No data returned from document creation")

        except Exception as e:
            logger.error(f"Failed to create document: {e}")
            raise

    async def search_similar_documents(
        self,
        query_embedding: List[float],
        source_types: Optional[List[str]] = None,
        limit: int = 10,
        similarity_threshold: float = 0.7,
    ) -> List[Dict[str, Any]]:
        """Search for similar documents using vector similarity."""
        if self.client is None:
            logger.info("Mock: No similar documents found")
            return []

        try:
            # Validate embedding dimension
            if len(query_embedding) != self.embedding_dimension:
                raise ValueError(
                    f"Query embedding dimension {len(query_embedding)} does not match expected {self.embedding_dimension}"
                )

            # Build the query
            query = self.client.table("documents").select("*")

            # Filter by source types if specified
            if source_types:
                query = query.in_("source_type", source_types)

            # Add vector similarity search
            query = query.rpc(
                "match_documents",
                {
                    "query_embedding": query_embedding,
                    "match_threshold": similarity_threshold,
                    "match_count": limit,
                },
            )

            response = query.execute()

            if response.data:
                logger.info(f"Found {len(response.data)} similar documents")
                return response.data
            else:
                return []

        except Exception as e:
            logger.error(f"Failed to search similar documents: {e}")
            return []

    async def get_document_by_url(self, url: str) -> Optional[Dict[str, Any]]:
        """Get document by URL."""
        if self.client is None:
            logger.info(f"Mock: No document found for URL {url}")
            return None

        try:
            response = (
                self.client.table("documents").select("*").eq("url", url).execute()
            )

            if response.data:
                return response.data[0]
            else:
                return None

        except Exception as e:
            logger.error(f"Failed to get document by URL: {e}")
            return None

    async def get_documents_by_source(
        self, source_type: str, source_id: Optional[str] = None, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get documents by source type and optionally source ID."""
        if self.client is None:
            logger.info(f"Mock: No documents found for source {source_type}")
            return []

        try:
            query = (
                self.client.table("documents")
                .select("*")
                .eq("source_type", source_type)
            )

            if source_id:
                query = query.eq("source_id", source_id)

            response = query.limit(limit).execute()

            if response.data:
                logger.info(
                    f"Found {len(response.data)} documents for source {source_type}"
                )
                return response.data
            else:
                return []

        except Exception as e:
            logger.error(f"Failed to get documents by source: {e}")
            return []

    async def update_document(
        self, document_id: str, update_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Update an existing document."""
        if self.client is None:
            logger.info(f"Mock: Updated document {document_id}")
            return {"id": document_id, **update_data}

        try:
            # Validate embedding dimension if present
            if "embedding" in update_data:
                embedding = update_data["embedding"]
                if len(embedding) != self.embedding_dimension:
                    raise ValueError(
                        f"Embedding dimension {len(embedding)} does not match expected {self.embedding_dimension}"
                    )

            response = (
                self.client.table("documents")
                .update(update_data)
                .eq("id", document_id)
                .execute()
            )

            if response.data:
                logger.info(f"Updated document: {document_id}")
                return response.data[0]
            else:
                return None

        except Exception as e:
            logger.error(f"Failed to update document: {e}")
            return None

    async def delete_old_documents(
        self, source_type: str, older_than_days: int = 30
    ) -> int:
        """Delete old documents of a specific source type."""
        if self.client is None:
            logger.info(f"Mock: Deleted old documents for source {source_type}")
            return 0

        try:
            from datetime import datetime, timedelta

            cutoff_date = datetime.utcnow() - timedelta(days=older_than_days)

            response = (
                self.client.table("documents")
                .delete()
                .eq("source_type", source_type)
                .lt("created_at", cutoff_date.isoformat())
                .execute()
            )

            deleted_count = len(response.data) if response.data else 0
            logger.info(
                f"Deleted {deleted_count} old documents for source {source_type}"
            )
            return deleted_count

        except Exception as e:
            logger.error(f"Failed to delete old documents: {e}")
            return 0

    async def create_content_source(
        self, source_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a new content source record."""
        if self.client is None:
            import uuid

            mock_id = str(uuid.uuid4())
            logger.info(f"Mock: Created content source: {mock_id}")
            return {"id": mock_id, **source_data}

        try:
            response = (
                self.client.table("content_sources").insert(source_data).execute()
            )

            if response.data:
                logger.info(f"Created content source: {response.data[0]['id']}")
                return response.data[0]
            else:
                raise Exception("No data returned from content source creation")

        except Exception as e:
            logger.error(f"Failed to create content source: {e}")
            raise

    async def get_content_sources(
        self, source_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get content sources, optionally filtered by type."""
        if self.client is None:
            logger.info("Mock: No content sources found")
            return []

        try:
            query = self.client.table("content_sources").select("*")

            if source_type:
                query = query.eq("source_type", source_type)

            response = query.execute()

            if response.data:
                return response.data
            else:
                return []

        except Exception as e:
            logger.error(f"Failed to get content sources: {e}")
            return []

    # Legacy methods for backward compatibility (now map to document methods)
    async def create_sitemap_record(
        self, sitemap_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Legacy method: Create a sitemap record as a document."""
        document_data = {
            "title": f"Sitemap: {sitemap_data.get('url', 'Unknown')}",
            "url": sitemap_data.get("url"),
            "content": f"Sitemap containing {sitemap_data.get('total_pages', 0)} pages",
            "content_preview": f"Sitemap with {sitemap_data.get('total_pages', 0)} pages",
            "content_hash": sitemap_data.get("content_hash"),
            "source_type": "sitemap",
            "source_id": sitemap_data.get("id"),
            "source_url": sitemap_data.get("url"),
            "domain": sitemap_data.get("domain"),
            "metadata": {
                "total_pages": sitemap_data.get("total_pages"),
                "config": sitemap_data.get("config", {}),
                "status": sitemap_data.get("status", "active"),
            },
            "tags": ["sitemap", "index"],
        }
        return await self.create_document(document_data)

    async def create_web_page_record(self, page_data: Dict[str, Any]) -> Dict[str, Any]:
        """Legacy method: Create a web page record as a document."""
        document_data = {
            "title": page_data.get("title"),
            "url": page_data.get("url"),
            "content": page_data.get("content"),
            "content_preview": page_data.get("content_preview"),
            "content_hash": page_data.get("content_hash"),
            "source_type": "sitemap",
            "source_id": page_data.get("sitemap_id"),
            "source_url": page_data.get("url"),
            "domain": page_data.get("domain"),
            "metadata": page_data.get("metadata", {}),
            "embedding": page_data.get("embedding"),
            "tags": ["webpage", "sitemap"],
        }
        return await self.create_document(document_data)

    async def get_sitemap_by_url(self, sitemap_url: str) -> Optional[Dict[str, Any]]:
        """Legacy method: Get sitemap document by URL."""
        return await self.get_document_by_url(sitemap_url)

    async def get_sitemap_pages(
        self, sitemap_id: str, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Legacy method: Get web page documents for a sitemap."""
        return await self.get_documents_by_source("sitemap", sitemap_id, limit)

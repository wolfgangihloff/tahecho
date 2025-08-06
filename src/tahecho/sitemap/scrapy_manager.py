"""Scrapy manager for sitemap scraping operations."""

import asyncio
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .configuration_manager import ConfigurationManager
from .embedding_generator import EmbeddingGenerator
from .supabase_integration import SupabaseIntegration

logger = logging.getLogger(__name__)


class ScrapyManager:
    """Manages Scrapy-based sitemap scraping operations."""

    def __init__(self, config_manager: ConfigurationManager):
        """Initialize Scrapy manager."""
        self.config_manager = config_manager
        self.supabase = SupabaseIntegration(
            url=config_manager.get_supabase_url(),
            anon_key=config_manager.get_supabase_anon_key(),
            service_key=config_manager.get_supabase_service_key(),
        )
        self.embedding_generator = EmbeddingGenerator(
            config_manager.get_embedding_config()
        )
        self.operations: Dict[str, Dict[str, Any]] = {}

    async def scrape_sitemap(
        self,
        url: str,
        incremental: bool = False,
        differential: bool = False,
        config: Dict[str, Any] = None,
    ) -> str:
        """Start a sitemap scraping operation."""
        operation_id = str(uuid.uuid4())

        # Initialize operation
        self.operations[operation_id] = {
            "id": operation_id,
            "url": url,
            "status": "running",
            "progress": 0,
            "started_at": datetime.now().isoformat(),
            "incremental": incremental,
            "differential": differential,
            "config": config or {},
            "error": None,
        }

        # Start scraping in background
        asyncio.create_task(self._run_scraping_operation(operation_id))

        return operation_id

    async def update_sitemap(
        self,
        url: str,
        incremental: bool = True,
        differential: bool = False,
        config: Dict[str, Any] = None,
    ) -> str:
        """Update existing sitemap data."""
        operation_id = str(uuid.uuid4())

        # Initialize operation
        self.operations[operation_id] = {
            "id": operation_id,
            "url": url,
            "status": "running",
            "progress": 0,
            "started_at": datetime.now().isoformat(),
            "incremental": incremental,
            "differential": differential,
            "config": config or {},
            "error": None,
            "type": "update",
        }

        # Start update in background
        asyncio.create_task(self._run_update_operation(operation_id))

        return operation_id

    async def get_operation_status(self, operation_id: str) -> Dict[str, Any]:
        """Get status of a specific operation."""
        if operation_id not in self.operations:
            raise ValueError(f"Operation {operation_id} not found")

        return self.operations[operation_id].copy()

    async def get_recent_operations(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent operations."""
        sorted_operations = sorted(
            self.operations.values(), key=lambda x: x["started_at"], reverse=True
        )
        return sorted_operations[:limit]

    async def _run_scraping_operation(self, operation_id: str):
        """Run the actual scraping operation."""
        operation = self.operations[operation_id]

        try:
            logger.info(
                f"Starting scraping operation {operation_id} for {operation['url']}"
            )

            # Update progress
            operation["progress"] = 10

            # Check if sitemap exists
            existing_sitemap = await self.supabase.get_sitemap_by_url(operation["url"])

            if existing_sitemap and operation["incremental"]:
                # Incremental update
                await self._run_incremental_update(operation_id, existing_sitemap)
            else:
                # Full scrape
                await self._run_full_scrape(operation_id)

            # Mark as completed
            operation["status"] = "completed"
            operation["progress"] = 100
            operation["completed_at"] = datetime.now().isoformat()

            logger.info(f"Scraping operation {operation_id} completed successfully")

        except Exception as e:
            logger.error(f"Scraping operation {operation_id} failed: {e}")
            operation["status"] = "failed"
            operation["error"] = str(e)
            operation["completed_at"] = datetime.now().isoformat()

    async def _run_update_operation(self, operation_id: str):
        """Run update operation."""
        operation = self.operations[operation_id]

        try:
            logger.info(
                f"Starting update operation {operation_id} for {operation['url']}"
            )

            # Get existing sitemap
            existing_sitemap = await self.supabase.get_sitemap_by_url(operation["url"])
            if not existing_sitemap:
                raise ValueError(f"Sitemap {operation['url']} not found in database")

            if operation["differential"]:
                await self._run_differential_update(operation_id, existing_sitemap)
            else:
                await self._run_incremental_update(operation_id, existing_sitemap)

            # Mark as completed
            operation["status"] = "completed"
            operation["progress"] = 100
            operation["completed_at"] = datetime.now().isoformat()

            logger.info(f"Update operation {operation_id} completed successfully")

        except Exception as e:
            logger.error(f"Update operation {operation_id} failed: {e}")
            operation["status"] = "failed"
            operation["error"] = str(e)
            operation["completed_at"] = datetime.now().isoformat()

    async def _run_full_scrape(self, operation_id: str):
        """Run full sitemap scraping."""
        operation = self.operations[operation_id]
        url = operation["url"]
        config = operation["config"]

        # Update progress
        operation["progress"] = 20

        # Create sitemap record
        sitemap_data = {
            "url": url,
            "domain": self.config_manager.get_sitemap_domain(url),
            "total_pages": 0,  # Will be updated after scraping
            "config": config,
        }

        sitemap_record = await self.supabase.create_sitemap_record(sitemap_data)

        # Update progress
        operation["progress"] = 30

        # TODO: Implement actual Scrapy scraping
        # For now, we'll simulate the process
        await self._simulate_scraping(operation_id, sitemap_record["id"])

    async def _run_incremental_update(
        self, operation_id: str, existing_sitemap: Dict[str, Any]
    ):
        """Run incremental update."""
        operation = self.operations[operation_id]

        # Update progress
        operation["progress"] = 40

        # TODO: Implement incremental update logic
        # 1. Get existing pages
        # 2. Check for changes using content hashes
        # 3. Update only changed pages

        await self._simulate_incremental_update(operation_id, existing_sitemap["id"])

    async def _run_differential_update(
        self, operation_id: str, existing_sitemap: Dict[str, Any]
    ):
        """Run differential update for specific sections."""
        operation = self.operations[operation_id]
        config = operation["config"]

        # Update progress
        operation["progress"] = 50

        differential_sections = config.get("differential_sections", [])
        if not differential_sections:
            raise ValueError("No differential sections specified")

        # TODO: Implement differential update logic
        # 1. Filter pages by sections
        # 2. Update only those sections

        await self._simulate_differential_update(
            operation_id, existing_sitemap["id"], differential_sections
        )

    async def _simulate_scraping(self, operation_id: str, sitemap_id: str):
        """Simulate scraping process for testing."""
        operation = self.operations[operation_id]

        # Simulate progress updates
        for progress in range(40, 90, 10):
            await asyncio.sleep(1)  # Simulate work
            operation["progress"] = progress

        # Simulate creating some web pages
        sample_pages = [
            {
                "sitemap_id": sitemap_id,
                "url": f"{operation['url']}/page1",
                "title": "Sample Page 1",
                "content": "This is sample content for page 1.",
                "content_preview": "This is sample content...",
                "embedding": [0.1] * 1536,  # Dummy embedding
            },
            {
                "sitemap_id": sitemap_id,
                "url": f"{operation['url']}/page2",
                "title": "Sample Page 2",
                "content": "This is sample content for page 2.",
                "content_preview": "This is sample content...",
                "embedding": [0.2] * 1536,  # Dummy embedding
            },
        ]

        for page_data in sample_pages:
            await self.supabase.create_web_page_record(page_data)

        operation["progress"] = 90

    async def _simulate_incremental_update(self, operation_id: str, sitemap_id: str):
        """Simulate incremental update process."""
        operation = self.operations[operation_id]

        # Simulate progress updates
        for progress in range(60, 90, 10):
            await asyncio.sleep(0.5)  # Simulate work
            operation["progress"] = progress

        # Simulate updating one page
        existing_pages = await self.supabase.get_sitemap_pages(sitemap_id, limit=1)
        if existing_pages:
            page = existing_pages[0]
            updated_content = f"{page['content']} (Updated at {datetime.now()})"
            new_embedding = [0.3] * 1536  # Dummy embedding

            await self.supabase.update_web_page_content(
                page["id"], updated_content, new_embedding
            )

        operation["progress"] = 90

    async def _simulate_differential_update(
        self, operation_id: str, sitemap_id: str, sections: List[str]
    ):
        """Simulate differential update process."""
        operation = self.operations[operation_id]

        # Simulate progress updates
        for progress in range(60, 90, 10):
            await asyncio.sleep(0.5)  # Simulate work
            operation["progress"] = progress

        # Simulate updating pages for specific sections
        logger.info(f"Updating sections: {sections}")

        operation["progress"] = 90

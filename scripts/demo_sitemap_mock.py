#!/usr/bin/env python3
"""Mock demo script for sitemap functionality (no real Supabase required)."""

import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from unittest.mock import patch, MagicMock

# Load environment variables from .env file
load_dotenv()

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from tahecho.sitemap.configuration_manager import ConfigurationManager
from tahecho.sitemap.scrapy_manager import ScrapyManager


async def demo_sitemap_functionality_mock() -> None:
    """Demo the sitemap functionality with mocked components."""
    print("🚀 Tahecho Sitemap Awareness Demo (Mock Mode)")
    print("=" * 50)
    
    # Set up demo environment variables (only if not already set)
    demo_env = {
        'SITEMAP_AGENTS_ENABLED': 'true',
        'SITEMAP_URLS': 'https://docs.aleph-alpha.com/sitemap.xml',
        'SITEMAP_CONFIG': '{"https://docs.aleph-alpha.com/sitemap.xml": {"filters": ["/docs/api", "/docs/tutorial"], "max_pages": 10}}',
        'EMBEDDING_MODEL': 'text-embedding-3-small',
        'EMBEDDING_DIMENSION': '1536'
    }
    
    # Apply demo environment only if not already set
    for key, value in demo_env.items():
        if not os.getenv(key):
            os.environ[key] = value
    
    try:
        # Initialize components with mocked Supabase
        print("📋 Initializing Configuration Manager...")
        config_manager = ConfigurationManager()
        
        if not config_manager.is_enabled():
            print("❌ Sitemap agents are disabled")
            return
        
        print("✅ Configuration Manager initialized")
        print(f"   - Sitemap URLs: {config_manager.get_sitemap_urls()}")
        print(f"   - Requests per second: {config_manager.get_requests_per_second()}")
        print(f"   - Max pages: {config_manager.get_max_pages()}")
        
        # Initialize Scrapy Manager with mocked Supabase
        print("\n🕷️  Initializing Scrapy Manager (Mock Mode)...")
        
        with patch('tahecho.sitemap.supabase_integration.create_client') as mock_create, \
             patch('tahecho.sitemap.embedding_generator.openai.AsyncOpenAI') as mock_openai:
            
            # Mock Supabase client
            mock_supabase_client = MagicMock()
            mock_create.return_value = mock_supabase_client
            
            # Mock OpenAI client
            mock_openai_client = MagicMock()
            mock_openai.return_value = mock_openai_client
            
            scrapy_manager = ScrapyManager(config_manager)
            print("✅ Scrapy Manager initialized (Mock Mode)")
        
        # Demo sitemap scraping
        print("\n🔍 Demo: Sitemap Scraping (Mock Mode)")
        print("-" * 30)
        
        sitemap_url = "https://docs.aleph-alpha.com/sitemap.xml"
        print(f"Starting scraping operation for: {sitemap_url}")
        
        # Start scraping operation
        operation_id = await scrapy_manager.scrape_sitemap(
            url=sitemap_url,
            incremental=False,
            differential=False,
            config={
                'filters': ['/docs/api', '/docs/tutorial'],
                'max_pages': 5
            }
        )
        
        print(f"✅ Scraping operation started with ID: {operation_id}")
        
        # Monitor progress
        print("\n📊 Monitoring Progress...")
        for i in range(5):
            await asyncio.sleep(2)
            status = await scrapy_manager.get_operation_status(operation_id)
            print(f"   Progress: {status['progress']}% - Status: {status['status']}")
            
            if status['status'] in ['completed', 'failed']:
                break
        
        # Show final status
        final_status = await scrapy_manager.get_operation_status(operation_id)
        print(f"\n🎯 Final Status: {final_status['status']}")
        
        if final_status['status'] == 'completed':
            print("✅ Scraping completed successfully!")
        elif final_status['status'] == 'failed':
            print(f"❌ Scraping failed: {final_status.get('error', 'Unknown error')}")
        
        # Demo incremental update
        print("\n🔄 Demo: Incremental Update (Mock Mode)")
        print("-" * 30)
        
        update_operation_id = await scrapy_manager.update_sitemap(
            url=sitemap_url,
            incremental=True,
            differential=False
        )
        
        print(f"✅ Update operation started with ID: {update_operation_id}")
        
        # Monitor update progress
        for i in range(3):
            await asyncio.sleep(1)
            status = await scrapy_manager.get_operation_status(update_operation_id)
            print(f"   Progress: {status['progress']}% - Status: {status['status']}")
            
            if status['status'] in ['completed', 'failed']:
                break
        
        # Show recent operations
        print("\n📋 Recent Operations:")
        print("-" * 30)
        recent_ops = await scrapy_manager.get_recent_operations(limit=3)
        for op in recent_ops:
            print(f"   {op['id'][:8]}... - {op['status']} - {op['progress']}%")
        
        print("\n🎉 Demo completed successfully!")
        print("\nNext steps for production:")
        print("1. Set up real Supabase instance with pgvector extension")
        print("2. Verify your Supabase credentials in .env file")
        print("3. Run: python scripts/manage_sitemaps.py scrape --url https://docs.aleph-alpha.com/sitemap.xml")
        print("4. Query scraped content through the Tahecho agent")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    asyncio.run(demo_sitemap_functionality_mock()) 
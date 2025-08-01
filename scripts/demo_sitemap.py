#!/usr/bin/env python3
"""Demo script for sitemap functionality."""

import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from tahecho.sitemap.configuration_manager import ConfigurationManager
from tahecho.sitemap.supabase_integration import SupabaseIntegration
from tahecho.sitemap.scrapy_manager import ScrapyManager


async def demo_sitemap_functionality():
    """Demo the sitemap functionality."""
    print("🚀 Tahecho Sitemap Awareness Demo")
    print("=" * 50)
    
    # Check if required environment variables are set
    required_vars = ['OPENAI_API_KEY', 'SUPABASE_URL', 'SUPABASE_ANON_KEY']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("Please set these in your .env file:")
        for var in missing_vars:
            print(f"   {var}=your_value_here")
        return
    
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
        # Initialize components
        print("📋 Initializing Configuration Manager...")
        config_manager = ConfigurationManager()
        
        if not config_manager.is_enabled():
            print("❌ Sitemap agents are disabled")
            return
        
        print("✅ Configuration Manager initialized")
        print(f"   - Sitemap URLs: {config_manager.get_sitemap_urls()}")
        print(f"   - Requests per second: {config_manager.get_requests_per_second()}")
        print(f"   - Max pages: {config_manager.get_max_pages()}")
        
        # Initialize Supabase integration (with mock)
        print("\n🗄️  Initializing Supabase Integration...")
        with open('/dev/null', 'w') as f:
            # Redirect stdout to suppress Supabase client warnings
            import contextlib
            with contextlib.redirect_stdout(f):
                supabase = SupabaseIntegration(
                    url=config_manager.get_supabase_url(),
                    anon_key=config_manager.get_supabase_anon_key()
                )
        
        print("✅ Supabase Integration initialized")
        print(f"   - URL: {supabase.url}")
        print(f"   - Embedding dimension: {supabase.embedding_dimension}")
        
        # Initialize Scrapy Manager
        print("\n🕷️  Initializing Scrapy Manager...")
        scrapy_manager = ScrapyManager(config_manager)
        print("✅ Scrapy Manager initialized")
        
        # Demo sitemap scraping
        print("\n🔍 Demo: Sitemap Scraping")
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
        print("\n🔄 Demo: Incremental Update")
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
        print("\nNext steps:")
        print("1. Set up real Supabase instance with pgvector")
        print("2. Configure environment variables with real credentials")
        print("3. Run: python scripts/manage_sitemaps.py scrape --url https://docs.aleph-alpha.com/sitemap.xml")
        print("4. Query scraped content through the Tahecho agent")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    asyncio.run(demo_sitemap_functionality()) 
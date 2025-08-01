#!/usr/bin/env python3
"""Setup script for Supabase database schema."""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from tahecho.sitemap.supabase_integration import SupabaseIntegration


def setup_supabase_schema():
    """Set up the Supabase database schema for document-oriented content storage."""
    print("🗄️  Setting up Supabase Database Schema")
    print("=" * 50)
    
    # Check if Supabase credentials are available
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_anon_key = os.getenv('SUPABASE_ANON_KEY')
    
    if not supabase_url or not supabase_anon_key:
        print("❌ Missing Supabase credentials in .env file")
        print("Please set SUPABASE_URL and SUPABASE_ANON_KEY")
        return False
    
    try:
        # Initialize Supabase integration
        print("📋 Initializing Supabase connection...")
        supabase = SupabaseIntegration(supabase_url, supabase_anon_key)
        
        if supabase.client is None:
            print("❌ Failed to connect to Supabase")
            return False
        
        print("✅ Connected to Supabase successfully")
        
        # Document-oriented schema for unified content storage
        schema_sql = """
        -- Enable pgvector extension
        CREATE EXTENSION IF NOT EXISTS vector;

        -- Unified documents table for all content sources
        CREATE TABLE IF NOT EXISTS documents (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            
            -- Core document metadata
            title TEXT,
            url TEXT,
            content TEXT NOT NULL,
            content_preview TEXT,
            content_hash TEXT,
            
            -- Source and origin tracking
            source_type TEXT NOT NULL, -- 'sitemap', 'wiki', 'confluence', 'api', 'webcrawler', etc.
            source_id TEXT, -- ID from the original source system
            source_url TEXT, -- URL where this document was found
            
            -- Domain and organization context
            domain TEXT,
            organization TEXT,
            
            -- Content metadata (structured JSON)
            metadata JSONB DEFAULT '{}',
            
            -- Vector embedding for similarity search
            embedding vector(1536),
            
            -- Timestamps
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            last_modified TIMESTAMP WITH TIME ZONE,
            
            -- Status and versioning
            status TEXT DEFAULT 'active',
            version INTEGER DEFAULT 1,
            
            -- Tags for categorization
            tags TEXT[] DEFAULT '{}'
        );

        -- Create indexes for performance and search
        CREATE INDEX IF NOT EXISTS idx_documents_embedding ON documents USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
        CREATE INDEX IF NOT EXISTS idx_documents_source_type ON documents (source_type);
        CREATE INDEX IF NOT EXISTS idx_documents_source_id ON documents (source_id);
        CREATE INDEX IF NOT EXISTS idx_documents_url ON documents (url);
        CREATE INDEX IF NOT EXISTS idx_documents_domain ON documents (domain);
        CREATE INDEX IF NOT EXISTS idx_documents_content_hash ON documents (content_hash);
        CREATE INDEX IF NOT EXISTS idx_documents_created_at ON documents (created_at);
        CREATE INDEX IF NOT EXISTS idx_documents_status ON documents (status);
        CREATE INDEX IF NOT EXISTS idx_documents_tags ON documents USING GIN (tags);
        CREATE INDEX IF NOT EXISTS idx_documents_metadata ON documents USING GIN (metadata);

        -- Source tracking table for managing different content sources
        CREATE TABLE IF NOT EXISTS content_sources (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            name TEXT NOT NULL,
            source_type TEXT NOT NULL,
            config JSONB DEFAULT '{}',
            status TEXT DEFAULT 'active',
            last_sync_at TIMESTAMP WITH TIME ZONE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );

        -- Create indexes for content sources
        CREATE INDEX IF NOT EXISTS idx_content_sources_type ON content_sources (source_type);
        CREATE INDEX IF NOT EXISTS idx_content_sources_status ON content_sources (status);

        -- Function to update the updated_at timestamp
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ language 'plpgsql';

        -- Trigger to automatically update updated_at
        DROP TRIGGER IF EXISTS update_documents_updated_at ON documents;
        CREATE TRIGGER update_documents_updated_at
            BEFORE UPDATE ON documents
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();

        DROP TRIGGER IF EXISTS update_content_sources_updated_at ON content_sources;
        CREATE TRIGGER update_content_sources_updated_at
            BEFORE UPDATE ON content_sources
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
        """
        
        print("🔧 Creating document-oriented database schema...")
        
        # Execute the schema SQL
        try:
            # Split the SQL into individual statements
            statements = [stmt.strip() for stmt in schema_sql.split(';') if stmt.strip()]
            
            for statement in statements:
                if statement:
                    print(f"   Executing: {statement[:50]}...")
                    supabase.client.rpc('exec_sql', {'sql': statement}).execute()
            
            print("✅ Database schema created successfully!")
            
        except Exception as e:
            print(f"⚠️  Note: Some operations may have failed: {e}")
            print("This is normal if tables already exist or if you don't have admin privileges")
        
        # Test the connection by trying to create a test record
        print("\n🧪 Testing database connection...")
        try:
            test_document = {
                'title': 'Test Document',
                'url': 'https://test.example.com/page',
                'content': 'This is a test document for the unified content storage system.',
                'content_preview': 'Test document for unified storage...',
                'content_hash': 'test_hash_123',
                'source_type': 'sitemap',
                'source_id': 'test_sitemap_123',
                'source_url': 'https://test.example.com/sitemap.xml',
                'domain': 'test.example.com',
                'organization': 'Test Org',
                'metadata': {
                    'language': 'en',
                    'content_type': 'documentation',
                    'word_count': 15
                },
                'tags': ['test', 'documentation']
            }
            
            result = supabase.client.table('documents').insert(test_document).execute()
            print("✅ Test document created successfully")
            
            # Clean up test record
            if result.data:
                test_id = result.data[0]['id']
                supabase.client.table('documents').delete().eq('id', test_id).execute()
                print("✅ Test document cleaned up")
                
        except Exception as e:
            print(f"⚠️  Test failed: {e}")
            print("This might be due to permissions or existing schema issues")
        
        print("\n🎉 Document-oriented Supabase setup completed!")
        print("\nSchema Overview:")
        print("📄 documents table - Unified storage for all content sources")
        print("   - source_type: sitemap, wiki, confluence, api, webcrawler, etc.")
        print("   - metadata: Flexible JSON for source-specific data")
        print("   - embedding: Vector for similarity search across all sources")
        print("   - tags: Array for categorization")
        print("\n📋 content_sources table - Track and manage different content sources")
        print("\nNext steps:")
        print("1. Run: poetry run python scripts/demo_sitemap.py")
        print("2. Run: poetry run python scripts/manage_sitemaps.py list")
        print("3. Start scraping: poetry run python scripts/manage_sitemaps.py scrape --url https://docs.aleph-alpha.com/sitemap.xml")
        
        return True
        
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        return False


if __name__ == '__main__':
    setup_supabase_schema() 
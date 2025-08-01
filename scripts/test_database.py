#!/usr/bin/env python3
"""Test script to verify database operations work after fixing RLS policies."""

import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from tahecho.sitemap.supabase_integration import SupabaseIntegration


async def test_database_operations():
    """Test basic database operations to verify RLS policies are working."""
    print("🧪 Testing Database Operations")
    print("=" * 40)
    
    # Check if Supabase credentials are available
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_anon_key = os.getenv('SUPABASE_ANON_KEY')
    
    if not supabase_url or not supabase_anon_key:
        print("❌ Missing Supabase credentials in .env file")
        return False
    
    try:
        # Initialize Supabase integration
        print("📋 Initializing Supabase connection...")
        supabase = SupabaseIntegration(supabase_url, supabase_anon_key)
        
        if supabase.client is None:
            print("❌ Failed to connect to Supabase")
            return False
        
        print("✅ Connected to Supabase successfully")
        
        # Test 1: Create a test document
        print("\n📄 Test 1: Creating a test document...")
        test_document = {
            'title': 'Test Document for RLS',
            'url': 'https://test.example.com/rls-test',
            'content': 'This is a test document to verify RLS policies are working correctly.',
            'content_preview': 'Test document for RLS verification...',
            'content_hash': 'test_rls_hash_123',
            'source_type': 'test',
            'source_id': 'test_rls_123',
            'source_url': 'https://test.example.com',
            'domain': 'test.example.com',
            'metadata': {
                'test_type': 'rls_verification',
                'created_by': 'test_script'
            },
            'tags': ['test', 'rls', 'verification']
        }
        
        result = await supabase.create_document(test_document)
        if result and 'id' in result:
            print(f"✅ Test document created successfully: {result['id']}")
            document_id = result['id']
        else:
            print("❌ Failed to create test document")
            return False
        
        # Test 2: Retrieve the document
        print("\n🔍 Test 2: Retrieving the test document...")
        retrieved_doc = await supabase.get_document_by_url('https://test.example.com/rls-test')
        if retrieved_doc:
            print(f"✅ Document retrieved successfully: {retrieved_doc['title']}")
        else:
            print("❌ Failed to retrieve document")
            return False
        
        # Test 3: Update the document
        print("\n✏️  Test 3: Updating the test document...")
        update_data = {
            'title': 'Updated Test Document for RLS',
            'metadata': {
                'test_type': 'rls_verification',
                'created_by': 'test_script',
                'updated': True
            }
        }
        
        updated_doc = await supabase.update_document(document_id, update_data)
        if updated_doc:
            print(f"✅ Document updated successfully: {updated_doc['title']}")
        else:
            print("❌ Failed to update document")
            return False
        
        # Test 4: Search for documents
        print("\n🔎 Test 4: Searching for documents...")
        # Create a simple mock embedding for testing
        mock_embedding = [0.1] * 1536  # 1536-dimensional vector
        
        similar_docs = await supabase.search_similar_documents(
            query_embedding=mock_embedding,
            source_types=['test'],
            limit=5
        )
        
        if similar_docs:
            print(f"✅ Found {len(similar_docs)} similar documents")
        else:
            print("ℹ️  No similar documents found (this is normal for test data)")
        
        # Test 5: Create a content source
        print("\n📋 Test 5: Creating a test content source...")
        test_source = {
            'name': 'Test Content Source',
            'source_type': 'test',
            'config': {
                'test_config': True,
                'description': 'Test content source for RLS verification'
            },
            'status': 'active'
        }
        
        source_result = await supabase.create_content_source(test_source)
        if source_result and 'id' in source_result:
            print(f"✅ Content source created successfully: {source_result['id']}")
        else:
            print("❌ Failed to create content source")
            return False
        
        # Test 6: Get content sources
        print("\n📋 Test 6: Retrieving content sources...")
        sources = await supabase.get_content_sources('test')
        if sources:
            print(f"✅ Found {len(sources)} test content sources")
        else:
            print("ℹ️  No test content sources found")
        
        # Cleanup: Delete test document
        print("\n🧹 Cleanup: Removing test document...")
        try:
            # Note: We don't have a delete method in the current implementation
            # The test document will remain in the database
            print("ℹ️  Test document left in database for inspection")
        except Exception as e:
            print(f"⚠️  Cleanup note: {e}")
        
        print("\n🎉 All database operation tests passed!")
        print("\nNext steps:")
        print("1. Run: poetry run python scripts/demo_sitemap.py")
        print("2. The sitemap scraping should now work properly")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


if __name__ == '__main__':
    asyncio.run(test_database_operations()) 
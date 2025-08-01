# Sitemap Awareness Feature - Usage Guide

## Overview

The Sitemap Awareness feature provides a unified document storage system that enables similarity search across multiple content sources including sitemaps, wikis, Confluence, APIs, and more. This document-oriented approach allows you to find similar content regardless of its origin.

## Key Features

- **Unified Document Storage**: All content sources stored in a single `documents` table
- **Cross-Source Similarity Search**: Find similar documents across sitemaps, wikis, Confluence, etc.
- **Flexible Metadata**: JSON-based metadata for source-specific information
- **Vector Embeddings**: OpenAI-powered semantic search
- **Incremental Updates**: Content hash-based change detection
- **Source Tracking**: Manage and monitor different content sources

## Prerequisites

1. **Supabase Account**: Create a project at [supabase.com](https://supabase.com)
2. **OpenAI API Key**: For generating embeddings
3. **Python Environment**: Poetry-managed dependencies

## Environment Configuration

Create a `.env` file in your project root:

```bash
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_anon_key_here

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Sitemap Configuration
SITEMAP_AGENTS_ENABLED=true
SITEMAP_URLS=https://docs.aleph-alpha.com/sitemap.xml
SITEMAP_CONFIG={"https://docs.aleph-alpha.com/sitemap.xml": {"filters": ["/docs/api", "/docs/tutorial"], "max_pages": 100}}
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_DIMENSION=1536
```

## Database Setup

### Option 1: Using Supabase Dashboard (Recommended)

1. Go to your Supabase project dashboard
2. Navigate to **SQL Editor**
3. Copy and paste the contents of `scripts/supabase_schema.sql`
4. Execute the SQL script

### Option 2: Using the Setup Script

```bash
poetry run python scripts/setup_supabase.py
```

## Database Schema

### Documents Table

The unified `documents` table stores all content with the following structure:

```sql
CREATE TABLE documents (
    id UUID PRIMARY KEY,
    title TEXT,
    url TEXT,
    content TEXT NOT NULL,
    content_preview TEXT,
    content_hash TEXT,
    
    -- Source tracking
    source_type TEXT NOT NULL, -- 'sitemap', 'wiki', 'confluence', 'api', etc.
    source_id TEXT,
    source_url TEXT,
    
    -- Context
    domain TEXT,
    organization TEXT,
    
    -- Flexible metadata
    metadata JSONB DEFAULT '{}',
    
    -- Vector search
    embedding vector(1536),
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE,
    last_modified TIMESTAMP WITH TIME ZONE,
    
    -- Status and versioning
    status TEXT DEFAULT 'active',
    version INTEGER DEFAULT 1,
    
    -- Categorization
    tags TEXT[] DEFAULT '{}'
);
```

### Content Sources Table

Track and manage different content sources:

```sql
CREATE TABLE content_sources (
    id UUID PRIMARY KEY,
    name TEXT NOT NULL,
    source_type TEXT NOT NULL,
    config JSONB DEFAULT '{}',
    status TEXT DEFAULT 'active',
    last_sync_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE
);
```

## CLI Usage

### List Content Sources

```bash
poetry run python scripts/manage_sitemaps.py list
```

### Scrape a Sitemap

```bash
poetry run python scripts/manage_sitemaps.py scrape --url https://docs.aleph-alpha.com/sitemap.xml
```

### Update Existing Content

```bash
poetry run python scripts/manage_sitemaps.py update --url https://docs.aleph-alpha.com/sitemap.xml
```

### Check Operation Status

```bash
poetry run python scripts/manage_sitemaps.py status --operation-id <operation_id>
```

### Cleanup Old Data

```bash
poetry run python scripts/manage_sitemaps.py cleanup --older-than-days 30
```

## API Usage

### Basic Document Operations

```python
from tahecho.sitemap.supabase_integration import SupabaseIntegration

# Initialize
supabase = SupabaseIntegration(supabase_url, supabase_anon_key)

# Create a document
document = await supabase.create_document({
    'title': 'API Documentation',
    'url': 'https://docs.example.com/api',
    'content': 'Complete API documentation...',
    'source_type': 'sitemap',
    'source_id': 'sitemap_123',
    'domain': 'docs.example.com',
    'metadata': {'api_version': 'v2', 'category': 'reference'},
    'tags': ['api', 'documentation']
})

# Search similar documents
similar_docs = await supabase.search_similar_documents(
    query_embedding=embedding_vector,
    source_types=['sitemap', 'wiki'],  # Search across multiple sources
    limit=10,
    similarity_threshold=0.7
)
```

### Cross-Source Similarity Search

```python
# Search across all content sources
all_similar = await supabase.search_similar_documents(
    query_embedding=embedding_vector,
    limit=20
)

# Search only in specific sources
wiki_similar = await supabase.search_similar_documents(
    query_embedding=embedding_vector,
    source_types=['wiki', 'confluence'],
    limit=10
)
```

### Content Source Management

```python
# Create a new content source
source = await supabase.create_content_source({
    'name': 'Company Wiki',
    'source_type': 'wiki',
    'config': {
        'base_url': 'https://wiki.company.com',
        'api_token': 'your_token'
    }
})

# Get all content sources
sources = await supabase.get_content_sources()

# Get sources by type
sitemap_sources = await supabase.get_content_sources('sitemap')
```

## Demo Scripts

### Basic Demo

```bash
poetry run python scripts/demo_sitemap.py
```

### Mock Demo (No Real Connections)

```bash
poetry run python scripts/demo_sitemap_mock.py
```

## Best Practices

### 1. Content Organization

- Use meaningful `source_type` values: `sitemap`, `wiki`, `confluence`, `api`, `webcrawler`
- Add relevant tags for categorization: `['api', 'documentation', 'tutorial']`
- Store source-specific data in the `metadata` JSON field

### 2. Performance Optimization

- Use appropriate similarity thresholds (0.7-0.8 for most use cases)
- Limit search results to reasonable numbers (10-50)
- Filter by `source_type` when you know the content source

### 3. Data Management

- Regularly clean up old documents with `cleanup` command
- Monitor content source sync status
- Use content hashes for efficient incremental updates

### 4. Security

- Review and adjust Row Level Security (RLS) policies
- Use environment variables for sensitive configuration
- Validate input data before storage

## Troubleshooting

### Common Issues

1. **"relation does not exist"**: Run the database setup script
2. **"Invalid API key"**: Check your Supabase and OpenAI credentials
3. **"Embedding dimension mismatch"**: Ensure `EMBEDDING_DIMENSION=1536` in your `.env`
4. **"Permission denied"**: Check RLS policies in Supabase

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Environment Verification

```bash
poetry run python scripts/test_env.py
```

## Integration with Tahecho Agent

The sitemap content is automatically available to the Tahecho agent for answering questions about scraped documentation. The agent can:

- Search across all content sources for relevant information
- Provide context-aware answers based on documentation
- Reference specific URLs and sources
- Combine information from multiple sources

## Future Extensions

The document-oriented approach makes it easy to add new content sources:

1. **Confluence Integration**: Add `source_type: 'confluence'`
2. **Wiki Integration**: Add `source_type: 'wiki'`
3. **API Documentation**: Add `source_type: 'api'`
4. **Custom Sources**: Add any `source_type` with appropriate metadata

All new sources automatically benefit from cross-source similarity search and unified querying. 
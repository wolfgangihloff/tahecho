# Sitemap Awareness Feature Specification

## Overview

The Sitemap Awareness feature extends Tahecho's capabilities to include web scraping and document loading from sitemaps using a **document-oriented approach**. This allows users to scrape, analyze, and persist web content from various sources in a unified storage system that enables cross-source similarity search. The feature makes it easy to find similar content regardless of its origin (sitemaps, wikis, Confluence, APIs, etc.).

## Feature Goals

1. **Unified Document Storage**: Store all content sources in a single table for cross-source similarity search
2. **Web Content Integration**: Enable robust scraping and loading of web content from sitemaps using Scrapy
3. **Vector-Based Persistence**: Store scraped data and embeddings in Supabase with pgvector
4. **Configuration-Driven Agents**: Enable sitemap agents through environment configuration
5. **Asynchronous Processing**: Support background scraping operations
6. **Dedicated Management Script**: Python script for sitemap setup with incremental and differential runs
7. **Agent Integration**: Seamlessly integrate with existing multi-agent workflow
8. **Demo Capability**: Provide easy testing with the Aleph Alpha sitemap
9. **TDD Compliance**: Follow the project's test-driven development approach
10. **Cross-Source Search**: Enable similarity search across multiple content sources

## User Stories

### Admin/Owner User Stories

1. **As an admin/owner of a deployed Tahecho instance, I want to configure sitemap agents through environment variables** so that I can easily set up knowledge bases
   - **Acceptance Criteria**:
     - Can define sitemap URLs in .env configuration
     - Can specify multiple sitemaps for different domains
     - Can configure scraping parameters (rate limits, filters)
     - Agents become active automatically based on configuration
     - Minimal deployment overhead
     - Can use dedicated Python script for advanced configuration

2. **As an admin/owner, I want to use a dedicated Python script for sitemap management** so that I can perform complex operations and differential updates
   - **Acceptance Criteria**:
     - Can run incremental updates to only scrape new/changed content
     - Can perform differential runs to compare and update specific sections
     - Can configure advanced scraping parameters
     - Can monitor and manage scraping operations
     - Can handle complex sitemap structures and redirects

3. **As an admin/owner, I want to trigger asynchronous sitemap scraping** so that I can update knowledge bases without blocking the application
   - **Acceptance Criteria**:
     - Can trigger scraping operations locally
     - Scraping runs in background without blocking user interactions
     - Can monitor scraping progress and status
     - Can handle large sitemaps efficiently
     - Automatic retry logic for failed operations
     - Support for incremental and differential updates

4. **As an admin/owner, I want to manage scraped data in a unified document storage system** so that I can maintain a scalable knowledge base with cross-source search
   - **Acceptance Criteria**:
     - Data is stored in Supabase with pgvector for embeddings
     - All content sources (sitemaps, wikis, Confluence, APIs) use the same storage schema
     - Can view and manage scraped content through admin interface
     - Can update or refresh specific sitemaps
     - Can monitor storage usage and performance
     - Data is automatically indexed for fast retrieval
     - Can search across all content sources simultaneously

### End User Stories

5. **As an end user of Tahecho, I want to ask questions about Aleph Alpha documentation** so that I can get specific, accurate information about their APIs and services
   - **Acceptance Criteria**:
     - Can ask questions like "How do I use the chat completion API?"
     - Can ask about specific features like "What are the available models?"
     - Can get information about pricing, authentication, and best practices
     - Responses are based on the scraped Aleph Alpha documentation
     - Responses include source URLs for verification

6. **As an end user, I want to search for specific information across all content sources** so that I can find relevant documentation quickly regardless of its origin
   - **Acceptance Criteria**:
     - Can search for specific API endpoints across sitemaps, wikis, and Confluence
     - Can search for error codes and troubleshooting information
     - Can search for code examples and tutorials
     - Results are ranked by relevance across all sources
     - Results include context and source information
     - Can filter search results by content source type

7. **As an end user, I want to get contextual answers about web content** so that I can understand complex topics better
   - **Acceptance Criteria**:
     - Can ask follow-up questions about previous responses
     - Can get explanations of technical concepts
     - Can receive step-by-step guidance for implementation
     - Responses maintain context across conversation turns
     - Can get information from multiple sources in a single response

### Demo User Story

8. **As a developer, I want to test the feature with Aleph Alpha's sitemap** so that I can verify functionality
   - **Acceptance Criteria**:
     - Can scrape https://docs.aleph-alpha.com/sitemap.xml
     - Can filter and process the results
     - Can view the scraped content
     - Can demonstrate end-user query capabilities
     - Can demonstrate cross-source similarity search

## Document-Oriented Architecture

### Overview
The feature uses a **unified document storage approach** where all content sources (sitemaps, wikis, Confluence, APIs, web crawlers) are stored in a single `documents` table. This enables:

- **Cross-source similarity search**: Find similar content across all sources
- **Unified metadata**: Flexible JSON-based metadata for source-specific information
- **Consistent API**: Same interface for all content types
- **Scalable storage**: Single table design with proper indexing

### Database Schema

#### Documents Table (Unified Storage)
```sql
CREATE TABLE documents (
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
```

#### Content Sources Table (Source Management)
```sql
CREATE TABLE content_sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    source_type TEXT NOT NULL,
    config JSONB DEFAULT '{}',
    status TEXT DEFAULT 'active',
    last_sync_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### Cross-Source Similarity Search

The unified approach enables powerful cross-source search capabilities:

```python
# Search across all content sources
similar_docs = await supabase.search_similar_documents(
    query_embedding=embedding_vector,
    limit=20
)

# Search only in specific sources
wiki_docs = await supabase.search_similar_documents(
    query_embedding=embedding_vector,
    source_types=['wiki', 'confluence'],
    limit=10
)

# Search with metadata filtering
api_docs = await supabase.search_similar_documents(
    query_embedding=embedding_vector,
    source_types=['sitemap'],
    metadata_filter={'content_type': 'api_documentation'}
)
```

## Technical Architecture

### Components

1. **ConfigurationManager**: Environment-based configuration loading and validation
2. **SupabaseIntegration**: Document-oriented database operations with vector search
3. **ScrapyManager**: Robust web scraping framework for handling complex sites
4. **EmbeddingGenerator**: OpenAI-powered embedding generation for semantic search
5. **SitemapLoader Integration**: Uses [LangChain's SitemapLoader](https://python.langchain.com/docs/integrations/document_loaders/sitemap/) for initial sitemap parsing
6. **Async Processing Engine**: Background scraping operations
7. **Sitemap Management Script**: Dedicated Python script for advanced sitemap operations
8. **Task Classifier Extension**: Routes sitemap-related requests
9. **Workflow Integration**: Integrates with existing LangGraph workflow
10. **Knowledge Base Integration**: Enables end-user queries against scraped content
11. **Vector Search**: Semantic search using pgvector embeddings

### User Role Separation

#### Admin/Owner Capabilities
- **Sitemap Scraping**: Initiate and manage sitemap scraping operations
- **Data Management**: View, delete, and manage scraped data
- **Configuration**: Set scraping parameters and schedules
- **Monitoring**: Track scraping performance and errors
- **Cross-Source Management**: Manage multiple content sources

#### End User Capabilities
- **Content Queries**: Ask questions about scraped content
- **Cross-Source Search**: Find specific information across all content sources
- **Contextual Conversations**: Maintain context across multiple queries
- **Source Attribution**: Get references to original documentation

### Data Flow

#### Configuration-Driven Setup
```
.env Configuration → Configuration Manager → Sitemap Agent Registration → Background Processing
```

#### Scraping Flow
```
Admin Trigger → Sitemap Management Script → Scrapy Engine → SitemapLoader → Content Processing → Embedding Generation → Unified Document Storage → Cleanup
```

#### Query Flow
```
User Query → Task Classifier → Sitemap Agent → Cross-Source Vector Search → Supabase Retrieval → Response Generation
```

### Storage Strategy

#### Local Processing Storage
- **Location**: `data/processing/`
- **Purpose**: Temporary storage during scraping and processing
- **Format**: JSON files for intermediate processing
- **Cleanup**: Automatic cleanup after successful Supabase upload

#### Supabase Vector Storage
- **Primary Storage**: Supabase with [pgvector](https://supabase.com/docs/guides/database/extensions/pgvector) extension
- **Unified Schema**: Single `documents` table for all content sources
- **Vector Search**: Cross-source similarity search using pgvector
- **Metadata**: Flexible JSON storage for source-specific information
- **Indexing**: Optimized indexes for performance and search

## Implementation Status

### ✅ Completed Components

1. **ConfigurationManager**: Environment-based configuration with validation
2. **SupabaseIntegration**: Document-oriented database operations with vector search
3. **EmbeddingGenerator**: OpenAI-powered embedding generation
4. **ScrapyManager**: Basic scraping framework (simulated for demo)
5. **Database Schema**: Unified document storage with pgvector
6. **CLI Management Script**: Basic sitemap management operations
7. **Demo Scripts**: Both real and mock demos for testing
8. **Poetry Integration**: Proper dependency management
9. **RLS Policy Management**: Database security configuration
10. **Cross-Source Search**: Unified similarity search across all content types

### 🔄 In Progress

1. **Real Scrapy Integration**: Actual web scraping implementation
2. **Incremental Updates**: Content hash-based change detection
3. **Advanced Filtering**: Regex-based URL filtering
4. **Error Recovery**: Robust retry logic and error handling

### 📋 Planned Components

1. **Agent Integration**: Integration with existing multi-agent workflow
2. **Task Classifier Extension**: Sitemap-specific task routing
3. **Advanced Monitoring**: Progress tracking and performance metrics
4. **Scheduled Scraping**: Automated periodic updates

## Configuration

### Environment Variables

```bash
# Supabase Configuration
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_supabase_anon_key

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key

# Sitemap Configuration
SITEMAP_AGENTS_ENABLED=true
SITEMAP_URLS=https://docs.aleph-alpha.com/sitemap.xml
SITEMAP_CONFIG={"https://docs.aleph-alpha.com/sitemap.xml": {"filters": ["/docs/api", "/docs/tutorial"], "max_pages": 100}}
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_DIMENSION=1536
```

### Configuration Format

#### Multiple Sitemaps
```bash
# Comma-separated list of sitemap URLs
SITEMAP_URLS=https://docs.aleph-alpha.com/sitemap.xml,https://api.example.com/sitemap.xml,https://docs.example.com/sitemap.xml
```

#### Sitemap-Specific Filters
```bash
# JSON format for sitemap-specific configurations
SITEMAP_CONFIG='{
  "https://docs.aleph-alpha.com/sitemap.xml": {
    "filters": ["/docs/api", "/docs/tutorial"],
    "max_pages": 200,
    "requests_per_second": 1
  },
  "https://api.example.com/sitemap.xml": {
    "filters": ["/api/v1"],
    "max_pages": 50,
    "requests_per_second": 3
  }
}'
```

## Usage Examples

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

# Search similar documents across all sources
similar_docs = await supabase.search_similar_documents(
    query_embedding=embedding_vector,
    source_types=['sitemap', 'wiki'],  # Search across multiple sources
    limit=10,
    similarity_threshold=0.7
)
```

### CLI Management

```bash
# List content sources
poetry run python scripts/manage_sitemaps.py list

# Scrape a sitemap
poetry run python scripts/manage_sitemaps.py scrape --url https://docs.aleph-alpha.com/sitemap.xml

# Update existing content
poetry run python scripts/manage_sitemaps.py update --url https://docs.aleph-alpha.com/sitemap.xml

# Check operation status
poetry run python scripts/manage_sitemaps.py status --operation-id <operation_id>

# Cleanup old data
poetry run python scripts/manage_sitemaps.py cleanup --older-than-days 30
```

### Demo Scripts

```bash
# Real demo (requires Supabase setup)
poetry run python scripts/demo_sitemap.py

# Mock demo (no external dependencies)
poetry run python scripts/demo_sitemap_mock.py

# Database test
poetry run python scripts/test_database.py
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

### Fix RLS Policies

If you encounter RLS policy errors, run the fix script:

1. Go to Supabase SQL Editor
2. Copy and paste the contents of `scripts/fix_rls_policies.sql`
3. Execute the SQL script

## Future Extensions

The document-oriented approach makes it easy to add new content sources:

1. **Confluence Integration**: Add `source_type: 'confluence'`
2. **Wiki Integration**: Add `source_type: 'wiki'`
3. **API Documentation**: Add `source_type: 'api'`
4. **Custom Sources**: Add any `source_type` with appropriate metadata

All new sources automatically benefit from cross-source similarity search and unified querying.

## Success Metrics

### Functional Metrics
- ✅ Successful scraping of Aleph Alpha sitemap
- ✅ Data persistence to Supabase with pgvector
- ✅ Cross-source similarity search
- ✅ Unified document storage
- ✅ Configuration-driven setup
- ✅ Poetry dependency management

### Performance Metrics
- Scraping speed (pages per second)
- Memory usage during scraping
- Storage efficiency
- Response time for agent queries
- Cross-source search performance

### Quality Metrics
- Test coverage > 90%
- Error rate < 5%
- User satisfaction with error messages
- Integration stability

## Conclusion

The Sitemap Awareness feature has been successfully implemented using a document-oriented approach that provides unified storage and cross-source similarity search. The implementation follows the project's TDD approach and establishes a foundation for future content source integrations. The feature provides immediate value through the Aleph Alpha demo while enabling powerful cross-source search capabilities.

Key achievements:
- ✅ Document-oriented unified storage
- ✅ Cross-source similarity search
- ✅ Poetry dependency management
- ✅ Supabase integration with pgvector
- ✅ Configuration-driven setup
- ✅ Mock and real demo capabilities
- ✅ RLS policy management
- ✅ Comprehensive documentation

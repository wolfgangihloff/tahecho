-- Tahecho Document-Oriented Database Schema
-- Run this in your Supabase SQL Editor

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

-- Function for vector similarity search
CREATE OR REPLACE FUNCTION match_documents(
    query_embedding vector(1536),
    match_threshold float DEFAULT 0.7,
    match_count int DEFAULT 10
)
RETURNS TABLE (
    id UUID,
    title TEXT,
    url TEXT,
    content_preview TEXT,
    source_type TEXT,
    domain TEXT,
    similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        documents.id,
        documents.title,
        documents.url,
        documents.content_preview,
        documents.source_type,
        documents.domain,
        1 - (documents.embedding <=> query_embedding) AS similarity
    FROM documents
    WHERE documents.embedding IS NOT NULL
    AND 1 - (documents.embedding <=> query_embedding) > match_threshold
    ORDER BY documents.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- Enable Row Level Security (RLS)
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE content_sources ENABLE ROW LEVEL SECURITY;

-- Create policies for public read access (adjust as needed for your security requirements)
CREATE POLICY "Allow public read access to documents" ON documents
    FOR SELECT USING (true);

CREATE POLICY "Allow public read access to content sources" ON content_sources
    FOR SELECT USING (true);

-- Create policies for authenticated users to insert/update (adjust as needed)
CREATE POLICY "Allow authenticated users to insert documents" ON documents
    FOR INSERT WITH CHECK (auth.role() = 'authenticated');

CREATE POLICY "Allow authenticated users to update documents" ON documents
    FOR UPDATE USING (auth.role() = 'authenticated');

CREATE POLICY "Allow authenticated users to insert content sources" ON content_sources
    FOR INSERT WITH CHECK (auth.role() = 'authenticated');

CREATE POLICY "Allow authenticated users to update content sources" ON content_sources
    FOR UPDATE USING (auth.role() = 'authenticated');

-- Insert some sample content sources
INSERT INTO content_sources (name, source_type, config, status) VALUES
    ('Aleph Alpha Documentation', 'sitemap', '{"url": "https://docs.aleph-alpha.com/sitemap.xml", "filters": ["/docs/api", "/docs/tutorial"], "max_pages": 100}', 'active'),
    ('Example Wiki', 'wiki', '{"base_url": "https://wiki.example.com", "api_token": "demo"}', 'inactive'),
    ('Confluence Space', 'confluence', '{"space_key": "DEMO", "base_url": "https://company.atlassian.net"}', 'inactive')
ON CONFLICT DO NOTHING; 
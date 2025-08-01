-- Fix Row Level Security Policies for Tahecho Sitemap Operations
-- Run this in your Supabase SQL Editor

-- Drop existing policies that might be too restrictive
DROP POLICY IF EXISTS "Allow authenticated users to insert documents" ON documents;
DROP POLICY IF EXISTS "Allow authenticated users to update documents" ON documents;
DROP POLICY IF EXISTS "Allow authenticated users to insert content sources" ON content_sources;
DROP POLICY IF EXISTS "Allow authenticated users to update content sources" ON content_sources;

-- Create more permissive policies for development/testing
-- Note: In production, you should make these more restrictive

-- Allow all operations on documents (for development)
CREATE POLICY "Allow all operations on documents" ON documents
    FOR ALL USING (true) WITH CHECK (true);

-- Allow all operations on content sources (for development)
CREATE POLICY "Allow all operations on content sources" ON content_sources
    FOR ALL USING (true) WITH CHECK (true);

-- Alternative: If you want to keep some security, use these policies instead:
-- (Uncomment the lines below and comment out the "Allow all operations" policies above)

/*
-- Allow insert for any user (including anonymous)
CREATE POLICY "Allow insert documents" ON documents
    FOR INSERT WITH CHECK (true);

-- Allow update for any user
CREATE POLICY "Allow update documents" ON documents
    FOR UPDATE USING (true) WITH CHECK (true);

-- Allow select for any user
CREATE POLICY "Allow select documents" ON documents
    FOR SELECT USING (true);

-- Allow delete for any user (be careful with this in production)
CREATE POLICY "Allow delete documents" ON documents
    FOR DELETE USING (true);

-- Similar policies for content_sources
CREATE POLICY "Allow insert content sources" ON content_sources
    FOR INSERT WITH CHECK (true);

CREATE POLICY "Allow update content sources" ON content_sources
    FOR UPDATE USING (true) WITH CHECK (true);

CREATE POLICY "Allow select content sources" ON content_sources
    FOR SELECT USING (true);

CREATE POLICY "Allow delete content sources" ON content_sources
    FOR DELETE USING (true);
*/

-- Verify the policies are in place
SELECT schemaname, tablename, policyname, permissive, roles, cmd, qual, with_check 
FROM pg_policies 
WHERE tablename IN ('documents', 'content_sources')
ORDER BY tablename, policyname; 
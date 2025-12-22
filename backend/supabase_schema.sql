-- ScriptAI Pro - Supabase Schema
-- Run this in your Supabase SQL Editor to set up the database

-- Enable the pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create the script_vectors table
CREATE TABLE IF NOT EXISTS script_vectors (
    id TEXT PRIMARY KEY,
    content TEXT NOT NULL,
    embedding vector(384),  -- sentence-transformers/all-MiniLM-L6-v2 outputs 384 dimensions
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create an index for faster vector similarity search
CREATE INDEX IF NOT EXISTS script_vectors_embedding_idx
ON script_vectors
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Create the match_scripts RPC function for vector similarity search
CREATE OR REPLACE FUNCTION match_scripts(
    query_embedding vector(384),
    match_count INT DEFAULT 5,
    filter_mode TEXT DEFAULT NULL,
    filter_vector_type TEXT DEFAULT NULL
)
RETURNS TABLE (
    id TEXT,
    content TEXT,
    metadata JSONB,
    similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        sv.id,
        sv.content,
        sv.metadata,
        1 - (sv.embedding <=> query_embedding) AS similarity
    FROM script_vectors sv
    WHERE
        (filter_mode IS NULL OR sv.metadata->>'mode' = filter_mode)
        AND (filter_vector_type IS NULL OR sv.metadata->>'vector_type' = filter_vector_type)
    ORDER BY sv.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- Grant access to the function
GRANT EXECUTE ON FUNCTION match_scripts TO anon, authenticated;

-- Create RLS policies (optional but recommended)
ALTER TABLE script_vectors ENABLE ROW LEVEL SECURITY;

-- Allow all operations for now (adjust based on your security needs)
CREATE POLICY "Allow all operations on script_vectors"
ON script_vectors
FOR ALL
USING (true)
WITH CHECK (true);

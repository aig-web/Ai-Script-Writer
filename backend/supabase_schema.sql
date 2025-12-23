-- ScriptAI Pro - Supabase Schema
-- Run this in your Supabase SQL Editor to set up the database

-- Enable the pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- ============================================
-- SESSION MANAGEMENT TABLES (Version 2.0)
-- ============================================

-- Sessions table: Stores each generation session by topic
CREATE TABLE IF NOT EXISTS sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    topic TEXT NOT NULL,
    mode TEXT NOT NULL DEFAULT 'informational',
    user_notes TEXT DEFAULT '',
    research_data TEXT DEFAULT '',
    research_sources JSONB DEFAULT '[]',
    topic_type TEXT DEFAULT 'A',
    skip_research BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Session files table: Stores uploaded file metadata
CREATE TABLE IF NOT EXISTS session_files (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    file_name TEXT NOT NULL,
    file_type TEXT NOT NULL,
    file_content TEXT NOT NULL,
    file_size INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Session scripts table: Stores the 3 generated scripts per session
CREATE TABLE IF NOT EXISTS session_scripts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    script_number INTEGER NOT NULL CHECK (script_number BETWEEN 1 AND 3),
    angle_name TEXT DEFAULT '',
    angle_focus TEXT DEFAULT '',
    angle_hook_style TEXT DEFAULT '',
    script_content TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(session_id, script_number)
);

-- Chat messages table: Stores per-script chat history
CREATE TABLE IF NOT EXISTS chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    script_number INTEGER NOT NULL CHECK (script_number BETWEEN 1 AND 3),
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for faster queries
CREATE INDEX IF NOT EXISTS idx_sessions_topic ON sessions(topic);
CREATE INDEX IF NOT EXISTS idx_sessions_created_at ON sessions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_session_files_session_id ON session_files(session_id);
CREATE INDEX IF NOT EXISTS idx_session_scripts_session_id ON session_scripts(session_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_session_script ON chat_messages(session_id, script_number);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for updated_at
DROP TRIGGER IF EXISTS update_sessions_updated_at ON sessions;
CREATE TRIGGER update_sessions_updated_at
    BEFORE UPDATE ON sessions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_session_scripts_updated_at ON session_scripts;
CREATE TRIGGER update_session_scripts_updated_at
    BEFORE UPDATE ON session_scripts
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- RLS Policies for session tables
ALTER TABLE sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE session_files ENABLE ROW LEVEL SECURITY;
ALTER TABLE session_scripts ENABLE ROW LEVEL SECURITY;
ALTER TABLE chat_messages ENABLE ROW LEVEL SECURITY;

-- Allow all operations for now (public access - adjust for production)
CREATE POLICY "Allow all on sessions" ON sessions FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all on session_files" ON session_files FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all on session_scripts" ON session_scripts FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all on chat_messages" ON chat_messages FOR ALL USING (true) WITH CHECK (true);

-- ============================================
-- VECTOR STORAGE TABLES (Version 1.0)
-- ============================================

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

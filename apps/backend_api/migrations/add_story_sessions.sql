-- Migration: Add StorySession table for narrative generation tracking
-- Compatible with both PostgreSQL and SQLite

-- Create story content type enum (PostgreSQL only)
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'story_content_type') THEN
        CREATE TYPE story_content_type AS ENUM ('summary', 'story', 'reflection', 'achievement');
    END IF;
END $$;

-- Create posting status enum (PostgreSQL only)
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'posting_status') THEN
        CREATE TYPE posting_status AS ENUM ('draft', 'scheduled', 'posted', 'failed');
    END IF;
END $$;

-- Create processing status enum (PostgreSQL only)
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'processing_status') THEN
        CREATE TYPE processing_status AS ENUM ('pending', 'generating', 'completed', 'failed');
    END IF;
END $$;

-- Create story_sessions table
CREATE TABLE IF NOT EXISTS story_sessions (
    id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid()::text,
    user_id VARCHAR NOT NULL REFERENCES users(uid) ON DELETE CASCADE,
    
    -- Content information
    title VARCHAR(200),
    generated_text TEXT,
    video_url VARCHAR,
    audio_url VARCHAR,
    thumbnail_url VARCHAR,
    
    -- Generation parameters
    summary_period VARCHAR,
    period_start TIMESTAMP WITH TIME ZONE,
    period_end TIMESTAMP WITH TIME ZONE,
    content_type story_content_type DEFAULT 'summary',
    
    -- Social media and distribution
    posted_to JSONB DEFAULT '[]'::jsonb,
    posting_status posting_status DEFAULT 'draft',
    scheduled_post_time TIMESTAMP WITH TIME ZONE,
    
    -- Generation metadata
    generation_prompt TEXT,
    model_version VARCHAR,
    generation_params JSONB,
    word_count INTEGER CHECK (word_count >= 0),
    estimated_read_time INTEGER CHECK (estimated_read_time >= 0),
    
    -- Related content
    source_goals JSONB DEFAULT '[]'::jsonb,
    source_tasks JSONB DEFAULT '[]'::jsonb,
    source_life_areas JSONB DEFAULT '[]'::jsonb,
    
    -- Engagement and analytics
    view_count INTEGER DEFAULT 0 CHECK (view_count >= 0),
    like_count INTEGER DEFAULT 0 CHECK (like_count >= 0),
    share_count INTEGER DEFAULT 0 CHECK (share_count >= 0),
    engagement_data JSONB,
    
    -- Quality and user feedback
    user_rating DECIMAL(2,1) CHECK (user_rating IS NULL OR (user_rating >= 1.0 AND user_rating <= 5.0)),
    user_notes TEXT,
    regeneration_count INTEGER DEFAULT 0 CHECK (regeneration_count >= 0),
    
    -- Processing status
    processing_status processing_status DEFAULT 'pending',
    error_message TEXT,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    generated_at TIMESTAMP WITH TIME ZONE,
    posted_at TIMESTAMP WITH TIME ZONE
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_story_sessions_user_id ON story_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_story_sessions_content_type ON story_sessions(content_type);
CREATE INDEX IF NOT EXISTS idx_story_sessions_posting_status ON story_sessions(posting_status);
CREATE INDEX IF NOT EXISTS idx_story_sessions_processing_status ON story_sessions(processing_status);
CREATE INDEX IF NOT EXISTS idx_story_sessions_summary_period ON story_sessions(summary_period);
CREATE INDEX IF NOT EXISTS idx_story_sessions_created_at ON story_sessions(created_at);
CREATE INDEX IF NOT EXISTS idx_story_sessions_generated_at ON story_sessions(generated_at) WHERE generated_at IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_story_sessions_posted_at ON story_sessions(posted_at) WHERE posted_at IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_story_sessions_period_range ON story_sessions(period_start, period_end) WHERE period_start IS NOT NULL AND period_end IS NOT NULL;

-- SQLite compatible version (use this instead if using SQLite)
-- CREATE TABLE IF NOT EXISTS story_sessions (
--     id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(4))) || '-' || lower(hex(randomblob(2))) || '-' || lower(hex(randomblob(2))) || '-' || lower(hex(randomblob(2))) || '-' || lower(hex(randomblob(6)))),
--     user_id TEXT NOT NULL REFERENCES users(uid) ON DELETE CASCADE,
--     
--     -- Content information
--     title TEXT,
--     generated_text TEXT,
--     video_url TEXT,
--     audio_url TEXT,
--     thumbnail_url TEXT,
--     
--     -- Generation parameters
--     summary_period TEXT,
--     period_start DATETIME,
--     period_end DATETIME,
--     content_type TEXT DEFAULT 'summary' CHECK (content_type IN ('summary', 'story', 'reflection', 'achievement')),
--     
--     -- Social media and distribution
--     posted_to TEXT DEFAULT '[]',  -- JSON stored as TEXT
--     posting_status TEXT DEFAULT 'draft' CHECK (posting_status IN ('draft', 'scheduled', 'posted', 'failed')),
--     scheduled_post_time DATETIME,
--     
--     -- Generation metadata
--     generation_prompt TEXT,
--     model_version TEXT,
--     generation_params TEXT,  -- JSON stored as TEXT
--     word_count INTEGER CHECK (word_count IS NULL OR word_count >= 0),
--     estimated_read_time INTEGER CHECK (estimated_read_time IS NULL OR estimated_read_time >= 0),
--     
--     -- Related content
--     source_goals TEXT DEFAULT '[]',  -- JSON stored as TEXT
--     source_tasks TEXT DEFAULT '[]',  -- JSON stored as TEXT
--     source_life_areas TEXT DEFAULT '[]',  -- JSON stored as TEXT
--     
--     -- Engagement and analytics
--     view_count INTEGER DEFAULT 0 CHECK (view_count >= 0),
--     like_count INTEGER DEFAULT 0 CHECK (like_count >= 0),
--     share_count INTEGER DEFAULT 0 CHECK (share_count >= 0),
--     engagement_data TEXT,  -- JSON stored as TEXT
--     
--     -- Quality and user feedback
--     user_rating REAL CHECK (user_rating IS NULL OR (user_rating >= 1.0 AND user_rating <= 5.0)),
--     user_notes TEXT,
--     regeneration_count INTEGER DEFAULT 0 CHECK (regeneration_count >= 0),
--     
--     -- Processing status
--     processing_status TEXT DEFAULT 'pending' CHECK (processing_status IN ('pending', 'generating', 'completed', 'failed')),
--     error_message TEXT,
--     
--     -- Timestamps
--     created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
--     updated_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
--     generated_at DATETIME,
--     posted_at DATETIME
-- );

-- Comments for documentation
COMMENT ON TABLE story_sessions IS 'Stores AI-generated narrative content sessions for users';
COMMENT ON COLUMN story_sessions.title IS 'User-defined title for the story session';
COMMENT ON COLUMN story_sessions.generated_text IS 'AI-generated narrative text content';
COMMENT ON COLUMN story_sessions.video_url IS 'URL to generated video content';
COMMENT ON COLUMN story_sessions.audio_url IS 'URL to generated audio/narration';
COMMENT ON COLUMN story_sessions.thumbnail_url IS 'URL to video thumbnail image';
COMMENT ON COLUMN story_sessions.summary_period IS 'Type of summary period: weekly, monthly, project-based, custom';
COMMENT ON COLUMN story_sessions.period_start IS 'Start date of the period being summarized';
COMMENT ON COLUMN story_sessions.period_end IS 'End date of the period being summarized';
COMMENT ON COLUMN story_sessions.content_type IS 'Type of generated content: summary, story, reflection, achievement';
COMMENT ON COLUMN story_sessions.posted_to IS 'JSON array of platforms where content was posted';
COMMENT ON COLUMN story_sessions.posting_status IS 'Current posting status: draft, scheduled, posted, failed';
COMMENT ON COLUMN story_sessions.scheduled_post_time IS 'When content is scheduled to be posted';
COMMENT ON COLUMN story_sessions.generation_prompt IS 'The prompt used for AI generation';
COMMENT ON COLUMN story_sessions.model_version IS 'Version of AI model used for generation';
COMMENT ON COLUMN story_sessions.generation_params IS 'JSON object with generation parameters';
COMMENT ON COLUMN story_sessions.word_count IS 'Number of words in generated text';
COMMENT ON COLUMN story_sessions.estimated_read_time IS 'Estimated reading time in seconds';
COMMENT ON COLUMN story_sessions.source_goals IS 'JSON array of goal IDs that contributed to this story';
COMMENT ON COLUMN story_sessions.source_tasks IS 'JSON array of task IDs that contributed to this story';
COMMENT ON COLUMN story_sessions.source_life_areas IS 'JSON array of life area IDs featured in this story';
COMMENT ON COLUMN story_sessions.view_count IS 'Number of times this story was viewed';
COMMENT ON COLUMN story_sessions.like_count IS 'Number of likes received (if posted)';
COMMENT ON COLUMN story_sessions.share_count IS 'Number of shares/reposts';
COMMENT ON COLUMN story_sessions.engagement_data IS 'JSON object with additional engagement metrics';
COMMENT ON COLUMN story_sessions.user_rating IS 'User rating from 1.0 to 5.0 stars';
COMMENT ON COLUMN story_sessions.user_notes IS 'User notes and feedback about the story';
COMMENT ON COLUMN story_sessions.regeneration_count IS 'Number of times this story was regenerated';
COMMENT ON COLUMN story_sessions.processing_status IS 'Current processing status: pending, generating, completed, failed';
COMMENT ON COLUMN story_sessions.error_message IS 'Error message if generation failed';
COMMENT ON COLUMN story_sessions.generated_at IS 'When the content generation was completed';
COMMENT ON COLUMN story_sessions.posted_at IS 'When the content was actually posted to platforms';
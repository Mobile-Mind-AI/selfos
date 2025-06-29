-- Migration: Add FeedbackLog table for collecting training data and user feedback
-- Compatible with both PostgreSQL and SQLite

-- Create feedback_type enum (PostgreSQL only)
-- For SQLite, this is handled as a check constraint
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'feedback_type') THEN
        CREATE TYPE feedback_type AS ENUM ('positive', 'negative', 'neutral');
    END IF;
END $$;

-- Create feedback_logs table
CREATE TABLE IF NOT EXISTS feedback_logs (
    id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid()::text,
    user_id VARCHAR NOT NULL REFERENCES users(uid) ON DELETE CASCADE,
    
    -- Context information for the feedback
    context_type VARCHAR NOT NULL,
    context_id VARCHAR,
    context_data JSONB,
    
    -- Feedback details
    feedback_type feedback_type NOT NULL,
    feedback_value DECIMAL(3,2),  -- For numeric feedback scores (-1.0 to 1.0)
    comment TEXT,
    
    -- ML/RLHF specific fields
    action_taken JSONB,
    reward_signal DECIMAL(10,6),
    model_version VARCHAR,
    
    -- Metadata
    session_id VARCHAR,
    device_info JSONB,
    feature_flags JSONB,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    processed_at TIMESTAMP WITH TIME ZONE
);

-- Add constraints
ALTER TABLE feedback_logs 
ADD CONSTRAINT check_feedback_value_range 
CHECK (feedback_value IS NULL OR (feedback_value >= -1.0 AND feedback_value <= 1.0));

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_feedback_logs_user_id ON feedback_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_feedback_logs_context_type ON feedback_logs(context_type);
CREATE INDEX IF NOT EXISTS idx_feedback_logs_feedback_type ON feedback_logs(feedback_type);
CREATE INDEX IF NOT EXISTS idx_feedback_logs_session_id ON feedback_logs(session_id);
CREATE INDEX IF NOT EXISTS idx_feedback_logs_created_at ON feedback_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_feedback_logs_processed_at ON feedback_logs(processed_at) WHERE processed_at IS NOT NULL;

-- SQLite compatible version (use this instead if using SQLite)
-- CREATE TABLE IF NOT EXISTS feedback_logs (
--     id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(4))) || '-' || lower(hex(randomblob(2))) || '-' || lower(hex(randomblob(2))) || '-' || lower(hex(randomblob(2))) || '-' || lower(hex(randomblob(6)))),
--     user_id TEXT NOT NULL REFERENCES users(uid) ON DELETE CASCADE,
--     
--     -- Context information for the feedback
--     context_type TEXT NOT NULL,
--     context_id TEXT,
--     context_data TEXT,  -- JSON stored as TEXT
--     
--     -- Feedback details
--     feedback_type TEXT NOT NULL CHECK (feedback_type IN ('positive', 'negative', 'neutral')),
--     feedback_value REAL CHECK (feedback_value IS NULL OR (feedback_value >= -1.0 AND feedback_value <= 1.0)),
--     comment TEXT,
--     
--     -- ML/RLHF specific fields
--     action_taken TEXT,  -- JSON stored as TEXT
--     reward_signal REAL,
--     model_version TEXT,
--     
--     -- Metadata
--     session_id TEXT,
--     device_info TEXT,  -- JSON stored as TEXT
--     feature_flags TEXT,  -- JSON stored as TEXT
--     
--     -- Timestamps
--     created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
--     processed_at DATETIME
-- );

-- Comments for documentation
COMMENT ON TABLE feedback_logs IS 'Stores user feedback and training signals for ML/RLHF';
COMMENT ON COLUMN feedback_logs.context_type IS 'Type of interaction: task, goal, plan, suggestion, ui_interaction, etc.';
COMMENT ON COLUMN feedback_logs.context_id IS 'ID of the related entity (goal_id, task_id, etc.)';
COMMENT ON COLUMN feedback_logs.context_data IS 'Additional context data (query, response, UI state, etc.)';
COMMENT ON COLUMN feedback_logs.feedback_type IS 'Type of feedback: positive, negative, or neutral';
COMMENT ON COLUMN feedback_logs.feedback_value IS 'Numeric feedback score from -1.0 (very negative) to 1.0 (very positive)';
COMMENT ON COLUMN feedback_logs.action_taken IS 'What action was taken by the system (for reinforcement learning)';
COMMENT ON COLUMN feedback_logs.reward_signal IS 'Computed reward signal for training';
COMMENT ON COLUMN feedback_logs.model_version IS 'Version of AI model that generated the response being rated';
COMMENT ON COLUMN feedback_logs.session_id IS 'Session identifier for grouping related feedback';
COMMENT ON COLUMN feedback_logs.processed_at IS 'When this feedback was processed for training (NULL if not yet processed)';
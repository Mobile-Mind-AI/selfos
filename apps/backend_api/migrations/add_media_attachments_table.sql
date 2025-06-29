-- Migration: Add media_attachments table
-- Date: 2025-06-29
-- Description: Add MediaAttachment model for storing file attachments for tasks/goals

CREATE TABLE media_attachments (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL REFERENCES users(uid),
    goal_id INTEGER REFERENCES goals(id),
    task_id INTEGER REFERENCES tasks(id),
    
    -- File information
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size INTEGER NOT NULL CHECK (file_size >= 0),
    mime_type VARCHAR(100) NOT NULL,
    file_type VARCHAR(50) NOT NULL CHECK (file_type IN ('image', 'video', 'audio', 'document')),
    
    -- Optional metadata for storytelling
    title VARCHAR(200),
    description TEXT,
    duration INTEGER CHECK (duration >= 0),  -- Duration in seconds for video/audio
    width INTEGER CHECK (width >= 0),        -- Width in pixels for images/videos
    height INTEGER CHECK (height >= 0),      -- Height in pixels for images/videos
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX idx_media_attachments_user_id ON media_attachments(user_id);
CREATE INDEX idx_media_attachments_goal_id ON media_attachments(goal_id) WHERE goal_id IS NOT NULL;
CREATE INDEX idx_media_attachments_task_id ON media_attachments(task_id) WHERE task_id IS NOT NULL;
CREATE INDEX idx_media_attachments_file_type ON media_attachments(file_type);
CREATE INDEX idx_media_attachments_created_at ON media_attachments(created_at DESC);

-- Comments for documentation
COMMENT ON TABLE media_attachments IS 'File attachments for goals and tasks to support storytelling';
COMMENT ON COLUMN media_attachments.filename IS 'System-generated unique filename';
COMMENT ON COLUMN media_attachments.original_filename IS 'Original filename from user upload';
COMMENT ON COLUMN media_attachments.file_path IS 'Full path to stored file on filesystem';
COMMENT ON COLUMN media_attachments.file_size IS 'File size in bytes';
COMMENT ON COLUMN media_attachments.mime_type IS 'MIME type (e.g., image/jpeg, video/mp4, audio/mpeg)';
COMMENT ON COLUMN media_attachments.file_type IS 'File category: image, video, audio, document';
COMMENT ON COLUMN media_attachments.title IS 'User-defined title for the attachment';
COMMENT ON COLUMN media_attachments.description IS 'User description for storytelling purposes';
COMMENT ON COLUMN media_attachments.duration IS 'Duration in seconds for video/audio files';
COMMENT ON COLUMN media_attachments.width IS 'Width in pixels for images/videos';
COMMENT ON COLUMN media_attachments.height IS 'Height in pixels for images/videos';
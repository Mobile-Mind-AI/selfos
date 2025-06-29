-- Migration: Add UserPreferences table
-- Created: 2025-06-29
-- Description: Add user preferences table to store user customization settings

-- Create enum types first
CREATE TYPE tone_style AS ENUM ('friendly', 'coach', 'minimal', 'professional');
CREATE TYPE view_mode AS ENUM ('list', 'card', 'timeline');

-- Create user_preferences table
CREATE TABLE user_preferences (
    id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid()::text,
    user_id VARCHAR NOT NULL UNIQUE REFERENCES users(uid) ON DELETE CASCADE,
    
    -- Tone and communication preferences
    tone tone_style DEFAULT 'friendly',
    
    -- Notification preferences
    notification_time TIME,
    notifications_enabled BOOLEAN DEFAULT true,
    email_notifications BOOLEAN DEFAULT false,
    
    -- Content and visualization preferences
    prefers_video BOOLEAN DEFAULT true,
    prefers_audio BOOLEAN DEFAULT false,
    default_view view_mode DEFAULT 'card',
    
    -- Feature preferences
    mood_tracking_enabled BOOLEAN DEFAULT false,
    progress_charts_enabled BOOLEAN DEFAULT true,
    ai_suggestions_enabled BOOLEAN DEFAULT true,
    
    -- Default associations
    default_life_area_id INTEGER REFERENCES life_areas(id) ON DELETE SET NULL,
    
    -- Privacy and data preferences
    data_sharing_enabled BOOLEAN DEFAULT false,
    analytics_enabled BOOLEAN DEFAULT true,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX idx_user_preferences_user_id ON user_preferences(user_id);
CREATE INDEX idx_user_preferences_default_life_area ON user_preferences(default_life_area_id);

-- Add trigger to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_user_preferences_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_user_preferences_updated_at
    BEFORE UPDATE ON user_preferences
    FOR EACH ROW
    EXECUTE FUNCTION update_user_preferences_updated_at();

-- SQLite equivalent (comment out PostgreSQL version above and use this for SQLite)
/*
CREATE TABLE user_preferences (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    user_id TEXT NOT NULL UNIQUE REFERENCES users(uid) ON DELETE CASCADE,
    
    -- Tone and communication preferences
    tone TEXT CHECK(tone IN ('friendly', 'coach', 'minimal', 'professional')) DEFAULT 'friendly',
    
    -- Notification preferences  
    notification_time TEXT, -- Stored as HH:MM format
    notifications_enabled BOOLEAN DEFAULT 1,
    email_notifications BOOLEAN DEFAULT 0,
    
    -- Content and visualization preferences
    prefers_video BOOLEAN DEFAULT 1,
    prefers_audio BOOLEAN DEFAULT 0,
    default_view TEXT CHECK(default_view IN ('list', 'card', 'timeline')) DEFAULT 'card',
    
    -- Feature preferences
    mood_tracking_enabled BOOLEAN DEFAULT 0,
    progress_charts_enabled BOOLEAN DEFAULT 1,
    ai_suggestions_enabled BOOLEAN DEFAULT 1,
    
    -- Default associations
    default_life_area_id INTEGER REFERENCES life_areas(id) ON DELETE SET NULL,
    
    -- Privacy and data preferences
    data_sharing_enabled BOOLEAN DEFAULT 0,
    analytics_enabled BOOLEAN DEFAULT 1,
    
    -- Timestamps
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX idx_user_preferences_user_id ON user_preferences(user_id);
CREATE INDEX idx_user_preferences_default_life_area ON user_preferences(default_life_area_id);

-- SQLite trigger for updated_at
CREATE TRIGGER update_user_preferences_updated_at
    AFTER UPDATE ON user_preferences
BEGIN
    UPDATE user_preferences 
    SET updated_at = CURRENT_TIMESTAMP 
    WHERE id = NEW.id;
END;
*/
-- Migration: Add life_areas table
-- Date: 2025-06-29
-- Description: Add LifeArea model to track user life balance domains

CREATE TABLE life_areas (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL REFERENCES users(uid),
    name VARCHAR(100) NOT NULL,
    weight INTEGER NOT NULL DEFAULT 10 CHECK (weight >= 0 AND weight <= 100),
    icon VARCHAR(50),
    color VARCHAR(50),
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Ensure unique life area names per user
    UNIQUE(user_id, name)
);

-- Create indexes for better performance
CREATE INDEX idx_life_areas_user_id ON life_areas(user_id);
CREATE INDEX idx_life_areas_weight ON life_areas(weight DESC);

-- Comments for documentation
COMMENT ON TABLE life_areas IS 'User-defined life domains for tracking balance and personalization';
COMMENT ON COLUMN life_areas.weight IS 'Importance weight as percentage (0-100)';
COMMENT ON COLUMN life_areas.icon IS 'UI icon identifier for display';
COMMENT ON COLUMN life_areas.color IS 'UI color preference (hex or color name)';
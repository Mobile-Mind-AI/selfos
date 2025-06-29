-- Migration: Update model relationships
-- Date: 2025-06-29
-- Description: Add life_area_id to goals/tasks and remove redundant media_urls

-- Add life_area_id column to goals table
ALTER TABLE goals ADD COLUMN life_area_id INTEGER REFERENCES life_areas(id);

-- Add life_area_id column to tasks table  
ALTER TABLE tasks ADD COLUMN life_area_id INTEGER REFERENCES life_areas(id);

-- Remove redundant media_urls columns (replaced by MediaAttachment model)
ALTER TABLE goals DROP COLUMN IF EXISTS media_urls;
ALTER TABLE tasks DROP COLUMN IF EXISTS media_urls;

-- Create indexes for better performance
CREATE INDEX idx_goals_life_area_id ON goals(life_area_id) WHERE life_area_id IS NOT NULL;
CREATE INDEX idx_tasks_life_area_id ON tasks(life_area_id) WHERE life_area_id IS NOT NULL;

-- Comments for documentation
COMMENT ON COLUMN goals.life_area_id IS 'Optional life area association for balance tracking';
COMMENT ON COLUMN tasks.life_area_id IS 'Optional life area association for balance tracking';
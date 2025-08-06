-- Migration: Add hierarchy support to tasks table
-- This migration adds parent_id column to enable hierarchical task structures

-- Add parent_id column to tasks table
ALTER TABLE tasks ADD COLUMN parent_id INTEGER;

-- Add foreign key constraint to reference the same table
ALTER TABLE tasks ADD CONSTRAINT fk_tasks_parent_id FOREIGN KEY (parent_id) REFERENCES tasks(id) ON DELETE CASCADE;

-- Add indexes for performance
CREATE INDEX idx_tasks_parent_id ON tasks(parent_id);
CREATE INDEX idx_tasks_user_parent ON tasks(user_id, parent_id);

-- Note: This migration is compatible with existing data as parent_id is nullable

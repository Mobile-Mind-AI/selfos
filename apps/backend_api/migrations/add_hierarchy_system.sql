-- Migration: Add Hierarchical Support to Goals and Projects
-- Date: 2025-01-08
-- Description: Adds parent_id fields to goals and projects tables to support hierarchical (nested) structures

-- Add parent_id column to goals table
ALTER TABLE goals 
ADD COLUMN parent_id INTEGER REFERENCES goals(id) ON DELETE CASCADE;

-- Add parent_id column to projects table  
ALTER TABLE projects 
ADD COLUMN parent_id INTEGER REFERENCES projects(id) ON DELETE CASCADE;

-- Add indexes for performance optimization
CREATE INDEX ix_goals_parent_id ON goals(parent_id);
CREATE INDEX ix_goals_user_parent ON goals(user_id, parent_id);
CREATE INDEX ix_projects_parent_id ON projects(parent_id);
CREATE INDEX ix_projects_user_parent ON projects(user_id, parent_id);

-- Add comments for documentation
COMMENT ON COLUMN goals.parent_id IS 'Reference to parent goal for hierarchical structure. NULL for root-level goals.';
COMMENT ON COLUMN projects.parent_id IS 'Reference to parent project for hierarchical structure. NULL for root-level projects.';

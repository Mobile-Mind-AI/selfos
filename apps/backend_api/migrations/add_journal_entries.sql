-- Migration: Add journal entries system
-- Description: Create journal_entries table for user journaling functionality
-- Date: 2025-08-06

-- Create journal_entries table
CREATE TABLE IF NOT EXISTS journal_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    content TEXT NOT NULL,
    project_id INTEGER NULL,
    goal_id INTEGER NULL,
    task_id INTEGER NULL,
    version INTEGER NOT NULL DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    -- Foreign key constraints
    FOREIGN KEY (user_id) REFERENCES users (uid) ON DELETE CASCADE,
    FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE,
    FOREIGN KEY (goal_id) REFERENCES goals (id) ON DELETE CASCADE,
    FOREIGN KEY (task_id) REFERENCES tasks (id) ON DELETE CASCADE
);

-- Create performance indexes for journal_entries
CREATE INDEX IF NOT EXISTS ix_journal_entries_user_created
    ON journal_entries (user_id, created_at DESC);

CREATE INDEX IF NOT EXISTS ix_journal_entries_project_created
    ON journal_entries (project_id, created_at DESC);

CREATE INDEX IF NOT EXISTS ix_journal_entries_goal_created
    ON journal_entries (goal_id, created_at DESC);

CREATE INDEX IF NOT EXISTS ix_journal_entries_task_created
    ON journal_entries (task_id, created_at DESC);

-- Add basic indexes
CREATE INDEX IF NOT EXISTS ix_journal_entries_id ON journal_entries (id);

-- Add trigger for updating updated_at timestamp
CREATE TRIGGER IF NOT EXISTS update_journal_entries_updated_at
AFTER UPDATE ON journal_entries
FOR EACH ROW
BEGIN
    UPDATE journal_entries SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

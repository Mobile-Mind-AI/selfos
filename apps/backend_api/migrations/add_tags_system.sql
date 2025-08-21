-- Tags System Migration
-- Adds tags table and association tables for many-to-many relationships

-- Create tags table
CREATE TABLE tags (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR NOT NULL REFERENCES users(uid) ON DELETE CASCADE,
    name VARCHAR NOT NULL,
    color VARCHAR,
    version INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create unique constraint for tag names per user
CREATE UNIQUE INDEX uq_user_tag_name ON tags(user_id, name);

-- Create association tables for many-to-many relationships

-- Project tags association
CREATE TABLE project_tags (
    project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
    tag_id INTEGER REFERENCES tags(id) ON DELETE CASCADE,
    PRIMARY KEY (project_id, tag_id)
);

-- Goal tags association
CREATE TABLE goal_tags (
    goal_id INTEGER REFERENCES goals(id) ON DELETE CASCADE,
    tag_id INTEGER REFERENCES tags(id) ON DELETE CASCADE,
    PRIMARY KEY (goal_id, tag_id)
);

-- Task tags association
CREATE TABLE task_tags (
    task_id INTEGER REFERENCES tasks(id) ON DELETE CASCADE,
    tag_id INTEGER REFERENCES tags(id) ON DELETE CASCADE,
    PRIMARY KEY (task_id, tag_id)
);

-- Habit tags association
CREATE TABLE habit_tags (
    habit_id INTEGER REFERENCES habits(id) ON DELETE CASCADE,
    tag_id INTEGER REFERENCES tags(id) ON DELETE CASCADE,
    PRIMARY KEY (habit_id, tag_id)
);

-- Journal entry tags association
CREATE TABLE journal_entry_tags (
    journal_entry_id INTEGER REFERENCES journal_entries(id) ON DELETE CASCADE,
    tag_id INTEGER REFERENCES tags(id) ON DELETE CASCADE,
    PRIMARY KEY (journal_entry_id, tag_id)
);

-- Add performance indexes

-- Tags table indexes
CREATE INDEX ix_tags_user_created ON tags(user_id, created_at DESC);
CREATE INDEX ix_tags_user_name ON tags(user_id, name);

-- Association table indexes for efficient queries
CREATE INDEX ix_project_tags_project ON project_tags(project_id);
CREATE INDEX ix_project_tags_tag ON project_tags(tag_id);

CREATE INDEX ix_goal_tags_goal ON goal_tags(goal_id);
CREATE INDEX ix_goal_tags_tag ON goal_tags(tag_id);

CREATE INDEX ix_task_tags_task ON task_tags(task_id);
CREATE INDEX ix_task_tags_tag ON task_tags(tag_id);

CREATE INDEX ix_habit_tags_habit ON habit_tags(habit_id);
CREATE INDEX ix_habit_tags_tag ON habit_tags(tag_id);

CREATE INDEX ix_journal_entry_tags_entry ON journal_entry_tags(journal_entry_id);
CREATE INDEX ix_journal_entry_tags_tag ON journal_entry_tags(tag_id);

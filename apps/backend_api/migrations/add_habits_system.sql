-- Migration: Add habits system
-- Date: 2025-01-08
-- Description: Add Habit and HabitCompletion models for flexible recurring task tracking

-- Table for habit definitions
CREATE TABLE habits (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL REFERENCES users(uid),
    goal_id INTEGER REFERENCES goals(id) ON DELETE SET NULL,
    life_area_id INTEGER REFERENCES life_areas(id) ON DELETE SET NULL,

    -- Basic habit information
    title VARCHAR(200) NOT NULL,
    description TEXT,

    -- Recurrence configuration (stored as JSON for flexibility)
    recurrence_rule JSON NOT NULL DEFAULT '{}',
    -- Example: {"type": "weekly", "target_count": 3, "target_type": "count"}
    -- Example: {"type": "daily", "target_count": 1, "target_type": "count"}
    -- Example: {"type": "monthly", "target_count": 10, "target_type": "count"}

    -- Habit configuration
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    start_date DATE NOT NULL DEFAULT CURRENT_DATE,
    end_date DATE, -- Optional end date for temporary habits

    -- UI configuration
    icon VARCHAR(50),
    color VARCHAR(50),

    -- Progress tracking metadata
    current_streak INTEGER NOT NULL DEFAULT 0,
    best_streak INTEGER NOT NULL DEFAULT 0,
    total_completions INTEGER NOT NULL DEFAULT 0,

    -- Versioning for sync
    version INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CONSTRAINT chk_start_before_end CHECK (end_date IS NULL OR end_date >= start_date),
    CONSTRAINT chk_positive_streaks CHECK (current_streak >= 0 AND best_streak >= 0),
    CONSTRAINT chk_positive_completions CHECK (total_completions >= 0)
);

-- Table for individual habit completions
CREATE TABLE habit_completions (
    id SERIAL PRIMARY KEY,
    habit_id INTEGER NOT NULL REFERENCES habits(id) ON DELETE CASCADE,

    -- When the habit was completed
    completion_date DATE NOT NULL DEFAULT CURRENT_DATE,
    completion_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- Optional metadata about the completion
    notes TEXT,
    duration_minutes INTEGER, -- For habits that track time (e.g., "meditate for 10 minutes")
    intensity_rating INTEGER CHECK (intensity_rating >= 1 AND intensity_rating <= 10), -- Optional 1-10 rating

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- Prevent duplicate completions on the same date for the same habit
    UNIQUE(habit_id, completion_date)
);

-- Performance indexes for habits
CREATE INDEX idx_habits_user_id ON habits(user_id);
CREATE INDEX idx_habits_user_active ON habits(user_id, is_active) WHERE is_active = TRUE;
CREATE INDEX idx_habits_goal_id ON habits(goal_id) WHERE goal_id IS NOT NULL;
CREATE INDEX idx_habits_life_area_id ON habits(life_area_id) WHERE life_area_id IS NOT NULL;
CREATE INDEX idx_habits_created ON habits(created_at DESC);

-- Performance indexes for habit_completions
CREATE INDEX idx_habit_completions_habit_id ON habit_completions(habit_id);
CREATE INDEX idx_habit_completions_date ON habit_completions(completion_date DESC);
CREATE INDEX idx_habit_completions_habit_date ON habit_completions(habit_id, completion_date DESC);
CREATE INDEX idx_habit_completions_created ON habit_completions(created_at DESC);

-- Comments for documentation
COMMENT ON TABLE habits IS 'User-defined recurring habits with flexible scheduling';
COMMENT ON COLUMN habits.recurrence_rule IS 'JSON configuration for habit frequency and targets';
COMMENT ON COLUMN habits.current_streak IS 'Current consecutive completion streak';
COMMENT ON COLUMN habits.best_streak IS 'Highest streak ever achieved for this habit';
COMMENT ON COLUMN habits.total_completions IS 'Lifetime total completion count';

COMMENT ON TABLE habit_completions IS 'Individual records of habit completion events';
COMMENT ON COLUMN habit_completions.duration_minutes IS 'Optional duration tracking (e.g., exercise minutes)';
COMMENT ON COLUMN habit_completions.intensity_rating IS 'Optional 1-10 subjective intensity rating';

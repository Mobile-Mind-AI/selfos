-- Add user preferences history table for analytics
-- This tracks all changes to user preferences over time

CREATE TABLE IF NOT EXISTS user_preferences_history (
    id VARCHAR PRIMARY KEY,
    user_id VARCHAR NOT NULL,
    preference_name VARCHAR NOT NULL,
    old_value VARCHAR,
    new_value VARCHAR,
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(uid) ON DELETE CASCADE
);

-- Indexes for efficient queries
CREATE INDEX IF NOT EXISTS ix_user_preferences_history_id ON user_preferences_history(id);
CREATE INDEX IF NOT EXISTS ix_user_preferences_history_user_id ON user_preferences_history(user_id);
CREATE INDEX IF NOT EXISTS ix_user_preferences_history_changed_at ON user_preferences_history(changed_at);
CREATE INDEX IF NOT EXISTS ix_user_prefs_history_user_time ON user_preferences_history(user_id, changed_at DESC);
CREATE INDEX IF NOT EXISTS ix_user_prefs_history_pref_name ON user_preferences_history(preference_name);

-- Add relationship to users table (this will be handled by SQLAlchemy ORM)
-- The relationship is already defined in the User model as preferences_history

-- Example usage:
-- To track a preference change:
-- INSERT INTO user_preferences_history (id, user_id, preference_name, old_value, new_value)
-- VALUES ('uuid-here', 'user-id', 'tone', 'friendly', 'coach');

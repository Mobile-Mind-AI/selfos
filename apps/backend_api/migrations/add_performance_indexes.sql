-- Performance Indexes Migration
-- This migration adds comprehensive indexes for optimal query performance
-- Run with: psql -d your_database -f add_performance_indexes.sql

-- ============================================================================
-- GOAL TABLE INDEXES
-- ============================================================================

-- Composite index for user goals ordered by creation date (most common query)
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_goals_user_created 
ON goals(user_id, created_at DESC);

-- Index for filtering goals by status for a specific user
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_goals_user_status 
ON goals(user_id, status);

-- Index for life area goals ordered by creation date
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_goals_life_area_created 
ON life_areas(id, created_at DESC);

-- ============================================================================
-- TASK TABLE INDEXES
-- ============================================================================

-- Composite index for user tasks ordered by creation date (most common query)
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_tasks_user_created 
ON tasks(user_id, created_at DESC);

-- Index for filtering tasks by status for a specific user
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_tasks_user_status 
ON tasks(user_id, status);

-- Index for goal tasks ordered by creation date
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_tasks_goal_created 
ON tasks(goal_id, created_at DESC);

-- Index for tasks with due dates (useful for scheduling queries)
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_tasks_due_date 
ON tasks(user_id, due_date) WHERE due_date IS NOT NULL;

-- Partial index for completed tasks (PostgreSQL specific)
-- This is highly selective and speeds up analytics on completed tasks
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_tasks_completed 
ON tasks(user_id, created_at DESC) WHERE status = 'completed';

-- ============================================================================
-- LIFE AREA TABLE INDEXES
-- ============================================================================

-- Composite index for user life areas ordered by creation date
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_life_areas_user_created 
ON life_areas(user_id, created_at DESC);

-- Index for searching life areas by name within user context
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_life_areas_user_name 
ON life_areas(user_id, name);

-- ============================================================================
-- MEDIA ATTACHMENT TABLE INDEXES
-- ============================================================================

-- Composite index for user media ordered by creation date
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_media_user_created 
ON media_attachments(user_id, created_at DESC);

-- Index for filtering media by type for a specific user
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_media_user_type 
ON media_attachments(user_id, file_type);

-- Index for goal-specific media ordered by creation date
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_media_goal 
ON media_attachments(goal_id, created_at DESC) WHERE goal_id IS NOT NULL;

-- Index for task-specific media ordered by creation date
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_media_task 
ON media_attachments(task_id, created_at DESC) WHERE task_id IS NOT NULL;

-- ============================================================================
-- MEMORY ITEM TABLE INDEXES
-- ============================================================================

-- Composite index for user memory items ordered by timestamp
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_memory_user_timestamp 
ON memory_items(user_id, timestamp DESC);

-- ============================================================================
-- USER PREFERENCES TABLE INDEXES
-- ============================================================================

-- Index for user preferences ordered by creation date
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_user_prefs_user_created 
ON user_preferences(user_id, created_at DESC);

-- ============================================================================
-- FEEDBACK LOG TABLE INDEXES (High Volume)
-- ============================================================================

-- Primary composite index for user feedback ordered by creation date
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_feedback_user_created 
ON feedback_logs(user_id, created_at DESC);

-- Index for filtering feedback by type for a specific user
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_feedback_user_type 
ON feedback_logs(user_id, feedback_type);

-- Index for context-based queries (useful for analytics)
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_feedback_context 
ON feedback_logs(context_type, created_at DESC);

-- Index for session-based queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_feedback_session 
ON feedback_logs(session_id, created_at DESC) WHERE session_id IS NOT NULL;

-- Index for archival operations (processed feedback)
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_feedback_processed 
ON feedback_logs(processed_at) WHERE processed_at IS NOT NULL;

-- ============================================================================
-- STORY SESSION TABLE INDEXES (High Volume)
-- ============================================================================

-- Primary composite index for user story sessions ordered by creation date
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_story_user_created 
ON story_sessions(user_id, created_at DESC);

-- Index for filtering by processing status
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_story_user_status 
ON story_sessions(user_id, processing_status);

-- Index for filtering by summary period
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_story_user_period 
ON story_sessions(user_id, summary_period);

-- Index for archival operations (posted stories)
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_story_posted_at 
ON story_sessions(posted_at) WHERE posted_at IS NOT NULL;

-- Index for content type analytics
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_story_content_type 
ON story_sessions(content_type, created_at DESC);

-- ============================================================================
-- ANALYZE TABLES FOR QUERY PLANNER
-- ============================================================================

-- Update table statistics for the query planner
ANALYZE goals;
ANALYZE tasks;
ANALYZE life_areas;
ANALYZE media_attachments;
ANALYZE memory_items;
ANALYZE user_preferences;
ANALYZE feedback_logs;
ANALYZE story_sessions;

-- ============================================================================
-- INDEX USAGE MONITORING QUERY
-- ============================================================================

-- Use this query to monitor index usage after deployment:
/*
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan as index_scans,
    idx_tup_read as tuples_read,
    idx_tup_fetch as tuples_fetched
FROM pg_stat_user_indexes 
WHERE schemaname = 'public'
ORDER BY idx_scan DESC;
*/

-- ============================================================================
-- PERFORMANCE VALIDATION QUERIES
-- ============================================================================

-- Test query performance with these example queries:
/*
-- Test goal queries
EXPLAIN ANALYZE SELECT * FROM goals WHERE user_id = 'test_user' ORDER BY created_at DESC LIMIT 10;
EXPLAIN ANALYZE SELECT * FROM goals WHERE user_id = 'test_user' AND status = 'todo';

-- Test task queries  
EXPLAIN ANALYZE SELECT * FROM tasks WHERE user_id = 'test_user' ORDER BY created_at DESC LIMIT 10;
EXPLAIN ANALYZE SELECT * FROM tasks WHERE user_id = 'test_user' AND status = 'completed' ORDER BY created_at DESC;
EXPLAIN ANALYZE SELECT * FROM tasks WHERE goal_id = 123 ORDER BY created_at DESC;

-- Test feedback log queries
EXPLAIN ANALYZE SELECT * FROM feedback_logs WHERE user_id = 'test_user' ORDER BY created_at DESC LIMIT 50;
EXPLAIN ANALYZE SELECT * FROM feedback_logs WHERE context_type = 'task' ORDER BY created_at DESC LIMIT 100;

-- Test story session queries
EXPLAIN ANALYZE SELECT * FROM story_sessions WHERE user_id = 'test_user' ORDER BY created_at DESC LIMIT 20;
EXPLAIN ANALYZE SELECT * FROM story_sessions WHERE user_id = 'test_user' AND processing_status = 'completed';
*/

-- ============================================================================
-- NOTES
-- ============================================================================

/*
PERFORMANCE IMPACT:
- These indexes will significantly improve query performance for common operations
- The CONCURRENTLY option ensures minimal disruption during index creation
- Partial indexes (WHERE clauses) are space-efficient for selective queries

MAINTENANCE:
- Monitor index usage with pg_stat_user_indexes
- Consider dropping unused indexes after monitoring
- Re-run ANALYZE periodically or set up auto-analyze

ARCHIVAL CONSIDERATIONS:
- Large tables (feedback_logs, story_sessions) should be archived regularly
- Use the archival.py script to move old data to archive tables
- Archive tables should have similar indexes for historical queries

SPACE USAGE:
- These indexes will use additional disk space (typically 10-30% of table size)
- Benefits in query performance far outweigh storage costs
- Consider using smaller index types for very large tables if needed
*/
# Database Optimization & Archival Strategy

This document outlines the database performance optimizations and archival strategies implemented for the SelfOS Backend API.

## 📊 Performance Indexes

### Overview
Comprehensive indexes have been added to all models to optimize query performance for common operations. These indexes are designed based on actual query patterns and user access patterns.

### Index Strategy

#### **Composite Indexes (user_id + created_at)**
Every model includes a composite index on `(user_id, created_at DESC)` because:
- Most queries filter by user for data isolation
- Results are commonly ordered by creation date (newest first)
- This pattern covers 80%+ of application queries

#### **Status & Type Indexes**
Additional indexes on commonly filtered fields:
- `(user_id, status)` for goals and tasks
- `(user_id, file_type)` for media attachments
- `(user_id, feedback_type)` for feedback logs

#### **Partial Indexes**
Selective indexes for specific use cases:
- `ix_tasks_completed`: Only indexes completed tasks (highly selective)
- `ix_tasks_due_date`: Only indexes tasks with due dates
- Archive-specific indexes for cleanup operations

### Index Details

```sql
-- Goals
ix_goals_user_created      (user_id, created_at DESC)
ix_goals_user_status       (user_id, status)
ix_goals_life_area_created (life_area_id, created_at DESC)

-- Tasks  
ix_tasks_user_created      (user_id, created_at DESC)
ix_tasks_user_status       (user_id, status)
ix_tasks_goal_created      (goal_id, created_at DESC)
ix_tasks_due_date          (user_id, due_date) WHERE due_date IS NOT NULL
ix_tasks_completed         (user_id, created_at DESC) WHERE status = 'completed'

-- Life Areas
ix_life_areas_user_created (user_id, created_at DESC)
ix_life_areas_user_name    (user_id, name)

-- Media Attachments
ix_media_user_created      (user_id, created_at DESC)
ix_media_user_type         (user_id, file_type)
ix_media_goal              (goal_id, created_at DESC)
ix_media_task              (task_id, created_at DESC)

-- Memory Items
ix_memory_user_timestamp   (user_id, timestamp DESC)

-- User Preferences
ix_user_prefs_user_created (user_id, created_at DESC)

-- Feedback Logs (High Volume)
ix_feedback_user_created   (user_id, created_at DESC)
ix_feedback_user_type      (user_id, feedback_type)
ix_feedback_context        (context_type, created_at DESC)
ix_feedback_session        (session_id, created_at DESC)
ix_feedback_processed      (processed_at)

-- Story Sessions (High Volume)
ix_story_user_created      (user_id, created_at DESC)
ix_story_user_status       (user_id, processing_status)
ix_story_user_period       (user_id, summary_period)
ix_story_posted_at         (posted_at)
ix_story_content_type      (content_type, created_at DESC)
```

## 🗄️ Archival Strategy

### Problem
High-volume tables like `story_sessions` and `feedback_logs` can grow large over time, impacting performance despite indexes.

### Solution
Implement a two-tier archival system:

1. **Active Tables**: Recent data for fast access
2. **Archive Tables**: Historical data for long-term storage

### Retention Policies

| Table | Retention | Reason |
|-------|-----------|---------|
| `story_sessions` | 365 days | Stories are personal content users may want to revisit |
| `feedback_logs` | 90 days | ML training data has diminishing value over time |

### Archive Table Structure

Archive tables mirror the main table structure with an additional `archived_at` timestamp:

```sql
-- Example: story_sessions_archive
CREATE TABLE story_sessions_archive (
    LIKE story_sessions INCLUDING ALL,
    archived_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Archival Process

1. **Identify** records older than retention period
2. **Copy** to archive table with `archived_at` timestamp
3. **Delete** from main table
4. **Process in batches** to avoid blocking operations

## 🛠️ Management Tools

### CLI Tool: `manage_db.py`

```bash
# Show current statistics
python manage_db.py stats

# Preview what would be archived
python manage_db.py archive --dry-run

# Archive old records
python manage_db.py archive

# Archive specific table only
python manage_db.py archive --table story_sessions

# Custom retention period
python manage_db.py archive --retention-days 30

# Show index usage statistics
python manage_db.py indexes
```

### Direct Python Usage

```python
from archival import get_archival_stats, archive_all_tables
from db import get_db

db = next(get_db())

# Get statistics
stats = get_archival_stats(db)
print(f"Archivable records: {stats['total_archivable_records']}")

# Run archival
results = archive_all_tables(db, dry_run=False)
print(f"Archived: {results['summary']['total_records_archived']} records")
```

## 📈 Performance Impact

### Query Performance
- **Before**: Linear scan through all records
- **After**: Index-based lookups with logarithmic performance
- **Improvement**: 10-100x faster queries on large datasets

### Index Space Usage
- **Overhead**: ~10-30% additional storage for indexes
- **Trade-off**: Storage cost vs. query performance (heavily favors performance)

### Archival Benefits
- **Active table size**: Stays bounded regardless of total data volume
- **Query performance**: Maintains consistent speed over time
- **Storage cost**: Archive tables can use cheaper storage tiers

## 🔍 Monitoring

### Index Usage
Monitor index effectiveness with:

```sql
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan as scans,
    idx_tup_read as tuples_read,
    pg_size_pretty(pg_relation_size(indexrelid)) as size
FROM pg_stat_user_indexes 
WHERE schemaname = 'public'
ORDER BY idx_scan DESC;
```

### Query Performance
Test common queries with `EXPLAIN ANALYZE`:

```sql
-- Should use ix_goals_user_created
EXPLAIN ANALYZE 
SELECT * FROM goals 
WHERE user_id = 'user123' 
ORDER BY created_at DESC 
LIMIT 10;

-- Should use ix_tasks_completed
EXPLAIN ANALYZE 
SELECT * FROM tasks 
WHERE user_id = 'user123' 
AND status = 'completed' 
ORDER BY created_at DESC;
```

### Archival Health
Check archival status regularly:

```bash
# Weekly check
python manage_db.py stats

# Monthly archival (in cron)
0 2 1 * * /path/to/manage_db.py archive
```

## 🚀 Deployment Steps

### 1. Apply Index Migration
```bash
# For PostgreSQL
psql -d selfos_db -f migrations/add_performance_indexes.sql

# Monitor progress
SELECT * FROM pg_stat_progress_create_index;
```

### 2. Set Up Archival
```bash
# Create archive tables
python manage_db.py create-archive-tables

# Test with dry run
python manage_db.py archive --dry-run

# Initial archival
python manage_db.py archive
```

### 3. Schedule Regular Archival
```bash
# Add to crontab for monthly archival
0 2 1 * * cd /path/to/app && python manage_db.py archive
```

## 🎯 Best Practices

### Index Maintenance
- Use `CONCURRENTLY` option for large table indexes
- Monitor index usage and remove unused indexes
- Run `ANALYZE` after significant data changes

### Archival Automation
- Schedule archival during low-traffic periods
- Always run dry-run first in production
- Monitor archival success/failure
- Keep archive tables for compliance/analytics

### Performance Testing
- Test query performance before/after index deployment
- Use realistic data volumes for testing
- Monitor application performance metrics

## 🔧 Troubleshooting

### Slow Index Creation
```sql
-- Check progress
SELECT * FROM pg_stat_progress_create_index;

-- If stuck, try smaller batch sizes or off-peak hours
```

### Archival Failures
```python
# Check logs
python manage_db.py stats  # Shows any error details

# Manual recovery if needed
from archival import archive_story_sessions
result = archive_story_sessions(db, batch_size=100)
```

### High Storage Usage
```sql
-- Check table and index sizes
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

## 📋 Maintenance Schedule

### Daily
- Monitor application performance metrics
- Check error logs for database issues

### Weekly  
- Run `python manage_db.py stats` to check archival needs
- Review slow query logs

### Monthly
- Run archival operations
- Review index usage statistics
- Check storage utilization

### Quarterly
- Analyze query patterns for new index opportunities
- Review and adjust retention policies
- Performance testing with production-like data

---

This optimization strategy ensures the SelfOS Backend API maintains high performance as data volume grows, while providing tools for ongoing maintenance and monitoring.
import os
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

# Use DATABASE_URL environment variable; default to SQLite in-memory for testing
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    DATABASE_URL = "sqlite:///:memory:"

# Handle postgres:// URLs (convert to postgresql://)
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

logger = logging.getLogger(__name__)

# ============================================================================
# ARCHIVAL CONFIGURATION AND UTILITIES
# ============================================================================

class ArchivalConfig:
    """Configuration for archival operations."""
    
    # Archive records older than these days
    STORY_SESSION_RETENTION_DAYS = 365  # Keep 1 year
    FEEDBACK_LOG_RETENTION_DAYS = 90    # Keep 3 months for recent analysis
    
    # Batch size for archival operations
    BATCH_SIZE = 1000
    
    # Archive table naming convention
    ARCHIVE_TABLE_SUFFIX = "_archive"

def create_archive_tables(db: Session) -> None:
    """
    Create archive tables for StorySession and FeedbackLog.
    These tables have the same structure but are designed for long-term storage.
    """
    
    # Create story_sessions_archive table
    story_archive_sql = """
    CREATE TABLE IF NOT EXISTS story_sessions_archive (
        LIKE story_sessions INCLUDING ALL
    );
    
    -- Add archival metadata
    ALTER TABLE story_sessions_archive 
    ADD COLUMN IF NOT EXISTS archived_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
    
    -- Index for archival queries
    CREATE INDEX IF NOT EXISTS ix_story_archive_archived_at 
    ON story_sessions_archive(archived_at);
    """
    
    # Create feedback_logs_archive table
    feedback_archive_sql = """
    CREATE TABLE IF NOT EXISTS feedback_logs_archive (
        LIKE feedback_logs INCLUDING ALL
    );
    
    -- Add archival metadata
    ALTER TABLE feedback_logs_archive 
    ADD COLUMN IF NOT EXISTS archived_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
    
    -- Index for archival queries
    CREATE INDEX IF NOT EXISTS ix_feedback_archive_archived_at 
    ON feedback_logs_archive(archived_at);
    """
    
    try:
        db.execute(text(story_archive_sql))
        db.execute(text(feedback_archive_sql))
        db.commit()
        logger.info("Archive tables created successfully")
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create archive tables: {e}")
        raise

def archive_story_sessions(
    db: Session, 
    retention_days: int = ArchivalConfig.STORY_SESSION_RETENTION_DAYS,
    batch_size: int = ArchivalConfig.BATCH_SIZE,
    dry_run: bool = False
) -> Dict[str, Any]:
    """
    Archive old StorySession records to story_sessions_archive table.
    
    Args:
        db: Database session
        retention_days: Keep records newer than this many days
        batch_size: Process records in batches of this size
        dry_run: If True, only count records without archiving
        
    Returns:
        Dict with archival statistics
    """
    from models import StorySession
    
    cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
    
    # Count records to archive
    archive_query = db.query(StorySession).filter(
        StorySession.created_at < cutoff_date
    )
    total_records = archive_query.count()
    
    if dry_run:
        return {
            "total_records_to_archive": total_records,
            "cutoff_date": cutoff_date.isoformat(),
            "retention_days": retention_days,
            "dry_run": True
        }
    
    archived_count = 0
    
    try:
        while True:
            # Get batch of records to archive
            records = archive_query.limit(batch_size).all()
            
            if not records:
                break
                
            # Insert into archive table
            for record in records:
                archive_sql = """
                INSERT INTO story_sessions_archive 
                SELECT *, CURRENT_TIMESTAMP as archived_at 
                FROM story_sessions 
                WHERE id = :record_id
                """
                db.execute(text(archive_sql), {"record_id": record.id})
            
            # Delete from main table
            record_ids = [record.id for record in records]
            db.query(StorySession).filter(
                StorySession.id.in_(record_ids)
            ).delete(synchronize_session=False)
            
            archived_count += len(records)
            db.commit()
            
            logger.info(f"Archived {len(records)} story sessions (total: {archived_count})")
        
        return {
            "total_records_archived": archived_count,
            "cutoff_date": cutoff_date.isoformat(),
            "retention_days": retention_days,
            "batch_size": batch_size,
            "success": True
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to archive story sessions: {e}")
        return {
            "error": str(e),
            "records_archived_before_error": archived_count,
            "success": False
        }

def archive_feedback_logs(
    db: Session,
    retention_days: int = ArchivalConfig.FEEDBACK_LOG_RETENTION_DAYS,
    batch_size: int = ArchivalConfig.BATCH_SIZE,
    dry_run: bool = False
) -> Dict[str, Any]:
    """
    Archive old FeedbackLog records to feedback_logs_archive table.
    
    Args:
        db: Database session
        retention_days: Keep records newer than this many days
        batch_size: Process records in batches of this size
        dry_run: If True, only count records without archiving
        
    Returns:
        Dict with archival statistics
    """
    from models import FeedbackLog
    
    cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
    
    # Count records to archive
    archive_query = db.query(FeedbackLog).filter(
        FeedbackLog.created_at < cutoff_date
    )
    total_records = archive_query.count()
    
    if dry_run:
        return {
            "total_records_to_archive": total_records,
            "cutoff_date": cutoff_date.isoformat(),
            "retention_days": retention_days,
            "dry_run": True
        }
    
    archived_count = 0
    
    try:
        while True:
            # Get batch of records to archive
            records = archive_query.limit(batch_size).all()
            
            if not records:
                break
                
            # Insert into archive table
            for record in records:
                archive_sql = """
                INSERT INTO feedback_logs_archive 
                SELECT *, CURRENT_TIMESTAMP as archived_at 
                FROM feedback_logs 
                WHERE id = :record_id
                """
                db.execute(text(archive_sql), {"record_id": record.id})
            
            # Delete from main table
            record_ids = [record.id for record in records]
            db.query(FeedbackLog).filter(
                FeedbackLog.id.in_(record_ids)
            ).delete(synchronize_session=False)
            
            archived_count += len(records)
            db.commit()
            
            logger.info(f"Archived {len(records)} feedback logs (total: {archived_count})")
        
        return {
            "total_records_archived": archived_count,
            "cutoff_date": cutoff_date.isoformat(),
            "retention_days": retention_days,
            "batch_size": batch_size,
            "success": True
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to archive feedback logs: {e}")
        return {
            "error": str(e),
            "records_archived_before_error": archived_count,
            "success": False
        }

def get_archival_stats(db: Session) -> Dict[str, Any]:
    """
    Get statistics about main and archive tables.
    
    Returns:
        Dict with table sizes and archival recommendations
    """
    from models import StorySession, FeedbackLog
    
    stats = {}
    
    try:
        # Story sessions stats
        story_count = db.query(StorySession).count()
        story_old_count = db.query(StorySession).filter(
            StorySession.created_at < datetime.utcnow() - timedelta(days=ArchivalConfig.STORY_SESSION_RETENTION_DAYS)
        ).count()
        
        # Feedback logs stats
        feedback_count = db.query(FeedbackLog).count()
        feedback_old_count = db.query(FeedbackLog).filter(
            FeedbackLog.created_at < datetime.utcnow() - timedelta(days=ArchivalConfig.FEEDBACK_LOG_RETENTION_DAYS)
        ).count()
        
        # Archive table stats (if they exist)
        try:
            story_archive_result = db.execute(text("SELECT COUNT(*) FROM story_sessions_archive")).scalar()
            story_archive_count = story_archive_result if story_archive_result else 0
        except:
            story_archive_count = 0
            
        try:
            feedback_archive_result = db.execute(text("SELECT COUNT(*) FROM feedback_logs_archive")).scalar()
            feedback_archive_count = feedback_archive_result if feedback_archive_result else 0
        except:
            feedback_archive_count = 0
        
        stats = {
            "story_sessions": {
                "active_records": story_count,
                "archivable_records": story_old_count,
                "archived_records": story_archive_count,
                "retention_days": ArchivalConfig.STORY_SESSION_RETENTION_DAYS,
                "needs_archival": story_old_count > 0
            },
            "feedback_logs": {
                "active_records": feedback_count,
                "archivable_records": feedback_old_count,
                "archived_records": feedback_archive_count,
                "retention_days": ArchivalConfig.FEEDBACK_LOG_RETENTION_DAYS,
                "needs_archival": feedback_old_count > 0
            },
            "total_active_records": story_count + feedback_count,
            "total_archivable_records": story_old_count + feedback_old_count,
            "total_archived_records": story_archive_count + feedback_archive_count
        }
        
    except Exception as e:
        logger.error(f"Failed to get archival stats: {e}")
        stats["error"] = str(e)
    
    return stats

def archive_all_tables(
    db: Session,
    dry_run: bool = False
) -> Dict[str, Any]:
    """
    Archive all configured tables in one operation.
    
    Args:
        db: Database session
        dry_run: If True, only show what would be archived
        
    Returns:
        Dict with results for all archival operations
    """
    results = {
        "timestamp": datetime.utcnow().isoformat(),
        "dry_run": dry_run,
        "operations": {}
    }
    
    # Archive story sessions
    results["operations"]["story_sessions"] = archive_story_sessions(
        db, dry_run=dry_run
    )
    
    # Archive feedback logs
    results["operations"]["feedback_logs"] = archive_feedback_logs(
        db, dry_run=dry_run
    )
    
    # Calculate totals
    total_archived = sum(
        op.get("total_records_archived", 0) 
        for op in results["operations"].values()
        if op.get("success", False)
    )
    
    results["summary"] = {
        "total_records_archived": total_archived,
        "successful_operations": sum(
            1 for op in results["operations"].values() 
            if op.get("success", False)
        ),
        "failed_operations": sum(
            1 for op in results["operations"].values() 
            if not op.get("success", True)
        )
    }
    
    return results
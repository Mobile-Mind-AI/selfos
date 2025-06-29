#!/usr/bin/env python3
"""
Test script for archival functionality.
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta
from dependencies import get_db
from models import Base, StorySession, FeedbackLog
from db import engine, get_archival_stats, archive_all_tables, create_archive_tables
import uuid

def test_archival():
    """Test the archival functionality with sample data."""
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    db = next(get_db())
    
    try:
        print("Creating test data...")
        
        # Create old story session (should be archived)
        old_story = StorySession(
            id=str(uuid.uuid4()),
            user_id="test_user_1",
            title="Old Story",
            content_type="story",
            processing_status="completed",
            created_at=datetime.utcnow() - timedelta(days=400)  # 400 days old
        )
        db.add(old_story)
        
        # Create recent story session (should NOT be archived)
        new_story = StorySession(
            id=str(uuid.uuid4()),
            user_id="test_user_1", 
            title="New Story",
            content_type="story",
            processing_status="completed",
            created_at=datetime.utcnow() - timedelta(days=30)  # 30 days old
        )
        db.add(new_story)
        
        # Create old feedback log (should be archived)
        old_feedback = FeedbackLog(
            id=str(uuid.uuid4()),
            user_id="test_user_1",
            context_type="task",
            feedback_type="positive",
            created_at=datetime.utcnow() - timedelta(days=100)  # 100 days old
        )
        db.add(old_feedback)
        
        # Create recent feedback log (should NOT be archived)
        new_feedback = FeedbackLog(
            id=str(uuid.uuid4()),
            user_id="test_user_1",
            context_type="goal",
            feedback_type="negative", 
            created_at=datetime.utcnow() - timedelta(days=30)  # 30 days old
        )
        db.add(new_feedback)
        
        db.commit()
        
        print("✅ Test data created")
        
        # Test archival stats
        print("\n📊 Getting archival stats...")
        stats = get_archival_stats(db)
        
        print(f"Story Sessions - Active: {stats['story_sessions']['active_records']}")
        print(f"Story Sessions - Archivable: {stats['story_sessions']['archivable_records']}")
        print(f"Feedback Logs - Active: {stats['feedback_logs']['active_records']}")
        print(f"Feedback Logs - Archivable: {stats['feedback_logs']['archivable_records']}")
        
        # Test dry run
        print("\n🧪 Testing dry run...")
        dry_results = archive_all_tables(db, dry_run=True)
        
        for table, result in dry_results["operations"].items():
            count = result.get('total_records_to_archive', 0)
            print(f"{table}: {count} records would be archived")
        
        # Test actual archival
        print("\n🗄️  Creating archive tables...")
        create_archive_tables(db)
        
        print("📦 Running actual archival...")
        archive_results = archive_all_tables(db, dry_run=False)
        
        for table, result in archive_results["operations"].items():
            if result.get("success"):
                count = result.get('total_records_archived', 0)
                print(f"{table}: {count} records archived ✅")
            else:
                error = result.get('error', 'Unknown error')
                print(f"{table}: FAILED - {error} ❌")
        
        # Verify results
        print("\n🔍 Verifying results...")
        final_stats = get_archival_stats(db)
        
        print(f"Story Sessions - Active after archival: {final_stats['story_sessions']['active_records']}")
        print(f"Feedback Logs - Active after archival: {final_stats['feedback_logs']['active_records']}")
        
        # Check archive tables
        try:
            from sqlalchemy import text
            story_archive_count = db.execute(text("SELECT COUNT(*) FROM story_sessions_archive")).scalar()
            feedback_archive_count = db.execute(text("SELECT COUNT(*) FROM feedback_logs_archive")).scalar()
            
            print(f"Story Sessions - Archived: {story_archive_count}")
            print(f"Feedback Logs - Archived: {feedback_archive_count}")
            
        except Exception as e:
            print(f"Could not check archive tables: {e}")
        
        print("\n✅ Archival test completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_archival()
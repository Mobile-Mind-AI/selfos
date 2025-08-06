#!/usr/bin/env python3
"""Simple test to check if tables are created correctly."""

import sys
import os

# Add the current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Tag, Goal, User
from models.tags import project_tags, goal_tags, task_tags, habit_tags, journal_entry_tags

def test_table_creation():
    """Test if all tables are created correctly."""
    # Create in-memory database
    engine = create_engine("sqlite:///:memory:", echo=True)
    
    # Create all tables
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ All tables created successfully!")
        
        # Check if tables exist
        inspector = engine.dialect.get_table_names(engine.connect())
        print(f"📋 Created tables: {sorted(inspector)}")
        
        # Check if tag associations exist
        association_tables = ["project_tags", "goal_tags", "task_tags", "habit_tags", "journal_entry_tags"]
        missing_tables = [t for t in association_tables if t not in inspector]
        
        if not missing_tables:
            print("✅ All association tables created!")
        else:
            print(f"❌ Missing association tables: {missing_tables}")
        
        return len(missing_tables) == 0
        
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        return False

if __name__ == "__main__":
    success = test_table_creation()
    sys.exit(0 if success else 1)

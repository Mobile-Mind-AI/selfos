#!/usr/bin/env python3
"""
Clean database script for development
Drops all tables and resets Alembic migrations
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text, inspect
import db
import subprocess

def clean_database():
    """Drop all tables and reset database"""
    print("🗑️  Cleaning database...")
    
    inspector = inspect(db.engine)
    existing_tables = inspector.get_table_names()
    
    if not existing_tables:
        print("✅ Database is already clean")
        return
    
    print(f"Found {len(existing_tables)} tables to drop")
    
    with db.engine.begin() as conn:
        # Disable foreign key checks
        conn.execute(text("SET session_replication_role = replica;"))
        
        # Drop all tables
        for table in existing_tables:
            print(f"  Dropping table: {table}")
            conn.execute(text(f'DROP TABLE IF EXISTS "{table}" CASCADE'))
        
        # Re-enable foreign key checks
        conn.execute(text("SET session_replication_role = DEFAULT;"))
    
    print("✅ All tables dropped")
    
    # Reset Alembic
    print("🔄 Resetting Alembic...")
    try:
        subprocess.run(['alembic', 'stamp', 'base'], check=True)
        print("✅ Alembic reset to base")
    except subprocess.CalledProcessError:
        print("⚠️  Could not reset Alembic (this is okay if alembic_version was dropped)")

if __name__ == "__main__":
    response = input("⚠️  This will DELETE ALL DATA in the database. Continue? (yes/no): ")
    if response.lower() == 'yes':
        clean_database()
        print("\n✅ Database cleaned successfully!")
        print("Run 'alembic upgrade head' to recreate tables with migrations")
    else:
        print("❌ Cancelled")
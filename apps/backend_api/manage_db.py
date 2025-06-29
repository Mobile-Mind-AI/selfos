#!/usr/bin/env python3
"""
Database management CLI tool for SelfOS Backend API.

This script provides utilities for database maintenance, archival, and optimization.
"""

import argparse
import sys
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def setup_database():
    """Initialize database connection and imports."""
    try:
        from dependencies import get_db
        from db import (
            create_archive_tables, 
            get_archival_stats, 
            archive_all_tables,
            archive_story_sessions,
            archive_feedback_logs
        )
        return get_db, {
            'create_archive_tables': create_archive_tables,
            'get_archival_stats': get_archival_stats,
            'archive_all_tables': archive_all_tables,
            'archive_story_sessions': archive_story_sessions,
            'archive_feedback_logs': archive_feedback_logs
        }
    except ImportError as e:
        logger.error(f"Failed to import database modules: {e}")
        sys.exit(1)

def cmd_stats(args):
    """Show database and archival statistics."""
    get_db, funcs = setup_database()
    db = next(get_db())
    
    try:
        stats = funcs['get_archival_stats'](db)
        
        print("\n" + "="*60)
        print("DATABASE ARCHIVAL STATISTICS")
        print("="*60)
        
        if "error" in stats:
            print(f"Error getting stats: {stats['error']}")
            return
        
        # Story Sessions
        story = stats['story_sessions']
        print(f"\nSTORY SESSIONS:")
        print(f"  Active Records:     {story['active_records']:,}")
        print(f"  Archivable Records: {story['archivable_records']:,}")
        print(f"  Archived Records:   {story['archived_records']:,}")
        print(f"  Retention Days:     {story['retention_days']}")
        print(f"  Needs Archival:     {'YES' if story['needs_archival'] else 'NO'}")
        
        # Feedback Logs
        feedback = stats['feedback_logs']
        print(f"\nFEEDBACK LOGS:")
        print(f"  Active Records:     {feedback['active_records']:,}")
        print(f"  Archivable Records: {feedback['archivable_records']:,}")
        print(f"  Archived Records:   {feedback['archived_records']:,}")
        print(f"  Retention Days:     {feedback['retention_days']}")
        print(f"  Needs Archival:     {'YES' if feedback['needs_archival'] else 'NO'}")
        
        # Totals
        print(f"\nTOTALS:")
        print(f"  Total Active:       {stats['total_active_records']:,}")
        print(f"  Total Archivable:   {stats['total_archivable_records']:,}")
        print(f"  Total Archived:     {stats['total_archived_records']:,}")
        
        if stats['total_archivable_records'] > 0:
            print(f"\n⚠️  {stats['total_archivable_records']:,} records are ready for archival")
            print("   Run 'python manage_db.py archive --dry-run' to see details")
        else:
            print(f"\n✅ No records need archival at this time")
            
    finally:
        db.close()

def cmd_archive(args):
    """Run archival operations."""
    get_db, funcs = setup_database()
    db = next(get_db())
    
    try:
        if not args.dry_run:
            # Create archive tables if they don't exist
            print("Creating archive tables...")
            funcs['create_archive_tables'](db)
        
        if args.table == 'all':
            # Archive all tables
            print(f"{'[DRY RUN] ' if args.dry_run else ''}Archiving all tables...")
            results = funcs['archive_all_tables'](db, dry_run=args.dry_run)
            
            print(f"\n{'DRY RUN ' if args.dry_run else ''}RESULTS:")
            print(f"Timestamp: {results['timestamp']}")
            
            for table, result in results['operations'].items():
                if args.dry_run:
                    count = result.get('total_records_to_archive', 0)
                    print(f"  {table}: {count:,} records would be archived")
                else:
                    if result.get('success'):
                        count = result.get('total_records_archived', 0)
                        print(f"  {table}: {count:,} records archived ✅")
                    else:
                        error = result.get('error', 'Unknown error')
                        print(f"  {table}: FAILED - {error} ❌")
            
            if not args.dry_run:
                summary = results['summary']
                print(f"\nSUMMARY:")
                print(f"  Total Archived: {summary['total_records_archived']:,}")
                print(f"  Successful:     {summary['successful_operations']}")
                print(f"  Failed:         {summary['failed_operations']}")
        
        elif args.table == 'story_sessions':
            # Archive only story sessions
            print(f"{'[DRY RUN] ' if args.dry_run else ''}Archiving story sessions...")
            result = funcs['archive_story_sessions'](
                db, 
                retention_days=args.retention_days,
                dry_run=args.dry_run
            )
            
            if args.dry_run:
                count = result.get('total_records_to_archive', 0)
                print(f"Would archive {count:,} story sessions")
            else:
                if result.get('success'):
                    count = result.get('total_records_archived', 0)
                    print(f"Archived {count:,} story sessions ✅")
                else:
                    error = result.get('error', 'Unknown error')
                    print(f"Failed to archive story sessions: {error} ❌")
        
        elif args.table == 'feedback_logs':
            # Archive only feedback logs
            print(f"{'[DRY RUN] ' if args.dry_run else ''}Archiving feedback logs...")
            result = funcs['archive_feedback_logs'](
                db,
                retention_days=args.retention_days,
                dry_run=args.dry_run
            )
            
            if args.dry_run:
                count = result.get('total_records_to_archive', 0)
                print(f"Would archive {count:,} feedback logs")
            else:
                if result.get('success'):
                    count = result.get('total_records_archived', 0)
                    print(f"Archived {count:,} feedback logs ✅")
                else:
                    error = result.get('error', 'Unknown error')
                    print(f"Failed to archive feedback logs: {error} ❌")
                    
    finally:
        db.close()

def cmd_create_archive_tables(args):
    """Create archive tables."""
    get_db, funcs = setup_database()
    db = next(get_db())
    
    try:
        print("Creating archive tables...")
        funcs['create_archive_tables'](db)
        print("Archive tables created successfully ✅")
    except Exception as e:
        print(f"Failed to create archive tables: {e} ❌")
    finally:
        db.close()

def cmd_indexes(args):
    """Show information about database indexes."""
    get_db, _ = setup_database()
    db = next(get_db())
    
    try:
        from sqlalchemy import text
        
        # Query to get index information
        index_query = """
        SELECT 
            schemaname,
            tablename,
            indexname,
            idx_scan as scans,
            idx_tup_read as tuples_read,
            idx_tup_fetch as tuples_fetched,
            pg_size_pretty(pg_relation_size(indexrelid)) as size
        FROM pg_stat_user_indexes 
        WHERE schemaname = 'public'
        ORDER BY idx_scan DESC;
        """
        
        result = db.execute(text(index_query))
        indexes = result.fetchall()
        
        print("\n" + "="*80)
        print("DATABASE INDEX USAGE STATISTICS")
        print("="*80)
        print(f"{'Table':<20} {'Index':<30} {'Scans':<10} {'Size':<10}")
        print("-"*80)
        
        for idx in indexes:
            print(f"{idx.tablename:<20} {idx.indexname:<30} {idx.scans:<10} {idx.size:<10}")
        
        if not indexes:
            print("No index statistics available (PostgreSQL only)")
            
    except Exception as e:
        print(f"Error getting index stats: {e}")
        print("Note: Index statistics are only available for PostgreSQL")
    finally:
        db.close()

def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Database management utilities for SelfOS Backend API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s stats                              # Show archival statistics
  %(prog)s archive --dry-run                  # See what would be archived
  %(prog)s archive                            # Archive old records
  %(prog)s archive --table story_sessions     # Archive only story sessions
  %(prog)s archive --retention-days 30        # Custom retention period
  %(prog)s create-archive-tables              # Create archive tables
  %(prog)s indexes                            # Show index usage stats
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Stats command
    stats_parser = subparsers.add_parser('stats', help='Show database statistics')
    stats_parser.set_defaults(func=cmd_stats)
    
    # Archive command
    archive_parser = subparsers.add_parser('archive', help='Archive old records')
    archive_parser.add_argument(
        '--dry-run', 
        action='store_true',
        help='Show what would be archived without actually doing it'
    )
    archive_parser.add_argument(
        '--table',
        choices=['all', 'story_sessions', 'feedback_logs'],
        default='all',
        help='Which table(s) to archive (default: all)'
    )
    archive_parser.add_argument(
        '--retention-days',
        type=int,
        help='Custom retention period in days (overrides defaults)'
    )
    archive_parser.set_defaults(func=cmd_archive)
    
    # Create archive tables command
    create_parser = subparsers.add_parser(
        'create-archive-tables', 
        help='Create archive tables'
    )
    create_parser.set_defaults(func=cmd_create_archive_tables)
    
    # Indexes command  
    indexes_parser = subparsers.add_parser('indexes', help='Show index usage statistics')
    indexes_parser.set_defaults(func=cmd_indexes)
    
    # Parse arguments
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Run the selected command
    try:
        args.func(args)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Command failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
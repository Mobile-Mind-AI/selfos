"""Journal entry service - business logic for journal/notes functionality."""

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, desc, or_
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from models import JournalEntry, User, Project, Goal, Task
from schemas import JournalEntryCreate, JournalEntryUpdate


class JournalService:
    """Service class for managing journal entries"""
    
    @staticmethod
    def create_entry(db: Session, user_id: str, entry_data: JournalEntryCreate) -> JournalEntry:
        """
        Create a new journal entry
        
        Args:
            db: Database session
            user_id: ID of the user creating the entry
            entry_data: Journal entry creation data
            
        Returns:
            Created JournalEntry object
            
        Raises:
            ValueError: If referenced project/goal/task doesn't exist or doesn't belong to user
        """
        # Validate that referenced entities exist and belong to user
        if entry_data.project_id:
            project = db.query(Project).filter(
                and_(Project.id == entry_data.project_id, Project.user_id == user_id)
            ).first()
            if not project:
                raise ValueError(f"Project with id {entry_data.project_id} not found or access denied")
                
        if entry_data.goal_id:
            goal = db.query(Goal).filter(
                and_(Goal.id == entry_data.goal_id, Goal.user_id == user_id)
            ).first()
            if not goal:
                raise ValueError(f"Goal with id {entry_data.goal_id} not found or access denied")
                
        if entry_data.task_id:
            task = db.query(Task).filter(
                and_(Task.id == entry_data.task_id, Task.user_id == user_id)
            ).first()
            if not task:
                raise ValueError(f"Task with id {entry_data.task_id} not found or access denied")
        
        # Create the journal entry
        db_entry = JournalEntry(
            user_id=user_id,
            content=entry_data.content,
            project_id=entry_data.project_id,
            goal_id=entry_data.goal_id,
            task_id=entry_data.task_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(db_entry)
        db.commit()
        db.refresh(db_entry)
        
        return db_entry
    
    @staticmethod
    def get_entry(db: Session, user_id: str, entry_id: int) -> Optional[JournalEntry]:
        """
        Get a specific journal entry by ID
        
        Args:
            db: Database session
            user_id: ID of the user requesting the entry
            entry_id: ID of the journal entry
            
        Returns:
            JournalEntry object if found and accessible, None otherwise
        """
        return db.query(JournalEntry).options(
            joinedload(JournalEntry.project),
            joinedload(JournalEntry.goal),
            joinedload(JournalEntry.task)
        ).filter(
            and_(JournalEntry.id == entry_id, JournalEntry.user_id == user_id)
        ).first()
    
    @staticmethod
    def get_entries(
        db: Session, 
        user_id: str, 
        project_id: Optional[int] = None,
        goal_id: Optional[int] = None,
        task_id: Optional[int] = None,
        limit: int = 50,
        offset: int = 0,
        search_content: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[JournalEntry]:
        """
        Get journal entries with filtering options
        
        Args:
            db: Database session
            user_id: ID of the user requesting entries
            project_id: Filter by project ID
            goal_id: Filter by goal ID  
            task_id: Filter by task ID
            limit: Maximum number of entries to return (max 100)
            offset: Number of entries to skip
            search_content: Search term to filter content
            start_date: Filter entries created after this date
            end_date: Filter entries created before this date
            
        Returns:
            List of JournalEntry objects
        """
        # Enforce reasonable limits
        limit = min(limit, 100)
        offset = max(offset, 0)
        
        query = db.query(JournalEntry).options(
            joinedload(JournalEntry.project),
            joinedload(JournalEntry.goal),
            joinedload(JournalEntry.task)
        ).filter(JournalEntry.user_id == user_id)
        
        # Apply filters
        if project_id:
            query = query.filter(JournalEntry.project_id == project_id)
        if goal_id:
            query = query.filter(JournalEntry.goal_id == goal_id)
        if task_id:
            query = query.filter(JournalEntry.task_id == task_id)
            
        if search_content:
            # Case-insensitive content search
            query = query.filter(JournalEntry.content.ilike(f"%{search_content}%"))
            
        if start_date:
            query = query.filter(JournalEntry.created_at >= start_date)
        if end_date:
            query = query.filter(JournalEntry.created_at <= end_date)
        
        # Order by most recent first
        query = query.order_by(desc(JournalEntry.created_at))
        
        return query.offset(offset).limit(limit).all()
    
    @staticmethod
    def get_entries_for_parent(
        db: Session, 
        user_id: str, 
        parent_type: str, 
        parent_id: int
    ) -> List[JournalEntry]:
        """
        Get all journal entries associated with a specific parent entity
        
        Args:
            db: Database session
            user_id: ID of the user requesting entries
            parent_type: Type of parent ('project', 'goal', or 'task')
            parent_id: ID of the parent entity
            
        Returns:
            List of JournalEntry objects associated with the parent
            
        Raises:
            ValueError: If parent_type is invalid
        """
        query = db.query(JournalEntry).filter(JournalEntry.user_id == user_id)
        
        if parent_type == 'project':
            query = query.filter(JournalEntry.project_id == parent_id)
        elif parent_type == 'goal':
            query = query.filter(JournalEntry.goal_id == parent_id)
        elif parent_type == 'task':
            query = query.filter(JournalEntry.task_id == parent_id)
        else:
            raise ValueError(f"Invalid parent_type: {parent_type}. Must be 'project', 'goal', or 'task'")
        
        return query.options(
            joinedload(JournalEntry.project),
            joinedload(JournalEntry.goal),
            joinedload(JournalEntry.task)
        ).order_by(desc(JournalEntry.created_at)).all()
    
    @staticmethod
    def update_entry(
        db: Session, 
        user_id: str, 
        entry_id: int, 
        entry_data: JournalEntryUpdate
    ) -> Optional[JournalEntry]:
        """
        Update a journal entry
        
        Args:
            db: Database session
            user_id: ID of the user updating the entry
            entry_id: ID of the journal entry to update
            entry_data: Updated entry data
            
        Returns:
            Updated JournalEntry object if found and accessible, None otherwise
        """
        entry = db.query(JournalEntry).filter(
            and_(JournalEntry.id == entry_id, JournalEntry.user_id == user_id)
        ).first()
        
        if not entry:
            return None
        
        # Update fields that were provided
        if entry_data.content is not None:
            entry.content = entry_data.content
        
        entry.updated_at = datetime.utcnow()
        entry.version += 1  # Increment version for sync
        
        db.commit()
        db.refresh(entry)
        
        return entry
    
    @staticmethod
    def delete_entry(db: Session, user_id: str, entry_id: int) -> bool:
        """
        Delete a journal entry
        
        Args:
            db: Database session
            user_id: ID of the user deleting the entry
            entry_id: ID of the journal entry to delete
            
        Returns:
            True if entry was found and deleted, False otherwise
        """
        entry = db.query(JournalEntry).filter(
            and_(JournalEntry.id == entry_id, JournalEntry.user_id == user_id)
        ).first()
        
        if not entry:
            return False
        
        db.delete(entry)
        db.commit()
        
        return True
    
    @staticmethod
    def get_entry_count(
        db: Session, 
        user_id: str,
        project_id: Optional[int] = None,
        goal_id: Optional[int] = None,
        task_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> int:
        """
        Get count of journal entries with optional filtering
        
        Args:
            db: Database session
            user_id: ID of the user
            project_id: Filter by project ID
            goal_id: Filter by goal ID
            task_id: Filter by task ID
            start_date: Filter entries created after this date
            end_date: Filter entries created before this date
            
        Returns:
            Count of matching journal entries
        """
        query = db.query(JournalEntry).filter(JournalEntry.user_id == user_id)
        
        # Apply the same filters as get_entries
        if project_id:
            query = query.filter(JournalEntry.project_id == project_id)
        if goal_id:
            query = query.filter(JournalEntry.goal_id == goal_id)
        if task_id:
            query = query.filter(JournalEntry.task_id == task_id)
        if start_date:
            query = query.filter(JournalEntry.created_at >= start_date)
        if end_date:
            query = query.filter(JournalEntry.created_at <= end_date)
        
        return query.count()
    
    @staticmethod
    def get_recent_entries(db: Session, user_id: str, days: int = 7, limit: int = 10) -> List[JournalEntry]:
        """
        Get recent journal entries for a user
        
        Args:
            db: Database session
            user_id: ID of the user
            days: Number of days to look back (default 7)
            limit: Maximum number of entries to return (default 10)
            
        Returns:
            List of recent JournalEntry objects
        """
        start_date = datetime.utcnow() - timedelta(days=days)
        
        return db.query(JournalEntry).options(
            joinedload(JournalEntry.project),
            joinedload(JournalEntry.goal),
            joinedload(JournalEntry.task)
        ).filter(
            and_(
                JournalEntry.user_id == user_id,
                JournalEntry.created_at >= start_date
            )
        ).order_by(desc(JournalEntry.created_at)).limit(limit).all()
    
    @staticmethod
    def search_entries(
        db: Session, 
        user_id: str, 
        search_term: str,
        limit: int = 20
    ) -> List[JournalEntry]:
        """
        Search journal entries by content
        
        Args:
            db: Database session
            user_id: ID of the user
            search_term: Term to search for in content
            limit: Maximum number of results (default 20)
            
        Returns:
            List of matching JournalEntry objects
        """
        return db.query(JournalEntry).options(
            joinedload(JournalEntry.project),
            joinedload(JournalEntry.goal),
            joinedload(JournalEntry.task)
        ).filter(
            and_(
                JournalEntry.user_id == user_id,
                JournalEntry.content.ilike(f"%{search_term}%")
            )
        ).order_by(desc(JournalEntry.created_at)).limit(limit).all()
    
    @staticmethod
    def get_entry_statistics(db: Session, user_id: str) -> Dict[str, Any]:
        """
        Get statistics about user's journal entries
        
        Args:
            db: Database session
            user_id: ID of the user
            
        Returns:
            Dictionary with entry statistics
        """
        from sqlalchemy import func
        
        # Basic counts
        total_entries = db.query(JournalEntry).filter(JournalEntry.user_id == user_id).count()
        
        # Entries by association type
        with_project = db.query(JournalEntry).filter(
            and_(JournalEntry.user_id == user_id, JournalEntry.project_id.isnot(None))
        ).count()
        
        with_goal = db.query(JournalEntry).filter(
            and_(JournalEntry.user_id == user_id, JournalEntry.goal_id.isnot(None))
        ).count()
        
        with_task = db.query(JournalEntry).filter(
            and_(JournalEntry.user_id == user_id, JournalEntry.task_id.isnot(None))
        ).count()
        
        standalone = total_entries - with_project - with_goal - with_task
        
        # Recent activity (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_entries = db.query(JournalEntry).filter(
            and_(
                JournalEntry.user_id == user_id,
                JournalEntry.created_at >= thirty_days_ago
            )
        ).count()
        
        # Average content length
        avg_length_result = db.query(func.avg(func.length(JournalEntry.content))).filter(
            JournalEntry.user_id == user_id
        ).scalar()
        avg_content_length = round(avg_length_result, 1) if avg_length_result else 0
        
        # Oldest and newest entries
        oldest_entry = db.query(JournalEntry.created_at).filter(
            JournalEntry.user_id == user_id
        ).order_by(JournalEntry.created_at).first()
        
        newest_entry = db.query(JournalEntry.created_at).filter(
            JournalEntry.user_id == user_id
        ).order_by(desc(JournalEntry.created_at)).first()
        
        return {
            "total_entries": total_entries,
            "entries_with_project": with_project,
            "entries_with_goal": with_goal,
            "entries_with_task": with_task,
            "standalone_entries": standalone,
            "recent_entries_30d": recent_entries,
            "average_content_length": avg_content_length,
            "oldest_entry_date": oldest_entry[0] if oldest_entry else None,
            "newest_entry_date": newest_entry[0] if newest_entry else None
        }


# Export service instance
journal_service = JournalService

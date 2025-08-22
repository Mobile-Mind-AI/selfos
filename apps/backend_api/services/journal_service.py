"""Service for managing journal entries and personal reflections."""

from datetime import datetime, timedelta
from typing import Any

import models
import schemas
from sqlalchemy import and_, desc, func, or_
from sqlalchemy.orm import Session


class JournalService:
    """Service class for journal entry management operations."""

    @staticmethod
    def create_entry(
        db: Session, user_id: str, entry_data: schemas.JournalEntryCreate
    ) -> models.JournalEntry:
        """Create a new journal entry for a user."""
        # Validate project exists if provided
        project_id = getattr(entry_data, "project_id", None)
        if project_id:
            project = (
                db.query(models.Project)
                .filter(
                    models.Project.id == project_id, models.Project.user_id == user_id
                )
                .first()
            )
            if not project:
                raise ValueError(f"Project {project_id} not found")

        # Map schema fields to model fields
        db_entry = models.JournalEntry(
            user_id=user_id,
            content=entry_data.content,
            entry_type="reflection",  # Default type
            entry_date=datetime.utcnow(),
            is_private=True,  # Default to private
            version=1,
            # Add the new relationship fields
            project_id=project_id,
            goal_id=getattr(entry_data, "goal_id", None),
            task_id=getattr(entry_data, "task_id", None),
        )

        db.add(db_entry)
        db.commit()
        db.refresh(db_entry)
        return db_entry

    @staticmethod
    def get_entries(
        db: Session,
        user_id: str,
        project_id: int | None = None,
        goal_id: int | None = None,
        task_id: int | None = None,
        limit: int = 50,
        offset: int = 0,
        search_content: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> list[models.JournalEntry]:
        """Get journal entries with optional filtering."""
        query = db.query(models.JournalEntry).filter(
            models.JournalEntry.user_id == user_id
        )

        # Filter by related entities
        if project_id:
            query = query.filter(models.JournalEntry.project_id == project_id)
        if goal_id:
            query = query.filter(models.JournalEntry.goal_id == goal_id)
        if task_id:
            query = query.filter(models.JournalEntry.task_id == task_id)

        if search_content:
            query = query.filter(
                or_(
                    models.JournalEntry.content.ilike(f"%{search_content}%"),
                    models.JournalEntry.title.ilike(f"%{search_content}%"),
                )
            )

        if start_date:
            query = query.filter(models.JournalEntry.entry_date >= start_date)

        if end_date:
            query = query.filter(models.JournalEntry.entry_date <= end_date)

        return (
            query.order_by(desc(models.JournalEntry.entry_date))
            .offset(offset)
            .limit(limit)
            .all()
        )

    @staticmethod
    def get_entry_count(
        db: Session,
        user_id: str,
        project_id: int | None = None,
        goal_id: int | None = None,
        task_id: int | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> int:
        """Get count of journal entries with optional filtering."""
        query = db.query(func.count(models.JournalEntry.id)).filter(
            models.JournalEntry.user_id == user_id
        )

        # Filter by related entities
        if project_id:
            query = query.filter(models.JournalEntry.project_id == project_id)
        if goal_id:
            query = query.filter(models.JournalEntry.goal_id == goal_id)
        if task_id:
            query = query.filter(models.JournalEntry.task_id == task_id)

        if start_date:
            query = query.filter(models.JournalEntry.entry_date >= start_date)

        if end_date:
            query = query.filter(models.JournalEntry.entry_date <= end_date)

        return query.scalar() or 0

    @staticmethod
    def get_recent_entries(
        db: Session, user_id: str, days: int = 7, limit: int = 10
    ) -> list[models.JournalEntry]:
        """Get recent journal entries from the specified number of days."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        return (
            db.query(models.JournalEntry)
            .filter(
                and_(
                    models.JournalEntry.user_id == user_id,
                    models.JournalEntry.entry_date >= cutoff_date,
                )
            )
            .order_by(desc(models.JournalEntry.entry_date))
            .limit(limit)
            .all()
        )

    @staticmethod
    def search_entries(
        db: Session, user_id: str, search_term: str, limit: int = 20
    ) -> list[models.JournalEntry]:
        """Search journal entries by content."""
        return (
            db.query(models.JournalEntry)
            .filter(
                and_(
                    models.JournalEntry.user_id == user_id,
                    or_(
                        models.JournalEntry.content.ilike(f"%{search_term}%"),
                        models.JournalEntry.title.ilike(f"%{search_term}%"),
                    ),
                )
            )
            .order_by(desc(models.JournalEntry.entry_date))
            .limit(limit)
            .all()
        )

    @staticmethod
    def get_entry_statistics(db: Session, user_id: str) -> dict[str, Any]:
        """Get statistics about user's journal entries."""
        # Total entries
        total_entries = (
            db.query(func.count(models.JournalEntry.id))
            .filter(models.JournalEntry.user_id == user_id)
            .scalar()
            or 0
        )

        # Entries this month
        current_month_start = datetime.utcnow().replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )
        this_month = (
            db.query(func.count(models.JournalEntry.id))
            .filter(
                and_(
                    models.JournalEntry.user_id == user_id,
                    models.JournalEntry.entry_date >= current_month_start,
                )
            )
            .scalar()
            or 0
        )

        # Entries by type
        entries_by_type = (
            db.query(models.JournalEntry.entry_type, func.count(models.JournalEntry.id))
            .filter(models.JournalEntry.user_id == user_id)
            .group_by(models.JournalEntry.entry_type)
            .all()
        )

        # Average entries per week (last 4 weeks)
        four_weeks_ago = datetime.utcnow() - timedelta(weeks=4)
        recent_entries = (
            db.query(func.count(models.JournalEntry.id))
            .filter(
                and_(
                    models.JournalEntry.user_id == user_id,
                    models.JournalEntry.entry_date >= four_weeks_ago,
                )
            )
            .scalar()
            or 0
        )

        # Entries in last 30 days
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_30d = (
            db.query(func.count(models.JournalEntry.id))
            .filter(
                and_(
                    models.JournalEntry.user_id == user_id,
                    models.JournalEntry.entry_date >= thirty_days_ago,
                )
            )
            .scalar()
            or 0
        )

        # First and last entry dates
        first_entry = (
            db.query(models.JournalEntry.entry_date)
            .filter(models.JournalEntry.user_id == user_id)
            .order_by(models.JournalEntry.entry_date)
            .first()
        )

        last_entry = (
            db.query(models.JournalEntry.entry_date)
            .filter(models.JournalEntry.user_id == user_id)
            .order_by(desc(models.JournalEntry.entry_date))
            .first()
        )

        # Count entries with associations
        entries_with_project = (
            db.query(func.count(models.JournalEntry.id))
            .filter(
                and_(
                    models.JournalEntry.user_id == user_id,
                    models.JournalEntry.project_id.isnot(None),
                )
            )
            .scalar()
            or 0
        )

        entries_with_goal = (
            db.query(func.count(models.JournalEntry.id))
            .filter(
                and_(
                    models.JournalEntry.user_id == user_id,
                    models.JournalEntry.goal_id.isnot(None),
                )
            )
            .scalar()
            or 0
        )

        entries_with_task = (
            db.query(func.count(models.JournalEntry.id))
            .filter(
                and_(
                    models.JournalEntry.user_id == user_id,
                    models.JournalEntry.task_id.isnot(None),
                )
            )
            .scalar()
            or 0
        )

        # Count standalone entries (no associations)
        standalone_entries = (
            db.query(func.count(models.JournalEntry.id))
            .filter(
                and_(
                    models.JournalEntry.user_id == user_id,
                    models.JournalEntry.project_id.is_(None),
                    models.JournalEntry.goal_id.is_(None),
                    models.JournalEntry.task_id.is_(None),
                )
            )
            .scalar()
            or 0
        )

        # Calculate average content length
        avg_length = (
            db.query(func.avg(func.length(models.JournalEntry.content)))
            .filter(models.JournalEntry.user_id == user_id)
            .scalar()
        )
        average_content_length = round(avg_length, 1) if avg_length else 0

        return {
            "total_entries": total_entries,
            "entries_this_month": this_month,
            "entries_by_type": dict(entries_by_type),
            "average_per_week": (
                round(recent_entries / 4, 1) if recent_entries > 0 else 0
            ),
            "recent_entries_30d": recent_30d,
            "average_content_length": average_content_length,
            "first_entry_date": first_entry[0] if first_entry else None,
            "last_entry_date": last_entry[0] if last_entry else None,
            "days_since_last_entry": (
                (datetime.utcnow() - last_entry[0]).days if last_entry else None
            ),
            "entries_with_project": entries_with_project,
            "entries_with_goal": entries_with_goal,
            "entries_with_task": entries_with_task,
            "standalone_entries": standalone_entries,
        }

    @staticmethod
    def get_entries_for_parent(
        db: Session, user_id: str, parent_type: str, parent_id: int
    ) -> list[models.JournalEntry]:
        """Get all journal entries associated with a specific parent entity."""

        if parent_type not in ["project", "goal", "task"]:
            raise ValueError("parent_type must be 'project', 'goal', or 'task'")

        query = db.query(models.JournalEntry).filter(
            models.JournalEntry.user_id == user_id
        )

        if parent_type == "project":
            query = query.filter(models.JournalEntry.project_id == parent_id)
        elif parent_type == "goal":
            query = query.filter(models.JournalEntry.goal_id == parent_id)
        elif parent_type == "task":
            query = query.filter(models.JournalEntry.task_id == parent_id)

        return query.order_by(desc(models.JournalEntry.entry_date)).all()

    @staticmethod
    def get_entry(
        db: Session, user_id: str, entry_id: int
    ) -> models.JournalEntry | None:
        """Get a specific journal entry by ID."""
        return (
            db.query(models.JournalEntry)
            .filter(
                and_(
                    models.JournalEntry.id == entry_id,
                    models.JournalEntry.user_id == user_id,
                )
            )
            .first()
        )

    @staticmethod
    def update_entry(
        db: Session, user_id: str, entry_id: int, entry_data: schemas.JournalEntryUpdate
    ) -> models.JournalEntry | None:
        """Update an existing journal entry."""
        db_entry = JournalService.get_entry(db, user_id, entry_id)
        if not db_entry:
            return None

        # Update fields that are provided
        update_data = entry_data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            if hasattr(db_entry, field):
                setattr(db_entry, field, value)

        db_entry.updated_at = datetime.utcnow()
        db_entry.version += 1

        db.commit()
        db.refresh(db_entry)
        return db_entry

    @staticmethod
    def delete_entry(db: Session, user_id: str, entry_id: int) -> bool:
        """Delete a journal entry."""
        db_entry = JournalService.get_entry(db, user_id, entry_id)
        if not db_entry:
            return False

        db.delete(db_entry)
        db.commit()
        return True


# Export service instance
journal_service = JournalService()

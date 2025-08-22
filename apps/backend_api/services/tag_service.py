"""Service layer for tag management and operations."""

import logging
from datetime import datetime
from typing import Any

from models.goals import Goal
from models.habits import Habit
from models.journal import JournalEntry
from models.projects import Project
from models.tags import Tag
from models.tasks import Task
from schemas import TagCreate, TagOut, TagUpdate
from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class TagService:
    """Service for managing tags and their associations."""

    def __init__(self, db: Session, current_user: dict[str, Any]):
        self.db = db
        self.current_user = current_user
        self.user_id = current_user["uid"]

    def create_tag(self, tag_data: TagCreate) -> Tag:
        """Create a new tag for the current user."""
        try:
            # Check if tag name already exists for this user
            existing_tag = (
                self.db.query(Tag)
                .filter(Tag.user_id == self.user_id, Tag.name == tag_data.name)
                .first()
            )

            if existing_tag:
                raise ValueError(f"Tag with name '{tag_data.name}' already exists")

            # Create new tag
            db_tag = Tag(
                user_id=self.user_id,
                name=tag_data.name,
                color=tag_data.color,
                version=1,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )

            self.db.add(db_tag)
            self.db.commit()
            self.db.refresh(db_tag)

            logger.info(f"Created tag {db_tag.id} for user {self.user_id}")
            return db_tag

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating tag for user {self.user_id}: {e}")
            raise

    def get_tags(self, include_usage_count: bool = False) -> list[TagOut]:
        """Get all tags for the current user."""
        try:
            query = self.db.query(Tag).filter(Tag.user_id == self.user_id)
            tags = query.all()

            result = []
            for tag in tags:
                tag_dict = {
                    "id": tag.id,
                    "user_id": tag.user_id,
                    "name": tag.name,
                    "color": tag.color,
                    "version": tag.version,
                    "created_at": tag.created_at,
                    "updated_at": tag.updated_at,
                }

                if include_usage_count:
                    usage_count = self._get_tag_usage_count(tag.id)
                    tag_dict["usage_count"] = usage_count

                result.append(TagOut(**tag_dict))

            return result

        except Exception as e:
            logger.error(f"Error fetching tags for user {self.user_id}: {e}")
            raise

    def search_tags(self, query: str, limit: int) -> list[TagOut]:
        """Search tags by name."""
        try:
            db_tags = (
                self.db.query(Tag)
                .filter(Tag.user_id == self.user_id, Tag.name.ilike(f"%{query}%"))
                .limit(limit)
                .all()
            )

            result = []
            for tag in db_tags:
                usage_count = self._get_tag_usage_count(tag.id)
                tag_dict = {
                    "id": tag.id,
                    "user_id": tag.user_id,
                    "name": tag.name,
                    "color": tag.color,
                    "version": tag.version,
                    "created_at": tag.created_at,
                    "updated_at": tag.updated_at,
                    "usage_count": usage_count,
                }
                result.append(TagOut(**tag_dict))

            return result

        except Exception as e:
            logger.error(f"Error searching tags for user {self.user_id}: {e}")
            raise

    def get_tag_statistics(self) -> dict[str, Any]:
        """Get tag usage statistics."""
        try:
            # Get total number of tags
            total_tags = self.db.query(Tag).filter(Tag.user_id == self.user_id).count()

            # Get usage statistics by entity type
            stats = {
                "total_tags": total_tags,
                "usage_by_entity_type": {},
                "most_used_tags": [],
                "unused_tags_count": 0,
            }

            # Count usage by entity type
            for entity_type, model_class, association_table in [
                ("projects", Project, "project_tags"),
                ("goals", Goal, "goal_tags"),
                ("tasks", Task, "task_tags"),
                ("habits", Habit, "habit_tags"),
                ("journal_entries", JournalEntry, "journal_entry_tags"),
            ]:
                # Use raw SQL to count associations
                count_query = text(
                    f"""
                    SELECT COUNT(DISTINCT t.id)
                    FROM tags t
                    JOIN {association_table} at ON t.id = at.tag_id
                    WHERE t.user_id = :user_id
                """
                )
                count = (
                    self.db.execute(count_query, {"user_id": self.user_id}).scalar()
                    or 0
                )
                stats["usage_by_entity_type"][entity_type] = count

            # Get most used tags (top 5)
            most_used_query = text(
                """
                SELECT t.id, t.name, 
                       (SELECT COUNT(*) FROM project_tags WHERE tag_id = t.id) +
                       (SELECT COUNT(*) FROM goal_tags WHERE tag_id = t.id) +
                       (SELECT COUNT(*) FROM task_tags WHERE tag_id = t.id) +
                       (SELECT COUNT(*) FROM habit_tags WHERE tag_id = t.id) +
                       (SELECT COUNT(*) FROM journal_entry_tags WHERE tag_id = t.id) as usage_count
                FROM tags t
                WHERE t.user_id = :user_id
                ORDER BY usage_count DESC
                LIMIT 5
            """
            )
            most_used_results = self.db.execute(
                most_used_query, {"user_id": self.user_id}
            ).fetchall()

            stats["most_used_tags"] = [
                {"id": row[0], "name": row[1], "usage_count": row[2]}
                for row in most_used_results
            ]

            # Count unused tags
            unused_query = text(
                """
                SELECT COUNT(*)
                FROM tags t
                WHERE t.user_id = :user_id
                AND NOT EXISTS (SELECT 1 FROM project_tags WHERE tag_id = t.id)
                AND NOT EXISTS (SELECT 1 FROM goal_tags WHERE tag_id = t.id)
                AND NOT EXISTS (SELECT 1 FROM task_tags WHERE tag_id = t.id)
                AND NOT EXISTS (SELECT 1 FROM habit_tags WHERE tag_id = t.id)
                AND NOT EXISTS (SELECT 1 FROM journal_entry_tags WHERE tag_id = t.id)
            """
            )
            unused_count = (
                self.db.execute(unused_query, {"user_id": self.user_id}).scalar() or 0
            )
            stats["unused_tags_count"] = unused_count

            return stats

        except Exception as e:
            logger.error(f"Error getting tag statistics for user {self.user_id}: {e}")
            raise

    def get_tag_by_id(
        self, tag_id: int, include_usage_count: bool = False
    ) -> TagOut | None:
        """Get a specific tag by ID."""
        try:
            tag = (
                self.db.query(Tag)
                .filter(Tag.id == tag_id, Tag.user_id == self.user_id)
                .first()
            )

            if not tag:
                return None

            tag_dict = {
                "id": tag.id,
                "user_id": tag.user_id,
                "name": tag.name,
                "color": tag.color,
                "version": tag.version,
                "created_at": tag.created_at,
                "updated_at": tag.updated_at,
            }

            if include_usage_count:
                usage_count = self._get_tag_usage_count(tag.id)
                tag_dict["usage_count"] = usage_count

            return TagOut(**tag_dict)

        except Exception as e:
            logger.error(f"Error fetching tag {tag_id} for user {self.user_id}: {e}")
            raise

    def update_tag(self, tag_id: int, tag_update: TagUpdate) -> Tag | None:
        """Update an existing tag."""
        try:
            tag = (
                self.db.query(Tag)
                .filter(Tag.id == tag_id, Tag.user_id == self.user_id)
                .first()
            )

            if not tag:
                return None

            # Check if new name conflicts with existing tags
            if tag_update.name and tag_update.name != tag.name:
                existing_tag = (
                    self.db.query(Tag)
                    .filter(
                        Tag.user_id == self.user_id,
                        Tag.name == tag_update.name,
                        Tag.id != tag_id,
                    )
                    .first()
                )

                if existing_tag:
                    raise ValueError(
                        f"Tag with name '{tag_update.name}' already exists"
                    )

            # Update fields
            update_data = tag_update.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(tag, field, value)

            tag.updated_at = datetime.utcnow()
            tag.version += 1

            self.db.commit()
            self.db.refresh(tag)

            logger.info(f"Updated tag {tag_id} for user {self.user_id}")
            return tag

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating tag {tag_id} for user {self.user_id}: {e}")
            raise

    def delete_tag(self, tag_id: int) -> bool:
        """Delete a tag and all its associations."""
        try:
            tag = (
                self.db.query(Tag)
                .filter(Tag.id == tag_id, Tag.user_id == self.user_id)
                .first()
            )

            if not tag:
                return False

            # SQLAlchemy will handle cascade deletions for association tables
            self.db.delete(tag)
            self.db.commit()

            logger.info(f"Deleted tag {tag_id} for user {self.user_id}")
            return True

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting tag {tag_id} for user {self.user_id}: {e}")
            raise

    def get_entities_by_tag(
        self, tag_id: int, entity_types: list[str] | None = None
    ) -> dict[str, list[dict]]:
        """Get all entities associated with a specific tag."""
        try:
            tag = (
                self.db.query(Tag)
                .filter(Tag.id == tag_id, Tag.user_id == self.user_id)
                .first()
            )

            if not tag:
                return {}

            # Default to all entity types if none specified
            if entity_types is None:
                entity_types = [
                    "projects",
                    "goals",
                    "tasks",
                    "habits",
                    "journal_entries",
                ]

            result = {}

            for entity_type in entity_types:
                if entity_type == "projects":
                    entities = [
                        {
                            "id": project.id,
                            "title": project.title,
                            "status": project.status,
                            "progress": project.progress,
                            "created_at": project.created_at.isoformat(),
                        }
                        for project in tag.projects
                    ]
                    result["projects"] = entities

                elif entity_type == "goals":
                    entities = [
                        {
                            "id": goal.id,
                            "title": goal.title,
                            "status": goal.status,
                            "progress": goal.progress,
                            "created_at": goal.created_at.isoformat(),
                        }
                        for goal in tag.goals
                    ]
                    result["goals"] = entities

                elif entity_type == "tasks":
                    entities = [
                        {
                            "id": task.id,
                            "title": task.title,
                            "status": task.status,
                            "progress": task.progress,
                            "due_date": (
                                task.due_date.isoformat() if task.due_date else None
                            ),
                            "created_at": task.created_at.isoformat(),
                        }
                        for task in tag.tasks
                    ]
                    result["tasks"] = entities

                elif entity_type == "habits":
                    entities = [
                        {
                            "id": habit.id,
                            "title": habit.title,
                            "is_active": habit.is_active,
                            "current_streak": habit.current_streak,
                            "created_at": habit.created_at.isoformat(),
                        }
                        for habit in tag.habits
                    ]
                    result["habits"] = entities

                elif entity_type == "journal_entries":
                    entities = [
                        {
                            "id": entry.id,
                            "content": (
                                entry.content[:100] + "..."
                                if len(entry.content) > 100
                                else entry.content
                            ),
                            "created_at": entry.created_at.isoformat(),
                        }
                        for entry in tag.journal_entries
                    ]
                    result["journal_entries"] = entities

            return result

        except Exception as e:
            logger.error(
                f"Error fetching entities for tag {tag_id} for user {self.user_id}: {e}"
            )
            raise

    def _get_tag_usage_count(self, tag_id: int) -> int:
        """Get total usage count for a tag across all entity types."""
        try:
            usage_query = text(
                """
                SELECT 
                    (SELECT COUNT(*) FROM project_tags WHERE tag_id = :tag_id) +
                    (SELECT COUNT(*) FROM goal_tags WHERE tag_id = :tag_id) +
                    (SELECT COUNT(*) FROM task_tags WHERE tag_id = :tag_id) +
                    (SELECT COUNT(*) FROM habit_tags WHERE tag_id = :tag_id) +
                    (SELECT COUNT(*) FROM journal_entry_tags WHERE tag_id = :tag_id) as total_usage
            """
            )
            result = self.db.execute(usage_query, {"tag_id": tag_id}).scalar()
            return result or 0

        except Exception as e:
            logger.error(f"Error calculating usage count for tag {tag_id}: {e}")
            return 0

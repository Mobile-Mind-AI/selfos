"""
Task Service

This service encapsulates all business logic related to task management,
including CRUD operations, task completion workflows, and integration
with progress tracking, storytelling, and notification services.
"""

import logging
from datetime import datetime

import models
import schemas
from services.notifications import send_completion_notification
from services.progress import update_project_progress
from services.storytelling import enqueue_segment_generation
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, joinedload

logger = logging.getLogger(__name__)


class TaskService:
    """Service class for task-related business operations."""

    def get_task(
        self, db: Session, user_id: str, task_id: int
    ) -> models.Task | None:
        """
        Retrieve a single task by ID for a specific user.

        Args:
            db: Database session
            user_id: ID of the user who owns the task
            task_id: ID of the task to retrieve

        Returns:
            Task model instance or None if not found
        """
        try:
            task = (
                db.query(models.Task)
                .options(
                    joinedload(models.Task.media_attachments),
                    joinedload(models.Task.life_area),
                )
                .filter(models.Task.id == task_id, models.Task.user_id == user_id)
                .first()
            )

            if task:
                logger.info(f"Retrieved task {task_id} for user {user_id}")
            else:
                logger.warning(f"Task {task_id} not found for user {user_id}")

            return task
        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving task {task_id}: {e}")
            raise

    def list_tasks(self, db: Session, user_id: str) -> list[models.Task]:
        """
        Retrieve all tasks for a specific user.

        Args:
            db: Database session
            user_id: ID of the user whose tasks to retrieve

        Returns:
            List of task model instances
        """
        try:
            tasks = (
                db.query(models.Task)
                .options(
                    joinedload(models.Task.media_attachments),
                    joinedload(models.Task.life_area),
                )
                .filter(models.Task.user_id == user_id)
                .order_by(models.Task.created_at.desc())
                .all()
            )

            logger.info(f"Retrieved {len(tasks)} tasks for user {user_id}")
            return tasks
        except SQLAlchemyError as e:
            logger.error(f"Database error listing tasks for user {user_id}: {e}")
            raise

    def create_task(
        self, db: Session, user_id: str, task_data: schemas.TaskCreate
    ) -> models.Task:
        """
        Create a new task for a user.

        Args:
            db: Database session
            user_id: ID of the user creating the task
            task_data: Task creation data

        Returns:
            Created task model instance
        """
        try:
            # Validate parent_id if provided
            if task_data.parent_id:
                if not self.get_task(db, user_id, task_data.parent_id):
                    raise ValueError(f"Parent task {task_data.parent_id} not found")

            # Exclude fields that need special handling
            task_payload = task_data.model_dump(
                exclude={
                    "dependencies",
                    "tag_ids",
                    "estimated_hours",
                    "actual_hours",
                    "parent_id",
                }
            )

            # Convert estimated_hours to duration in minutes
            if task_data.estimated_hours is not None:
                task_payload["duration"] = int(task_data.estimated_hours * 60)

            db_task = models.Task(**task_payload, user_id=user_id)

            if task_data.dependencies:
                db_task.depends_on_task_id = task_data.dependencies[0]

            # Handle tags if provided
            if task_data.tag_ids:
                tags = (
                    db.query(models.Tag)
                    .filter(
                        models.Tag.id.in_(task_data.tag_ids),
                        models.Tag.user_id == user_id,
                    )
                    .all()
                )
                db_task.tags = tags

            db.add(db_task)
            db.commit()
            db.refresh(db_task)

            logger.info(
                f"Created task {db_task.id} '{db_task.title}' for user {user_id} (parent: {task_data.parent_id})"
            )
            return db_task
        except (SQLAlchemyError, ValueError) as e:
            logger.error(f"Database error creating task for user {user_id}: {e}")
            db.rollback()
            raise

    async def update_task(
        self, db: Session, user_id: str, task_id: int, task_data: schemas.TaskCreate
    ) -> models.Task | None:
        """
        Update an existing task and handle completion workflows.

        Args:
            db: Database session
            user_id: ID of the user who owns the task
            task_id: ID of the task to update
            task_data: Updated task data

        Returns:
            Updated task model instance or None if not found
        """
        try:
            task = (
                db.query(models.Task)
                .options(
                    joinedload(models.Task.media_attachments),
                    joinedload(models.Task.life_area),
                )
                .filter(models.Task.id == task_id, models.Task.user_id == user_id)
                .first()
            )

            if not task:
                logger.warning(f"Task {task_id} not found for update by user {user_id}")
                return None

            # Store old status to detect completion
            old_status = task.status

            # Update task fields
            task.title = task_data.title
            task.description = task_data.description
            task.due_date = task_data.due_date
            task.estimated_hours = task_data.estimated_hours
            task.actual_hours = task_data.actual_hours
            task.status = task_data.status
            task.progress = task_data.progress
            task.life_area_id = task_data.life_area_id
            if task_data.dependencies:
                task.depends_on_task_id = task_data.dependencies[0]
            else:
                task.depends_on_task_id = None

            # Handle tags if provided
            if hasattr(task_data, "tag_ids") and task_data.tag_ids is not None:
                tags = (
                    db.query(models.Tag)
                    .filter(
                        models.Tag.id.in_(task_data.tag_ids),
                        models.Tag.user_id == user_id,
                    )
                    .all()
                )
                task.tags = tags

            task.updated_at = datetime.utcnow()

            db.commit()
            db.refresh(task)

            # Handle task completion workflow
            if old_status != "completed" and task.status == "completed":
                await self._handle_task_completion(db, task, old_status)

            logger.info(
                f"Updated task {task_id} for user {user_id}. Status: {old_status} -> {task.status}"
            )
            return task
        except SQLAlchemyError as e:
            logger.error(f"Database error updating task {task_id}: {e}")
            db.rollback()
            raise

    async def mark_task_complete(
        self, db: Session, user_id: str, task_id: int
    ) -> models.Task | None:
        """
        Mark a task as completed and trigger all completion workflows.

        Args:
            db: Database session
            user_id: ID of the user who owns the task
            task_id: ID of the task to complete

        Returns:
            Updated task model instance or None if not found
        """
        try:
            task = (
                db.query(models.Task)
                .options(
                    joinedload(models.Task.media_attachments),
                    joinedload(models.Task.life_area),
                )
                .filter(models.Task.id == task_id, models.Task.user_id == user_id)
                .first()
            )

            if not task:
                logger.warning(
                    f"Task {task_id} not found for completion by user {user_id}"
                )
                return None

            if task.status == "completed":
                logger.info(f"Task {task_id} is already completed")
                return task

            # Store old status
            old_status = task.status

            # Mark as completed
            task.status = "completed"
            task.progress = 100.0
            task.updated_at = datetime.utcnow()

            db.commit()
            db.refresh(task)

            # Handle completion workflow
            await self._handle_task_completion(db, task, old_status)

            logger.info(
                f"Marked task {task_id} '{task.title}' as completed for user {user_id}"
            )
            return task
        except SQLAlchemyError as e:
            logger.error(f"Database error completing task {task_id}: {e}")
            db.rollback()
            raise

    def delete_task(self, db: Session, user_id: str, task_id: int) -> bool:
        """
        Delete a task.

        Args:
            db: Database session
            user_id: ID of the user who owns the task
            task_id: ID of the task to delete

        Returns:
            True if task was deleted, False if not found
        """
        try:
            task = (
                db.query(models.Task)
                .filter(models.Task.id == task_id, models.Task.user_id == user_id)
                .first()
            )

            if not task:
                logger.warning(
                    f"Task {task_id} not found for deletion by user {user_id}"
                )
                return False

            db.delete(task)
            db.commit()

            logger.info(f"Deleted task {task_id} '{task.title}' for user {user_id}")
            return True
        except SQLAlchemyError as e:
            logger.error(f"Database error deleting task {task_id}: {e}")
            db.rollback()
            raise

    def get_tasks_by_goal(
        self, db: Session, user_id: str, goal_id: int
    ) -> list[models.Task]:
        """
        Retrieve all tasks for a specific goal.

        Args:
            db: Database session
            user_id: ID of the user
            goal_id: ID of the goal

        Returns:
            List of tasks for the specified goal
        """
        try:
            tasks = (
                db.query(models.Task)
                .options(
                    joinedload(models.Task.media_attachments),
                    joinedload(models.Task.life_area),
                )
                .filter(models.Task.user_id == user_id, models.Task.goal_id == goal_id)
                .all()
            )

            logger.info(
                f"Retrieved {len(tasks)} tasks for goal {goal_id}, user {user_id}"
            )
            return tasks
        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving tasks for goal {goal_id}: {e}")
            raise

    def get_tasks_by_status(
        self, db: Session, user_id: str, status: str
    ) -> list[models.Task]:
        """
        Retrieve all tasks with a specific status.

        Args:
            db: Database session
            user_id: ID of the user
            status: Task status to filter by

        Returns:
            List of tasks with the specified status
        """
        try:
            tasks = (
                db.query(models.Task)
                .options(
                    joinedload(models.Task.media_attachments),
                    joinedload(models.Task.life_area),
                )
                .filter(models.Task.user_id == user_id, models.Task.status == status)
                .all()
            )

            logger.info(
                f"Retrieved {len(tasks)} tasks with status '{status}' for user {user_id}"
            )
            return tasks
        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving tasks with status '{status}': {e}")
            raise

    # Hierarchy methods
    def get_children(
        self, db: Session, user_id: str, parent_id: int
    ) -> list[models.Task]:
        """Get direct children of a task."""
        try:
            children = (
                db.query(models.Task)
                .options(
                    joinedload(models.Task.media_attachments),
                    joinedload(models.Task.life_area),
                )
                .filter(
                    models.Task.parent_id == parent_id, models.Task.user_id == user_id
                )
                .order_by(models.Task.created_at.asc())
                .all()
            )

            logger.info(
                f"Retrieved {len(children)} children for task {parent_id}, user {user_id}"
            )
            return children
        except SQLAlchemyError as e:
            logger.error(f"Database error getting children for task {parent_id}: {e}")
            raise

    def get_descendants(
        self, db: Session, user_id: str, parent_id: int
    ) -> list[models.Task]:
        """Get all descendants of a task recursively."""
        try:
            descendants = []
            children = self.get_children(db, user_id, parent_id)

            for child in children:
                descendants.append(child)
                # Recursively get descendants
                child_descendants = self.get_descendants(db, user_id, child.id)
                descendants.extend(child_descendants)

            logger.info(
                f"Retrieved {len(descendants)} descendants for task {parent_id}, user {user_id}"
            )
            return descendants
        except Exception as e:
            logger.error(f"Error getting descendants for task {parent_id}: {e}")
            raise

    def get_ancestors(
        self, db: Session, user_id: str, task_id: int
    ) -> list[models.Task]:
        """Get all ancestors of a task up to root."""
        try:
            ancestors = []
            current_task = self.get_task(db, user_id, task_id)

            while current_task and current_task.parent_id:
                parent = self.get_task(db, user_id, current_task.parent_id)
                if parent:
                    ancestors.append(parent)
                    current_task = parent
                else:
                    break

            logger.info(
                f"Retrieved {len(ancestors)} ancestors for task {task_id}, user {user_id}"
            )
            return list(reversed(ancestors))  # Root first
        except Exception as e:
            logger.error(f"Error getting ancestors for task {task_id}: {e}")
            raise

    def get_root_tasks(
        self,
        db: Session,
        user_id: str,
        project_id: int | None = None,
        goal_id: int | None = None,
    ) -> list[models.Task]:
        """Get root level tasks (parent_id = None)."""
        try:
            query = (
                db.query(models.Task)
                .options(
                    joinedload(models.Task.media_attachments),
                    joinedload(models.Task.life_area),
                )
                .filter(models.Task.user_id == user_id, models.Task.parent_id.is_(None))
            )

            if project_id:
                query = query.filter(models.Task.project_id == project_id)
            if goal_id:
                query = query.filter(models.Task.goal_id == goal_id)

            root_tasks = query.order_by(models.Task.created_at.asc()).all()

            logger.info(f"Retrieved {len(root_tasks)} root tasks for user {user_id}")
            return root_tasks
        except SQLAlchemyError as e:
            logger.error(f"Database error getting root tasks for user {user_id}: {e}")
            raise

    def validate_hierarchy_move(
        self, db: Session, user_id: str, task_id: int, new_parent_id: int | None
    ) -> bool:
        """Validate that moving a task won't create a circular dependency."""
        if new_parent_id is None:
            return True  # Moving to root is always valid

        if task_id == new_parent_id:
            return False  # Cannot be parent of itself

        # Check if new_parent_id is a descendant of task_id
        descendants = self.get_descendants(db, user_id, task_id)
        descendant_ids = {desc.id for desc in descendants}

        return new_parent_id not in descendant_ids

    def move_task(
        self, db: Session, user_id: str, task_id: int, new_parent_id: int | None
    ) -> models.Task | None:
        """Move a task to a new parent in the hierarchy."""
        try:
            # Validate the move
            if not self.validate_hierarchy_move(db, user_id, task_id, new_parent_id):
                raise ValueError(
                    "Invalid hierarchy move: would create circular dependency"
                )

            # Get the task
            task = self.get_task(db, user_id, task_id)
            if not task:
                return None

            # If new parent is specified, verify it exists and belongs to user
            if new_parent_id:
                parent = self.get_task(db, user_id, new_parent_id)
                if not parent:
                    raise ValueError(f"Parent task {new_parent_id} not found")

                # Ensure parent and child have compatible project/goal associations
                if (
                    task.project_id != parent.project_id
                    and parent.project_id is not None
                ):
                    task.project_id = parent.project_id
                if task.goal_id != parent.goal_id and parent.goal_id is not None:
                    task.goal_id = parent.goal_id

            # Update parent
            task.parent_id = new_parent_id
            task.updated_at = datetime.utcnow()

            db.commit()
            db.refresh(task)

            logger.info(
                f"Moved task {task_id} to parent {new_parent_id} for user {user_id}"
            )
            return task
        except (SQLAlchemyError, ValueError) as e:
            logger.error(f"Error moving task {task_id}: {e}")
            db.rollback()
            raise

    def get_task_tree(
        self,
        db: Session,
        user_id: str,
        root_id: int | None = None,
        project_id: int | None = None,
        goal_id: int | None = None,
    ) -> list[dict]:
        """Get hierarchical tree of tasks."""
        try:

            def build_tree_node(task: models.Task, level: int = 0) -> dict:
                children = self.get_children(db, user_id, task.id)
                return {
                    "id": task.id,
                    "title": task.title,
                    "status": task.status,
                    "progress": task.progress,
                    "level": level,
                    "parent_id": task.parent_id,
                    "created_at": task.created_at,
                    "children": [
                        build_tree_node(child, level + 1) for child in children
                    ],
                    "children_count": len(children),
                }

            if root_id:
                # Start from specific root
                root_task = self.get_task(db, user_id, root_id)
                if not root_task:
                    return []
                return [build_tree_node(root_task)]
            else:
                # Get all root level tasks
                root_tasks = self.get_root_tasks(db, user_id, project_id, goal_id)
                return [build_tree_node(task) for task in root_tasks]

        except Exception as e:
            logger.error(f"Error building task tree for user {user_id}: {e}")
            raise

    def get_hierarchy_stats(
        self,
        db: Session,
        user_id: str,
        project_id: int | None = None,
        goal_id: int | None = None,
    ) -> dict:
        """Get hierarchy statistics for tasks."""
        try:
            query = db.query(models.Task).filter(models.Task.user_id == user_id)

            if project_id:
                query = query.filter(models.Task.project_id == project_id)
            if goal_id:
                query = query.filter(models.Task.goal_id == goal_id)

            all_tasks = query.all()

            # Calculate statistics
            total_tasks = len(all_tasks)
            root_tasks = [t for t in all_tasks if t.parent_id is None]

            # Calculate max depth
            max_depth = 0
            for root_task in root_tasks:
                depth = self._calculate_depth(db, user_id, root_task.id)
                max_depth = max(max_depth, depth)

            # Calculate completion by level
            completion_by_level = {}
            for task in all_tasks:
                level = self._get_task_level(db, user_id, task.id)
                if level not in completion_by_level:
                    completion_by_level[level] = {"total": 0, "completed": 0}
                completion_by_level[level]["total"] += 1
                if task.status == "completed":
                    completion_by_level[level]["completed"] += 1

            # Convert to completion rates
            completion_rates = {}
            for level, stats in completion_by_level.items():
                completion_rates[level] = (
                    stats["completed"] / stats["total"] if stats["total"] > 0 else 0.0
                )

            return {
                "total_items": total_tasks,
                "root_items": len(root_tasks),
                "max_depth": max_depth,
                "completion_rate_by_level": completion_rates,
            }

        except Exception as e:
            logger.error(f"Error calculating hierarchy stats for user {user_id}: {e}")
            raise

    def _calculate_depth(
        self, db: Session, user_id: str, task_id: int, current_depth: int = 0
    ) -> int:
        """Calculate the maximum depth of a task subtree."""
        children = self.get_children(db, user_id, task_id)
        if not children:
            return current_depth

        max_child_depth = current_depth
        for child in children:
            child_depth = self._calculate_depth(
                db, user_id, child.id, current_depth + 1
            )
            max_child_depth = max(max_child_depth, child_depth)

        return max_child_depth

    def _get_task_level(self, db: Session, user_id: str, task_id: int) -> int:
        """Get the hierarchy level of a task (0 = root)."""
        ancestors = self.get_ancestors(db, user_id, task_id)
        return len(ancestors)

    async def _handle_task_completion(
        self, db: Session, task: models.Task, old_status: str
    ):
        """
        Handle all workflows that should be triggered when a task is completed.

        Args:
            db: Database session
            task: The completed task
            old_status: Previous status of the task
        """
        try:
            task_data = {
                "task_id": str(task.id),
                "user_id": task.user_id,
                "title": task.title,
                "description": task.description,
                "goal_id": str(task.goal_id) if task.goal_id else None,
                "life_area_id": str(task.life_area_id) if task.life_area_id else None,
                "estimated_hours": task.estimated_hours,
                "media_count": (
                    len(task.media_attachments) if task.media_attachments else 0
                ),
                "previous_status": old_status,
            }

            # 1. Update goal progress if task is associated with a goal
            if task.goal_id:
                try:
                    progress_result = await update_project_progress(
                        db, task.goal_id, task.user_id
                    )
                    logger.info(f"Updated goal progress: {progress_result}")
                except Exception as e:
                    logger.error(f"Failed to update goal progress: {e}")

            # 2. Generate story segment
            try:
                story_result = await enqueue_segment_generation(db, task_data)
                logger.info(f"Generated story segment: {story_result}")
            except Exception as e:
                logger.error(f"Failed to generate story segment: {e}")

            # 3. Send completion notification
            try:
                notification_result = await send_completion_notification(
                    task.user_id, task.title, task_data
                )
                logger.info(f"Sent completion notification: {notification_result}")
            except Exception as e:
                logger.error(f"Failed to send completion notification: {e}")

        except Exception as e:
            logger.error(f"Error in task completion workflow: {e}")
            # Don't re-raise - completion workflows should not block the main operation


# Create a singleton instance of the service
task_service = TaskService()

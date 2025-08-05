"""
Task Service

This service encapsulates all business logic related to task management,
including CRUD operations, task completion workflows, and integration
with progress tracking, storytelling, and notification services.
"""

import logging
from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import SQLAlchemyError

import models
import schemas
from services.progress import update_project_progress
from services.storytelling import enqueue_segment_generation
from services.notifications import send_completion_notification

logger = logging.getLogger(__name__)


class TaskService:
    """Service class for task-related business operations."""
    
    def get_task(self, db: Session, user_id: str, task_id: int) -> Optional[models.Task]:
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
            task = db.query(models.Task).options(
                joinedload(models.Task.media_attachments),
                joinedload(models.Task.life_area)
            ).filter(
                models.Task.id == task_id,
                models.Task.user_id == user_id
            ).first()
            
            if task:
                logger.info(f"Retrieved task {task_id} for user {user_id}")
            else:
                logger.warning(f"Task {task_id} not found for user {user_id}")
                
            return task
        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving task {task_id}: {e}")
            raise
    
    def list_tasks(self, db: Session, user_id: str) -> List[models.Task]:
        """
        Retrieve all tasks for a specific user.
        
        Args:
            db: Database session
            user_id: ID of the user whose tasks to retrieve
            
        Returns:
            List of task model instances
        """
        try:
            tasks = db.query(models.Task).options(
                joinedload(models.Task.media_attachments),
                joinedload(models.Task.life_area)
            ).filter(models.Task.user_id == user_id).all()
            
            logger.info(f"Retrieved {len(tasks)} tasks for user {user_id}")
            return tasks
        except SQLAlchemyError as e:
            logger.error(f"Database error listing tasks for user {user_id}: {e}")
            raise
    
    def create_task(self, db: Session, user_id: str, task_data: schemas.TaskCreate) -> models.Task:
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
            db_task = models.Task(
                goal_id=task_data.goal_id,
                user_id=user_id,
                title=task_data.title,
                description=task_data.description,
                due_date=task_data.due_date,
                duration=task_data.duration,
                status=task_data.status,
                progress=task_data.progress,
                life_area_id=task_data.life_area_id,
                dependencies=task_data.dependencies,
            )
            
            db.add(db_task)
            db.commit()
            db.refresh(db_task)
            
            logger.info(f"Created task {db_task.id} '{db_task.title}' for user {user_id}")
            return db_task
        except SQLAlchemyError as e:
            logger.error(f"Database error creating task for user {user_id}: {e}")
            db.rollback()
            raise
    
    async def update_task(self, db: Session, user_id: str, task_id: int, task_data: schemas.TaskCreate) -> Optional[models.Task]:
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
            task = db.query(models.Task).options(
                joinedload(models.Task.media_attachments),
                joinedload(models.Task.life_area)
            ).filter(
                models.Task.id == task_id,
                models.Task.user_id == user_id
            ).first()
            
            if not task:
                logger.warning(f"Task {task_id} not found for update by user {user_id}")
                return None
            
            # Store old status to detect completion
            old_status = task.status
            
            # Update task fields
            task.title = task_data.title
            task.description = task_data.description
            task.due_date = task_data.due_date
            task.duration = task_data.duration
            task.status = task_data.status
            task.progress = task_data.progress
            task.life_area_id = task_data.life_area_id
            task.dependencies = task_data.dependencies
            task.updated_at = datetime.utcnow()
            
            db.commit()
            db.refresh(task)
            
            # Handle task completion workflow
            if old_status != "completed" and task.status == "completed":
                await self._handle_task_completion(db, task, old_status)
            
            logger.info(f"Updated task {task_id} for user {user_id}. Status: {old_status} -> {task.status}")
            return task
        except SQLAlchemyError as e:
            logger.error(f"Database error updating task {task_id}: {e}")
            db.rollback()
            raise
    
    async def mark_task_complete(self, db: Session, user_id: str, task_id: int) -> Optional[models.Task]:
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
            task = db.query(models.Task).options(
                joinedload(models.Task.media_attachments),
                joinedload(models.Task.life_area)
            ).filter(
                models.Task.id == task_id,
                models.Task.user_id == user_id
            ).first()
            
            if not task:
                logger.warning(f"Task {task_id} not found for completion by user {user_id}")
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
            
            logger.info(f"Marked task {task_id} '{task.title}' as completed for user {user_id}")
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
            task = db.query(models.Task).filter(
                models.Task.id == task_id,
                models.Task.user_id == user_id
            ).first()
            
            if not task:
                logger.warning(f"Task {task_id} not found for deletion by user {user_id}")
                return False
            
            db.delete(task)
            db.commit()
            
            logger.info(f"Deleted task {task_id} '{task.title}' for user {user_id}")
            return True
        except SQLAlchemyError as e:
            logger.error(f"Database error deleting task {task_id}: {e}")
            db.rollback()
            raise
    
    def get_tasks_by_goal(self, db: Session, user_id: str, goal_id: int) -> List[models.Task]:
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
            tasks = db.query(models.Task).options(
                joinedload(models.Task.media_attachments),
                joinedload(models.Task.life_area)
            ).filter(
                models.Task.user_id == user_id,
                models.Task.goal_id == goal_id
            ).all()
            
            logger.info(f"Retrieved {len(tasks)} tasks for goal {goal_id}, user {user_id}")
            return tasks
        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving tasks for goal {goal_id}: {e}")
            raise
    
    def get_tasks_by_status(self, db: Session, user_id: str, status: str) -> List[models.Task]:
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
            tasks = db.query(models.Task).options(
                joinedload(models.Task.media_attachments),
                joinedload(models.Task.life_area)
            ).filter(
                models.Task.user_id == user_id,
                models.Task.status == status
            ).all()
            
            logger.info(f"Retrieved {len(tasks)} tasks with status '{status}' for user {user_id}")
            return tasks
        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving tasks with status '{status}': {e}")
            raise
    
    async def _handle_task_completion(self, db: Session, task: models.Task, old_status: str):
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
                "duration": task.duration,
                "media_count": len(task.media_attachments) if task.media_attachments else 0,
                "previous_status": old_status
            }
            
            # 1. Update goal progress if task is associated with a goal
            if task.goal_id:
                try:
                    progress_result = await update_project_progress(db, task.goal_id, task.user_id)
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
                    task.user_id, 
                    task.title, 
                    task_data
                )
                logger.info(f"Sent completion notification: {notification_result}")
            except Exception as e:
                logger.error(f"Failed to send completion notification: {e}")
                
        except Exception as e:
            logger.error(f"Error in task completion workflow: {e}")
            # Don't re-raise - completion workflows should not block the main operation


# Create a singleton instance of the service
task_service = TaskService()

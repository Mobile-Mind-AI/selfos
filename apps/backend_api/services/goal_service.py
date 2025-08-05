"""
Goal Service

This service encapsulates all business logic related to goal management,
including CRUD operations, progress calculations, and goal-related workflows.
"""

import logging
from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import SQLAlchemyError

import models
import schemas

logger = logging.getLogger(__name__)


class GoalService:
    """Service class for goal-related business operations."""
    
    def get_goal(self, db: Session, user_id: str, goal_id: int) -> Optional[models.Goal]:
        """
        Retrieve a single goal by ID for a specific user.
        
        Args:
            db: Database session
            user_id: ID of the user who owns the goal
            goal_id: ID of the goal to retrieve
            
        Returns:
            Goal model instance or None if not found
        """
        try:
            goal = db.query(models.Goal).options(
                joinedload(models.Goal.tasks),
                joinedload(models.Goal.media_attachments),
                joinedload(models.Goal.life_area)
            ).filter(
                models.Goal.id == goal_id,
                models.Goal.user_id == user_id
            ).first()
            
            if goal:
                logger.info(f"Retrieved goal {goal_id} for user {user_id}")
            else:
                logger.warning(f"Goal {goal_id} not found for user {user_id}")
                
            return goal
        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving goal {goal_id}: {e}")
            raise
    
    def list_goals(self, db: Session, user_id: str) -> List[models.Goal]:
        """
        Retrieve all goals for a specific user.
        
        Args:
            db: Database session
            user_id: ID of the user whose goals to retrieve
            
        Returns:
            List of goal model instances
        """
        try:
            goals = db.query(models.Goal).options(
                joinedload(models.Goal.tasks),
                joinedload(models.Goal.media_attachments),
                joinedload(models.Goal.life_area)
            ).filter(models.Goal.user_id == user_id).all()
            
            logger.info(f"Retrieved {len(goals)} goals for user {user_id}")
            return goals
        except SQLAlchemyError as e:
            logger.error(f"Database error listing goals for user {user_id}: {e}")
            raise
    
    def create_goal(self, db: Session, user_id: str, goal_data: schemas.GoalCreate) -> models.Goal:
        """
        Create a new goal for a user.
        
        Args:
            db: Database session
            user_id: ID of the user creating the goal
            goal_data: Goal creation data
            
        Returns:
            Created goal model instance
        """
        try:
            db_goal = models.Goal(
                user_id=user_id,
                title=goal_data.title,
                description=goal_data.description,
                status=goal_data.status,
                progress=goal_data.progress,
                life_area_id=goal_data.life_area_id,
            )
            
            db.add(db_goal)
            db.commit()
            db.refresh(db_goal)
            
            logger.info(f"Created goal {db_goal.id} '{db_goal.title}' for user {user_id}")
            return db_goal
        except SQLAlchemyError as e:
            logger.error(f"Database error creating goal for user {user_id}: {e}")
            db.rollback()
            raise
    
    def update_goal(self, db: Session, user_id: str, goal_id: int, goal_data: schemas.GoalCreate) -> Optional[models.Goal]:
        """
        Update an existing goal.
        
        Args:
            db: Database session
            user_id: ID of the user who owns the goal
            goal_id: ID of the goal to update
            goal_data: Updated goal data
            
        Returns:
            Updated goal model instance or None if not found
        """
        try:
            goal = db.query(models.Goal).options(
                joinedload(models.Goal.tasks),
                joinedload(models.Goal.media_attachments),
                joinedload(models.Goal.life_area)
            ).filter(
                models.Goal.id == goal_id,
                models.Goal.user_id == user_id
            ).first()
            
            if not goal:
                logger.warning(f"Goal {goal_id} not found for update by user {user_id}")
                return None
            
            # Store old progress for comparison
            old_progress = goal.progress
            
            # Update goal fields
            goal.title = goal_data.title
            goal.description = goal_data.description
            goal.status = goal_data.status
            goal.progress = goal_data.progress
            goal.life_area_id = goal_data.life_area_id
            goal.updated_at = datetime.utcnow()
            
            db.commit()
            db.refresh(goal)
            
            logger.info(f"Updated goal {goal_id} for user {user_id}. Progress: {old_progress}% -> {goal.progress}%")
            return goal
        except SQLAlchemyError as e:
            logger.error(f"Database error updating goal {goal_id}: {e}")
            db.rollback()
            raise
    
    def delete_goal(self, db: Session, user_id: str, goal_id: int) -> bool:
        """
        Delete a goal.
        
        Args:
            db: Database session
            user_id: ID of the user who owns the goal
            goal_id: ID of the goal to delete
            
        Returns:
            True if goal was deleted, False if not found
        """
        try:
            goal = db.query(models.Goal).options(
                joinedload(models.Goal.tasks),
                joinedload(models.Goal.media_attachments),
                joinedload(models.Goal.life_area)
            ).filter(
                models.Goal.id == goal_id,
                models.Goal.user_id == user_id
            ).first()
            
            if not goal:
                logger.warning(f"Goal {goal_id} not found for deletion by user {user_id}")
                return False
            
            db.delete(goal)
            db.commit()
            
            logger.info(f"Deleted goal {goal_id} '{goal.title}' for user {user_id}")
            return True
        except SQLAlchemyError as e:
            logger.error(f"Database error deleting goal {goal_id}: {e}")
            db.rollback()
            raise
    
    def get_goals_by_life_area(self, db: Session, user_id: str, life_area_id: int) -> List[models.Goal]:
        """
        Retrieve all goals for a specific life area.
        
        Args:
            db: Database session
            user_id: ID of the user
            life_area_id: ID of the life area
            
        Returns:
            List of goals in the specified life area
        """
        try:
            goals = db.query(models.Goal).options(
                joinedload(models.Goal.tasks),
                joinedload(models.Goal.media_attachments),
                joinedload(models.Goal.life_area)
            ).filter(
                models.Goal.user_id == user_id,
                models.Goal.life_area_id == life_area_id
            ).all()
            
            logger.info(f"Retrieved {len(goals)} goals for life area {life_area_id}, user {user_id}")
            return goals
        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving goals for life area {life_area_id}: {e}")
            raise
    
    def get_goals_by_status(self, db: Session, user_id: str, status: str) -> List[models.Goal]:
        """
        Retrieve all goals with a specific status.
        
        Args:
            db: Database session
            user_id: ID of the user
            status: Goal status to filter by
            
        Returns:
            List of goals with the specified status
        """
        try:
            goals = db.query(models.Goal).options(
                joinedload(models.Goal.tasks),
                joinedload(models.Goal.media_attachments),
                joinedload(models.Goal.life_area)
            ).filter(
                models.Goal.user_id == user_id,
                models.Goal.status == status
            ).all()
            
            logger.info(f"Retrieved {len(goals)} goals with status '{status}' for user {user_id}")
            return goals
        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving goals with status '{status}': {e}")
            raise


# Create a singleton instance of the service
goal_service = GoalService()

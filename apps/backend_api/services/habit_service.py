"""
Habit Service

This service encapsulates all business logic related to habit management,
including CRUD operations, completion tracking, progress calculations, and streak management.
"""

import logging
from datetime import datetime, date, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import and_, desc, func

import models
import schemas

logger = logging.getLogger(__name__)


class HabitService:
    """Service class for habit-related business operations."""
    
    def get_habit(self, db: Session, user_id: str, habit_id: int) -> Optional[models.Habit]:
        """
        Retrieve a single habit by ID for a specific user.
        
        Args:
            db: Database session
            user_id: ID of the user who owns the habit
            habit_id: ID of the habit to retrieve
            
        Returns:
            Habit model instance or None if not found
        """
        try:
            habit = db.query(models.Habit).options(
                joinedload(models.Habit.completions),
                joinedload(models.Habit.goal),
                joinedload(models.Habit.life_area)
            ).filter(
                models.Habit.id == habit_id,
                models.Habit.user_id == user_id
            ).first()
            
            if habit:
                logger.info(f"Retrieved habit {habit_id} for user {user_id}")
            else:
                logger.warning(f"Habit {habit_id} not found for user {user_id}")
                
            return habit
        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving habit {habit_id}: {e}")
            raise
    
    def list_habits(self, db: Session, user_id: str, is_active: Optional[bool] = None) -> List[models.Habit]:
        """
        Retrieve all habits for a specific user.
        
        Args:
            db: Database session
            user_id: ID of the user whose habits to retrieve
            is_active: Filter by active status (None = all habits)
            
        Returns:
            List of habit model instances
        """
        try:
            query = db.query(models.Habit).options(
                joinedload(models.Habit.completions),
                joinedload(models.Habit.goal),
                joinedload(models.Habit.life_area)
            ).filter(models.Habit.user_id == user_id)
            
            if is_active is not None:
                query = query.filter(models.Habit.is_active == is_active)
            
            habits = query.all()
            
            logger.info(f"Retrieved {len(habits)} habits for user {user_id} (active={is_active})")
            return habits
        except SQLAlchemyError as e:
            logger.error(f"Database error listing habits for user {user_id}: {e}")
            raise
    
    def create_habit(self, db: Session, user_id: str, habit_data: schemas.HabitCreate) -> models.Habit:
        """
        Create a new habit for a user.
        
        Args:
            db: Database session
            user_id: ID of the user creating the habit
            habit_data: Habit creation data
            
        Returns:
            Created habit model instance
        """
        try:
            # Convert datetime to date if start_date provided
            start_date = habit_data.start_date.date() if habit_data.start_date else date.today()
            end_date = habit_data.end_date.date() if habit_data.end_date else None
            
            db_habit = models.Habit(
                user_id=user_id,
                title=habit_data.title,
                description=habit_data.description,
                recurrence_rule=habit_data.recurrence_rule.dict(),
                is_active=habit_data.is_active,
                start_date=start_date,
                end_date=end_date,
                icon=habit_data.icon,
                color=habit_data.color,
                goal_id=habit_data.goal_id,
                life_area_id=habit_data.life_area_id,
            )
            
            db.add(db_habit)
            db.commit()
            db.refresh(db_habit)
            
            logger.info(f"Created habit {db_habit.id} '{db_habit.title}' for user {user_id}")
            return db_habit
        except SQLAlchemyError as e:
            logger.error(f"Database error creating habit for user {user_id}: {e}")
            db.rollback()
            raise
    
    def update_habit(self, db: Session, user_id: str, habit_id: int, habit_data: schemas.HabitUpdate) -> Optional[models.Habit]:
        """
        Update an existing habit.
        
        Args:
            db: Database session
            user_id: ID of the user who owns the habit
            habit_id: ID of the habit to update
            habit_data: Updated habit data
            
        Returns:
            Updated habit model instance or None if not found
        """
        try:
            habit = db.query(models.Habit).options(
                joinedload(models.Habit.completions),
                joinedload(models.Habit.goal),
                joinedload(models.Habit.life_area)
            ).filter(
                models.Habit.id == habit_id,
                models.Habit.user_id == user_id
            ).first()
            
            if not habit:
                logger.warning(f"Habit {habit_id} not found for update by user {user_id}")
                return None
            
            # Update habit fields (only if provided)
            update_fields = habit_data.dict(exclude_unset=True)
            for field, value in update_fields.items():
                if field == 'recurrence_rule' and value:
                    setattr(habit, field, value.dict())
                elif field in ['start_date', 'end_date'] and value:
                    setattr(habit, field, value.date() if hasattr(value, 'date') else value)
                else:
                    setattr(habit, field, value)
            
            habit.updated_at = datetime.utcnow()
            
            db.commit()
            db.refresh(habit)
            
            logger.info(f"Updated habit {habit_id} for user {user_id}")
            return habit
        except SQLAlchemyError as e:
            logger.error(f"Database error updating habit {habit_id}: {e}")
            db.rollback()
            raise
    
    def delete_habit(self, db: Session, user_id: str, habit_id: int) -> bool:
        """
        Delete a habit and all its completions.
        
        Args:
            db: Database session
            user_id: ID of the user who owns the habit
            habit_id: ID of the habit to delete
            
        Returns:
            True if habit was deleted, False if not found
        """
        try:
            habit = db.query(models.Habit).filter(
                models.Habit.id == habit_id,
                models.Habit.user_id == user_id
            ).first()
            
            if not habit:
                logger.warning(f"Habit {habit_id} not found for deletion by user {user_id}")
                return False
            
            db.delete(habit)
            db.commit()
            
            logger.info(f"Deleted habit {habit_id} '{habit.title}' for user {user_id}")
            return True
        except SQLAlchemyError as e:
            logger.error(f"Database error deleting habit {habit_id}: {e}")
            db.rollback()
            raise
    
    def complete_habit(self, db: Session, user_id: str, habit_id: int, completion_data: schemas.HabitCompletionCreate) -> Optional[models.HabitCompletion]:
        """
        Record a completion of a habit.
        
        Args:
            db: Database session
            user_id: ID of the user
            habit_id: ID of the habit to complete
            completion_data: Completion data
            
        Returns:
            Created completion model instance or None if habit not found
        """
        try:
            # Verify habit exists and belongs to user
            habit = db.query(models.Habit).filter(
                models.Habit.id == habit_id,
                models.Habit.user_id == user_id,
                models.Habit.is_active == True
            ).first()
            
            if not habit:
                logger.warning(f"Active habit {habit_id} not found for completion by user {user_id}")
                return None
            
            # Use provided completion date or today
            completion_date = completion_data.completion_date.date() if completion_data.completion_date else date.today()
            
            # Check if completion already exists for this date
            existing_completion = db.query(models.HabitCompletion).filter(
                models.HabitCompletion.habit_id == habit_id,
                models.HabitCompletion.completion_date == completion_date
            ).first()
            
            if existing_completion:
                logger.warning(f"Habit {habit_id} already completed on {completion_date}")
                return existing_completion
            
            # Create new completion
            db_completion = models.HabitCompletion(
                habit_id=habit_id,
                completion_date=completion_date,
                completion_time=datetime.utcnow(),
                notes=completion_data.notes,
                duration_minutes=completion_data.duration_minutes,
                intensity_rating=completion_data.intensity_rating,
            )
            
            db.add(db_completion)
            
            # Update habit statistics
            self._update_habit_stats(db, habit, completion_date)
            
            db.commit()
            db.refresh(db_completion)
            
            logger.info(f"Recorded completion for habit {habit_id} on {completion_date} by user {user_id}")
            return db_completion
        except SQLAlchemyError as e:
            logger.error(f"Database error completing habit {habit_id}: {e}")
            db.rollback()
            raise
    
    def get_habit_completions(self, db: Session, user_id: str, habit_id: int, 
                             start_date: Optional[date] = None, end_date: Optional[date] = None) -> List[models.HabitCompletion]:
        """
        Get completions for a habit within a date range.
        
        Args:
            db: Database session
            user_id: ID of the user
            habit_id: ID of the habit
            start_date: Start of date range (optional)
            end_date: End of date range (optional)
            
        Returns:
            List of completion model instances
        """
        try:
            # Verify habit belongs to user
            habit = db.query(models.Habit).filter(
                models.Habit.id == habit_id,
                models.Habit.user_id == user_id
            ).first()
            
            if not habit:
                logger.warning(f"Habit {habit_id} not found for user {user_id}")
                return []
            
            query = db.query(models.HabitCompletion).filter(
                models.HabitCompletion.habit_id == habit_id
            )
            
            if start_date:
                query = query.filter(models.HabitCompletion.completion_date >= start_date)
            if end_date:
                query = query.filter(models.HabitCompletion.completion_date <= end_date)
            
            completions = query.order_by(desc(models.HabitCompletion.completion_date)).all()
            
            logger.info(f"Retrieved {len(completions)} completions for habit {habit_id}")
            return completions
        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving completions for habit {habit_id}: {e}")
            raise
    
    def get_habit_progress(self, db: Session, user_id: str, habit_id: int, target_date: Optional[date] = None) -> Optional[schemas.HabitProgress]:
        """
        Calculate habit progress for current period.
        
        Args:
            db: Database session
            user_id: ID of the user
            habit_id: ID of the habit
            target_date: Date to calculate progress for (defaults to today)
            
        Returns:
            HabitProgress schema or None if habit not found
        """
        try:
            habit = db.query(models.Habit).filter(
                models.Habit.id == habit_id,
                models.Habit.user_id == user_id
            ).first()
            
            if not habit:
                return None
            
            if not target_date:
                target_date = date.today()
            
            # Calculate period based on recurrence rule
            period_start, period_end = self._get_current_period(habit.recurrence_rule, target_date)
            
            # Get completions in this period
            completions = db.query(models.HabitCompletion).filter(
                models.HabitCompletion.habit_id == habit_id,
                models.HabitCompletion.completion_date >= period_start,
                models.HabitCompletion.completion_date <= period_end
            ).all()
            
            target_count = habit.recurrence_rule.get('target_count', 1)
            actual_count = len(completions)
            completion_rate = min(actual_count / target_count, 1.0) if target_count > 0 else 0.0
            is_completed = actual_count >= target_count
            
            return schemas.HabitProgress(
                habit_id=habit_id,
                period_start=datetime.combine(period_start, datetime.min.time()),
                period_end=datetime.combine(period_end, datetime.min.time()),
                target_count=target_count,
                actual_count=actual_count,
                completion_rate=completion_rate,
                is_completed=is_completed,
                completions=[schemas.HabitCompletion.from_orm(c) for c in completions]
            )
        except Exception as e:
            logger.error(f"Error calculating progress for habit {habit_id}: {e}")
            return None
    
    def _update_habit_stats(self, db: Session, habit: models.Habit, completion_date: date):
        """
        Update habit statistics after a completion.
        
        Args:
            db: Database session
            habit: Habit model instance
            completion_date: Date of the completion
        """
        try:
            # Update total completions
            habit.total_completions += 1
            
            # Calculate current streak
            current_streak = self._calculate_current_streak(db, habit.id, completion_date)
            habit.current_streak = current_streak
            
            # Update best streak if current is better
            if current_streak > habit.best_streak:
                habit.best_streak = current_streak
            
            habit.updated_at = datetime.utcnow()
            
            logger.debug(f"Updated stats for habit {habit.id}: total={habit.total_completions}, streak={habit.current_streak}")
        except Exception as e:
            logger.error(f"Error updating stats for habit {habit.id}: {e}")
            raise
    
    def _calculate_current_streak(self, db: Session, habit_id: int, completion_date: date) -> int:
        """
        Calculate the current completion streak for a habit.
        
        Args:
            db: Database session
            habit_id: ID of the habit
            completion_date: Latest completion date
            
        Returns:
            Current streak count
        """
        try:
            # Get all completions for this habit, ordered by date descending
            completions = db.query(models.HabitCompletion).filter(
                models.HabitCompletion.habit_id == habit_id
            ).order_by(desc(models.HabitCompletion.completion_date)).all()
            
            if not completions:
                return 0
            
            streak = 0
            expected_date = completion_date
            
            for completion in completions:
                if completion.completion_date == expected_date:
                    streak += 1
                    expected_date -= timedelta(days=1)
                else:
                    # Gap in streak found
                    break
            
            return streak
        except Exception as e:
            logger.error(f"Error calculating streak for habit {habit_id}: {e}")
            return 0
    
    def _get_current_period(self, recurrence_rule: Dict[str, Any], target_date: date) -> tuple[date, date]:
        """
        Get the start and end dates for the current period based on recurrence rule.
        
        Args:
            recurrence_rule: Habit recurrence configuration
            target_date: Date to calculate period for
            
        Returns:
            Tuple of (period_start, period_end)
        """
        recurrence_type = recurrence_rule.get('type', 'daily')
        
        if recurrence_type == 'daily':
            return target_date, target_date
        elif recurrence_type == 'weekly':
            # Start of week (Monday = 0)
            days_since_monday = target_date.weekday()
            week_start = target_date - timedelta(days=days_since_monday)
            week_end = week_start + timedelta(days=6)
            return week_start, week_end
        elif recurrence_type == 'monthly':
            # Start of month
            month_start = target_date.replace(day=1)
            # End of month
            if target_date.month == 12:
                month_end = target_date.replace(year=target_date.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                month_end = target_date.replace(month=target_date.month + 1, day=1) - timedelta(days=1)
            return month_start, month_end
        else:
            # Default to daily
            return target_date, target_date


# Create a singleton instance of the service
habit_service = HabitService()

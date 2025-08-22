"""Service for managing habit tracking and completions."""

from datetime import date, datetime, timedelta

import models
import schemas
from sqlalchemy import and_, desc, func
from sqlalchemy.orm import Session


class HabitService:
    """Service class for habit management operations."""

    @staticmethod
    def create_habit(
        db: Session, user_id: str, habit: schemas.HabitCreate
    ) -> models.Habit:
        """Create a new habit for a user."""
        # Map schema fields to model fields
        db_habit = models.Habit(
            user_id=user_id,
            title=habit.title,
            description=habit.description,
            habit_type="build",  # Default type
            recurrence_rule=(
                habit.recurrence_rule.model_dump()
                if habit.recurrence_rule
                else {"type": "daily", "target_count": 1, "target_type": "count"}
            ),
            frequency="daily",  # Default frequency
            frequency_details=(
                habit.recurrence_rule.model_dump() if habit.recurrence_rule else None
            ),
            is_active=habit.is_active if habit.is_active is not None else True,
            start_date=habit.start_date or datetime.utcnow(),
            goal_id=getattr(habit, "goal_id", None),
            life_area_id=getattr(habit, "life_area_id", None),
            reminder_enabled=False,  # Default
            current_streak=0,
            best_streak=0,
            longest_streak=0,
            total_completions=0,
            version=1,
            icon=habit.icon if hasattr(habit, "icon") else None,
            color=habit.color if hasattr(habit, "color") else None,
        )

        # Set optional fields
        if habit.end_date:
            db_habit.end_date = habit.end_date

        db.add(db_habit)
        db.commit()
        db.refresh(db_habit)
        return db_habit

    @staticmethod
    def list_habits(
        db: Session, user_id: str, is_active: bool | None = None
    ) -> list[models.Habit]:
        """List all habits for a user, optionally filtered by active status."""
        query = db.query(models.Habit).filter(models.Habit.user_id == user_id)

        if is_active is not None:
            query = query.filter(models.Habit.is_active == is_active)

        return query.order_by(desc(models.Habit.created_at)).all()

    @staticmethod
    def get_habit(db: Session, user_id: str, habit_id: int) -> models.Habit | None:
        """Get a specific habit by ID."""
        return (
            db.query(models.Habit)
            .filter(and_(models.Habit.id == habit_id, models.Habit.user_id == user_id))
            .first()
        )

    @staticmethod
    def update_habit(
        db: Session, user_id: str, habit_id: int, habit_in: schemas.HabitUpdate
    ) -> models.Habit | None:
        """Update an existing habit."""
        db_habit = HabitService.get_habit(db, user_id, habit_id)
        if not db_habit:
            return None

        # Update fields that are provided
        update_data = habit_in.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            if field == "recurrence_rule":
                # Store recurrence rule as JSON
                db_habit.recurrence_rule = value.model_dump() if value else None
                db_habit.frequency_details = value.model_dump() if value else None
            elif hasattr(db_habit, field):
                setattr(db_habit, field, value)

        db_habit.updated_at = datetime.utcnow()
        db_habit.version += 1

        db.commit()
        db.refresh(db_habit)
        return db_habit

    @staticmethod
    def delete_habit(db: Session, user_id: str, habit_id: int) -> bool:
        """Delete a habit and all its completions."""
        db_habit = HabitService.get_habit(db, user_id, habit_id)
        if not db_habit:
            return False

        # Delete all completions first (cascade should handle this)
        db.query(models.HabitCompletion).filter(
            models.HabitCompletion.habit_id == habit_id
        ).delete()

        # Delete the habit
        db.delete(db_habit)
        db.commit()
        return True

    @staticmethod
    def complete_habit(
        db: Session,
        user_id: str,
        habit_id: int,
        completion: schemas.HabitCompletionCreate,
    ) -> models.HabitCompletion | None:
        """Record a completion of a habit."""
        # Verify habit exists and is active
        db_habit = HabitService.get_habit(db, user_id, habit_id)
        if not db_habit or not db_habit.is_active:
            return None

        now = datetime.utcnow()
        completion_date = completion.completion_date or now

        # For duplicate checking, we need to check by date only
        from datetime import date as date_type

        from sqlalchemy import func

        # Ensure we have a date object for comparison
        if isinstance(completion_date, datetime):
            check_date = completion_date.date()
        elif isinstance(completion_date, date_type):
            check_date = completion_date
        else:
            # Handle string or other formats if needed
            check_date = completion_date

        # Check for existing completion on the same day
        existing_completion = (
            db.query(models.HabitCompletion)
            .filter(
                models.HabitCompletion.habit_id == habit_id,
                models.HabitCompletion.user_id == user_id,
                func.date(models.HabitCompletion.completion_date) == check_date,
            )
            .first()
        )

        if existing_completion:
            # Return existing completion instead of creating a new one
            return existing_completion

        # Create completion record
        db_completion = models.HabitCompletion(
            habit_id=habit_id,
            user_id=user_id,
            completion_date=completion_date,
            completion_time=now,  # Exact timestamp of completion
            completed=True,
            notes=completion.notes,
            duration_minutes=completion.duration_minutes,
            intensity_rating=completion.intensity_rating,
        )

        # Set optional fields for backward compatibility
        if completion.duration_minutes:
            db_completion.value = completion.duration_minutes
        if completion.intensity_rating:
            db_completion.rating = completion.intensity_rating

        db.add(db_completion)

        # Update habit statistics
        db_habit.total_completions += 1

        # Recalculate streak
        today = date.today()
        db_habit.current_streak = HabitService._calculate_current_streak(
            db, habit_id, today
        )
        if db_habit.current_streak > db_habit.longest_streak:
            db_habit.longest_streak = db_habit.current_streak
            db_habit.best_streak = db_habit.current_streak

        db_habit.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(db_completion)
        return db_completion

    @staticmethod
    def get_habit_completions(
        db: Session,
        user_id: str,
        habit_id: int,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list[models.HabitCompletion]:
        """Get completions for a habit within a date range."""
        # Verify habit belongs to user
        if not HabitService.get_habit(db, user_id, habit_id):
            return []

        query = db.query(models.HabitCompletion).filter(
            models.HabitCompletion.habit_id == habit_id
        )

        if start_date:
            query = query.filter(
                func.date(models.HabitCompletion.completion_date) >= start_date
            )

        if end_date:
            query = query.filter(
                func.date(models.HabitCompletion.completion_date) <= end_date
            )

        return query.order_by(desc(models.HabitCompletion.completion_date)).all()

    @staticmethod
    def get_habit_progress(
        db: Session, user_id: str, habit_id: int, target_date: date | None = None
    ) -> schemas.HabitProgress | None:
        """Get progress for a habit for the current period."""
        db_habit = HabitService.get_habit(db, user_id, habit_id)
        if not db_habit:
            return None

        target_date = target_date or date.today()

        # Get the recurrence rule to determine target count
        recurrence_rule = db_habit.recurrence_rule or {}
        recurrence_type = recurrence_rule.get("type", "daily")
        target_count = recurrence_rule.get("target_count", 1)

        # Calculate period boundaries based on recurrence type
        if recurrence_type == "daily":
            # For daily habits, use a single day period
            period_start = target_date
            period_end = target_date
        elif recurrence_type == "weekly":
            # For weekly habits, use the current week (Monday to Sunday)
            days_since_monday = target_date.weekday()
            period_start = target_date - timedelta(days=days_since_monday)
            period_end = period_start + timedelta(days=6)
        elif recurrence_type == "monthly":
            # For monthly habits, use the current month
            period_start = target_date.replace(day=1)
            # Get last day of month
            if target_date.month == 12:
                period_end = target_date.replace(day=31)
            else:
                next_month = target_date.replace(month=target_date.month + 1, day=1)
                period_end = next_month - timedelta(days=1)
        else:
            # Default to weekly period
            days_since_monday = target_date.weekday()
            period_start = target_date - timedelta(days=days_since_monday)
            period_end = period_start + timedelta(days=6)

        # Get completions for this period
        completions = HabitService.get_habit_completions(
            db, user_id, habit_id, period_start, period_end
        )

        # Calculate progress
        actual_count = len(completions)
        completion_rate = (
            min(actual_count / target_count, 1.0) if target_count > 0 else 0.0
        )

        return schemas.HabitProgress(
            habit_id=habit_id,
            period_start=datetime.combine(period_start, datetime.min.time()),
            period_end=datetime.combine(period_end, datetime.min.time()),
            target_count=target_count,
            actual_count=actual_count,
            completion_rate=completion_rate,
            is_completed=actual_count >= target_count,
            completions=[
                schemas.HabitCompletion(
                    id=c.id,
                    habit_id=c.habit_id,
                    completion_time=c.completion_date,
                    completion_date=c.completion_date,
                    notes=c.notes,
                    duration_minutes=c.value,
                    intensity_rating=c.rating,
                    created_at=c.created_at,
                )
                for c in completions
            ],
        )

    @staticmethod
    def _calculate_current_streak(db: Session, habit_id: int, target_date: date) -> int:
        """Calculate the current streak for a habit."""
        # Get recent completions in reverse chronological order
        completions = (
            db.query(models.HabitCompletion)
            .filter(
                and_(
                    models.HabitCompletion.habit_id == habit_id,
                    models.HabitCompletion.completed == True,
                    func.date(models.HabitCompletion.completion_date) <= target_date,
                )
            )
            .order_by(desc(models.HabitCompletion.completion_date))
            .all()
        )

        if not completions:
            return 0

        # For simplicity, count consecutive days with completions
        streak = 0
        current_date = target_date

        for completion in completions:
            completion_date = completion.completion_date.date()

            # If there's a gap, break the streak
            if completion_date < current_date - timedelta(days=1):
                break

            if completion_date == current_date:
                streak += 1
                current_date -= timedelta(days=1)
            elif completion_date == current_date - timedelta(days=1):
                streak += 1
                current_date = completion_date - timedelta(days=1)

        return streak


# Export service instance
habit_service = HabitService()

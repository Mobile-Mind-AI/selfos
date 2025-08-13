"""Habit tracking models for building and maintaining habits."""

from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, Boolean, JSON, Time, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base


class Habit(Base):
    __tablename__ = "habits"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.uid"), nullable=False)
    
    # Habit details
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    habit_type = Column(String, nullable=False, default="build")  # build, break, maintain
    
    # Habit configuration
    frequency = Column(String, nullable=False, default="daily")  # daily, weekly, custom
    frequency_details = Column(JSON, nullable=True)  # {"days": ["mon", "wed", "fri"]} or {"times_per_week": 3}
    target_time = Column(Time, nullable=True)  # Preferred time of day
    duration_minutes = Column(Integer, nullable=True)  # Expected duration
    
    # Tracking configuration
    tracking_method = Column(String, nullable=False, default="boolean")  # boolean, count, duration, rating
    target_value = Column(Integer, nullable=True)  # For count/duration tracking
    unit = Column(String, nullable=True)  # "minutes", "pages", "glasses", etc.
    
    # Associations
    goal_id = Column(Integer, ForeignKey("goals.id"), nullable=True)
    life_area_id = Column(Integer, ForeignKey("life_areas.id"), nullable=True)
    
    # Habit chain/streak tracking
    current_streak = Column(Integer, nullable=False, default=0)
    longest_streak = Column(Integer, nullable=False, default=0)
    total_completions = Column(Integer, nullable=False, default=0)
    
    # Reminders and notifications
    reminder_enabled = Column(Boolean, nullable=False, default=False)
    reminder_time = Column(Time, nullable=True)
    reminder_message = Column(String, nullable=True)
    
    # Motivation
    motivation = Column(Text, nullable=True)  # Why this habit matters
    reward = Column(String, nullable=True)  # Self-reward for milestones
    
    # Status
    is_active = Column(Boolean, nullable=False, default=True)
    is_archived = Column(Boolean, nullable=False, default=False)
    paused_until = Column(DateTime, nullable=True)  # Temporary pause
    
    # Analytics
    success_rate = Column(JSON, nullable=True)  # {"last_7_days": 0.85, "last_30_days": 0.72}
    difficulty_rating = Column(Integer, nullable=True)  # User's rating of difficulty (1-5)
    
    # Versioning for sync
    version = Column(Integer, nullable=False, default=1)
    
    # Timestamps
    start_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="habits")
    goal = relationship("Goal", back_populates="habits")
    life_area = relationship("LifeArea", back_populates="habits")
    completions = relationship("HabitCompletion", back_populates="habit", cascade="all, delete-orphan")
    tags = relationship("Tag", secondary="habit_tags", back_populates="habits")


class HabitCompletion(Base):
    __tablename__ = "habit_completions"
    
    id = Column(Integer, primary_key=True, index=True)
    habit_id = Column(Integer, ForeignKey("habits.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String, ForeignKey("users.uid"), nullable=False)
    
    # Completion details
    completion_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    completed = Column(Boolean, nullable=False, default=True)
    
    # Tracking values (based on tracking_method)
    value = Column(Integer, nullable=True)  # For count/duration
    rating = Column(Integer, nullable=True)  # For rating method (1-5)
    
    # Optional notes
    notes = Column(Text, nullable=True)
    
    # Context
    mood = Column(String, nullable=True)  # How user felt
    difficulty = Column(Integer, nullable=True)  # How hard it was (1-5)
    location = Column(String, nullable=True)  # Where completed
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    habit = relationship("Habit", back_populates="completions")
    user = relationship("User", back_populates="habit_completions")

# Performance indexes
Index('ix_habit_user_active', Habit.user_id, Habit.is_active)
Index('ix_habit_goal', Habit.goal_id, Habit.is_active)
Index('ix_habit_life_area', Habit.life_area_id, Habit.is_active)
Index('ix_completion_habit_date', HabitCompletion.habit_id, HabitCompletion.completion_date.desc())
Index('ix_completion_user_date', HabitCompletion.user_id, HabitCompletion.completion_date.desc())

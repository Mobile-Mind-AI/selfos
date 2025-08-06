"""Goal, Project, Task, LifeArea, and Habit models."""

from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, Float, Boolean, Index, JSON, Date
from sqlalchemy.orm import relationship
from datetime import datetime, date
from db import Base


class Goal(Base):
    __tablename__ = "goals"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.uid"), nullable=False)
    life_area_id = Column(Integer, ForeignKey("life_areas.id"), nullable=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    # Status: e.g., todo, in_progress, completed
    status = Column(String, nullable=False, default='todo')
    # Progress percentage 0.0 - 100.0
    progress = Column(Float, nullable=False, default=0.0)
    # Versioning for sync
    version = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="goals")
    life_area = relationship("LifeArea", back_populates="goals")
    project = relationship("Project", back_populates="goals")
    tasks = relationship("Task", back_populates="goal", cascade="all, delete-orphan")
    habits = relationship("Habit", back_populates="goal")
    media_attachments = relationship("MediaAttachment", back_populates="goal")
    journal_entries = relationship("JournalEntry", back_populates="goal", cascade="all, delete-orphan")


class Project(Base):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.uid"), nullable=False)
    life_area_id = Column(Integer, ForeignKey("life_areas.id"), nullable=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    # Status: e.g., planning, active, on_hold, completed
    status = Column(String, nullable=False, default='planning')
    # Priority: e.g., low, medium, high
    priority = Column(String, nullable=False, default='medium')
    # Progress percentage 0.0 - 100.0
    progress = Column(Float, nullable=False, default=0.0)
    # Versioning for sync
    version = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="projects")
    life_area = relationship("LifeArea", back_populates="projects")
    goals = relationship("Goal", back_populates="project", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="project", cascade="all, delete-orphan")
    journal_entries = relationship("JournalEntry", back_populates="project", cascade="all, delete-orphan")


class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.uid"), nullable=False)
    goal_id = Column(Integer, ForeignKey("goals.id"), nullable=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    life_area_id = Column(Integer, ForeignKey("life_areas.id"), nullable=True)
    
    title = Column(String, nullable=False)
    description = Column(Text)
    
    # Status: e.g., todo, in_progress, completed
    status = Column(String, nullable=False, default='todo')
    
    # Priority: e.g., low, medium, high
    priority = Column(String, nullable=False, default='medium')
    
    # Task dependencies
    depends_on_task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True)
    
    # Progress tracking
    progress = Column(Float, nullable=False, default=0.0)
    estimated_hours = Column(Float, nullable=True)
    actual_hours = Column(Float, nullable=True)
    
    # Time tracking
    due_date = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Versioning for sync
    version = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="tasks")
    goal = relationship("Goal", back_populates="tasks")
    project = relationship("Project", back_populates="tasks")
    life_area = relationship("LifeArea", back_populates="tasks")
    
    # Self-referential relationship for dependencies
    dependent_task = relationship("Task", remote_side=[id], backref="blocking_tasks")
    
    media_attachments = relationship("MediaAttachment", back_populates="task")
    journal_entries = relationship("JournalEntry", back_populates="task", cascade="all, delete-orphan")


class LifeArea(Base):
    __tablename__ = "life_areas"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.uid"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text)
    color = Column(String)  # Hex color code for UI
    icon = Column(String)   # Icon identifier for UI
    keywords = Column(JSON)  # JSON array of keywords
    weight = Column(Float, nullable=False, default=1.0)
    priority_order = Column(Integer, nullable=False, default=0)
    is_custom = Column(Boolean, nullable=False, default=True)
    # Versioning for sync
    version = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="life_areas")
    goals = relationship("Goal", back_populates="life_area")
    projects = relationship("Project", back_populates="life_area")
    tasks = relationship("Task", back_populates="life_area")
    habits = relationship("Habit", back_populates="life_area")


class Habit(Base):
    __tablename__ = "habits"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.uid"), nullable=False)
    goal_id = Column(Integer, ForeignKey("goals.id"), nullable=True)
    life_area_id = Column(Integer, ForeignKey("life_areas.id"), nullable=True)
    
    # Basic habit information
    title = Column(String, nullable=False)
    description = Column(Text)
    
    # Recurrence configuration (stored as JSON for flexibility)
    recurrence_rule = Column(JSON, nullable=False, default={})
    # Example: {"type": "weekly", "target_count": 3, "target_type": "count"}
    # Example: {"type": "daily", "target_count": 1, "target_type": "count"}
    # Example: {"type": "monthly", "target_count": 10, "target_type": "count"}
    
    # Habit configuration
    is_active = Column(Boolean, nullable=False, default=True)
    start_date = Column(Date, nullable=False, default=date.today)
    end_date = Column(Date, nullable=True)  # Optional end date for temporary habits
    
    # UI configuration
    icon = Column(String)
    color = Column(String)
    
    # Progress tracking metadata
    current_streak = Column(Integer, nullable=False, default=0)
    best_streak = Column(Integer, nullable=False, default=0)
    total_completions = Column(Integer, nullable=False, default=0)
    
    # Versioning for sync
    version = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="habits")
    goal = relationship("Goal", back_populates="habits")
    life_area = relationship("LifeArea", back_populates="habits")
    completions = relationship("HabitCompletion", back_populates="habit", cascade="all, delete-orphan")


class HabitCompletion(Base):
    __tablename__ = "habit_completions"
    id = Column(Integer, primary_key=True, index=True)
    habit_id = Column(Integer, ForeignKey("habits.id"), nullable=False)
    
    # When the habit was completed
    completion_date = Column(Date, nullable=False, default=date.today)
    completion_time = Column(DateTime, default=datetime.utcnow)
    
    # Optional metadata about the completion
    notes = Column(Text)
    duration_minutes = Column(Integer)  # For habits that track time (e.g., "meditate for 10 minutes")
    intensity_rating = Column(Integer)  # Optional 1-10 rating
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    habit = relationship("Habit", back_populates="completions")


class JournalEntry(Base):
    __tablename__ = "journal_entries"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.uid"), nullable=False)
    
    # Content
    content = Column(Text, nullable=False)
    
    # Optional associations - can be attached to project, goal, or task
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    goal_id = Column(Integer, ForeignKey("goals.id"), nullable=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True)
    
    # Versioning for sync
    version = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="journal_entries")
    project = relationship("Project", back_populates="journal_entries")
    goal = relationship("Goal", back_populates="journal_entries")
    task = relationship("Task", back_populates="journal_entries")


# Performance indexes for Goal model
Index('ix_goals_user_created', Goal.user_id, Goal.created_at.desc())
Index('ix_goals_user_status', Goal.user_id, Goal.status)
Index('ix_goals_life_area_created', Goal.life_area_id, Goal.created_at.desc())
Index('ix_goals_project_created', Goal.project_id, Goal.created_at.desc())

# Performance indexes for Project model
Index('ix_projects_user_created', Project.user_id, Project.created_at.desc())
Index('ix_projects_user_status', Project.user_id, Project.status)
Index('ix_projects_user_priority', Project.user_id, Project.priority)
Index('ix_projects_life_area_created', Project.life_area_id, Project.created_at.desc())

# Performance indexes for Task model
Index('ix_tasks_user_created', Task.user_id, Task.created_at.desc())
Index('ix_tasks_user_status', Task.user_id, Task.status)
Index('ix_tasks_goal_created', Task.goal_id, Task.created_at.desc())
Index('ix_tasks_project_created', Task.project_id, Task.created_at.desc())
Index('ix_tasks_due_date', Task.due_date)
Index('ix_tasks_completed', Task.completed_at)

# Performance indexes for LifeArea model
Index('ix_life_areas_user_created', LifeArea.user_id, LifeArea.created_at.desc())
Index('ix_life_areas_user_name', LifeArea.user_id, LifeArea.name)

# Performance indexes for Habit model
Index('ix_habits_user_created', Habit.user_id, Habit.created_at.desc())
Index('ix_habits_user_active', Habit.user_id, Habit.is_active)
Index('ix_habits_goal_created', Habit.goal_id, Habit.created_at.desc())
Index('ix_habits_life_area_created', Habit.life_area_id, Habit.created_at.desc())

# Performance indexes for HabitCompletion model
Index('ix_habit_completions_habit_id', HabitCompletion.habit_id)
Index('ix_habit_completions_date', HabitCompletion.completion_date.desc())
Index('ix_habit_completions_habit_date', HabitCompletion.habit_id, HabitCompletion.completion_date.desc())

# Performance indexes for JournalEntry model
Index('ix_journal_entries_user_created', JournalEntry.user_id, JournalEntry.created_at.desc())
Index('ix_journal_entries_project_created', JournalEntry.project_id, JournalEntry.created_at.desc())
Index('ix_journal_entries_goal_created', JournalEntry.goal_id, JournalEntry.created_at.desc())
Index('ix_journal_entries_task_created', JournalEntry.task_id, JournalEntry.created_at.desc())

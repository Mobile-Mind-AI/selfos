"""Goal, Project, Task, and LifeArea models."""

from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, Float, Boolean, Index
from sqlalchemy.orm import relationship
from datetime import datetime
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
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="goals")
    life_area = relationship("LifeArea", back_populates="goals")
    project = relationship("Project", back_populates="goals")
    tasks = relationship("Task", back_populates="goal", cascade="all, delete-orphan")
    media_attachments = relationship("MediaAttachment", back_populates="goal")


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
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="projects")
    life_area = relationship("LifeArea", back_populates="projects")
    goals = relationship("Goal", back_populates="project", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="project", cascade="all, delete-orphan")


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


class LifeArea(Base):
    __tablename__ = "life_areas"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.uid"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text)
    color = Column(String)  # Hex color code for UI
    icon = Column(String)   # Icon identifier for UI
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="life_areas")
    goals = relationship("Goal", back_populates="life_area")
    projects = relationship("Project", back_populates="life_area")
    tasks = relationship("Task", back_populates="life_area")


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
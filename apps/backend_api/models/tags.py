"""Tag system models for flexible cross-context entity grouping."""

from sqlalchemy import Column, String, Integer, ForeignKey, Table, DateTime, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from db import Base

# Association tables for many-to-many relationships
project_tags = Table(
    'project_tags',
    Base.metadata,
    Column('project_id', Integer, ForeignKey('projects.id', ondelete='CASCADE'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tags.id', ondelete='CASCADE'), primary_key=True)
)

goal_tags = Table(
    'goal_tags',
    Base.metadata,
    Column('goal_id', Integer, ForeignKey('goals.id', ondelete='CASCADE'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tags.id', ondelete='CASCADE'), primary_key=True)
)

task_tags = Table(
    'task_tags',
    Base.metadata,
    Column('task_id', Integer, ForeignKey('tasks.id', ondelete='CASCADE'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tags.id', ondelete='CASCADE'), primary_key=True)
)

habit_tags = Table(
    'habit_tags',
    Base.metadata,
    Column('habit_id', Integer, ForeignKey('habits.id', ondelete='CASCADE'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tags.id', ondelete='CASCADE'), primary_key=True)
)

journal_entry_tags = Table(
    'journal_entry_tags',
    Base.metadata,
    Column('journal_entry_id', Integer, ForeignKey('journal_entries.id', ondelete='CASCADE'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tags.id', ondelete='CASCADE'), primary_key=True)
)


class Tag(Base):
    __tablename__ = "tags"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.uid"), nullable=False)
    name = Column(String, nullable=False)
    color = Column(String)  # Hex color code for UI (e.g., "#FF5722")
    
    # Versioning for sync
    version = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="tags")
    
    # Many-to-many relationships with all entities
    projects = relationship("Project", secondary=project_tags, back_populates="tags")
    goals = relationship("Goal", secondary=goal_tags, back_populates="tags") 
    tasks = relationship("Task", secondary=task_tags, back_populates="tags")
    habits = relationship("Habit", secondary=habit_tags, back_populates="tags")
    journal_entries = relationship("JournalEntry", secondary=journal_entry_tags, back_populates="tags")
    
    # Ensure unique tag names per user
    __table_args__ = (
        Index('uq_user_tag_name', 'user_id', 'name', unique=True),
    )

from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, Float, JSON
from sqlalchemy.orm import relationship
import db
Base = db.Base
from datetime import datetime

class User(Base):
    __tablename__ = "users"
    uid = Column(String, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    
    # Relationships
    goals = relationship("Goal", back_populates="user", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="user", cascade="all, delete-orphan")
    life_areas = relationship("LifeArea", back_populates="user", cascade="all, delete-orphan")
    media_attachments = relationship("MediaAttachment", back_populates="user", cascade="all, delete-orphan")
    memory_items = relationship("MemoryItem", back_populates="user", cascade="all, delete-orphan")

class Goal(Base):
    __tablename__ = "goals"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.uid"), nullable=False)
    life_area_id = Column(Integer, ForeignKey("life_areas.id"), nullable=True)
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
    tasks = relationship("Task", back_populates="goal", cascade="all, delete-orphan")
    media_attachments = relationship("MediaAttachment", back_populates="goal")

class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, index=True)
    goal_id = Column(Integer, ForeignKey("goals.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.uid"), nullable=False)
    life_area_id = Column(Integer, ForeignKey("life_areas.id"), nullable=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    # When task is due
    due_date = Column(DateTime)
    # Expected duration in minutes
    duration = Column(Integer)
    # Status: todo, in_progress, completed
    status = Column(String, nullable=False, default='todo')
    # Progress percentage 0.0 - 100.0
    progress = Column(Float, nullable=False, default=0.0)
    # List of prerequisite task IDs (kept as JSON for simplicity)
    dependencies = Column(JSON, nullable=False, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="tasks")
    goal = relationship("Goal", back_populates="tasks")
    life_area = relationship("LifeArea", back_populates="tasks")
    media_attachments = relationship("MediaAttachment", back_populates="task")

class LifeArea(Base):
    __tablename__ = "life_areas"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.uid"), nullable=False)
    name = Column(String, nullable=False)
    # Weight as percentage importance (0-100)
    weight = Column(Integer, default=10, nullable=False)
    # Optional UI icon identifier
    icon = Column(String)
    # UI color preference (hex color or color name)
    color = Column(String)
    # Description of this life area
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="life_areas")
    goals = relationship("Goal", back_populates="life_area")
    tasks = relationship("Task", back_populates="life_area")

class MediaAttachment(Base):
    __tablename__ = "media_attachments"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.uid"), nullable=False)
    # What this attachment is linked to
    goal_id = Column(Integer, ForeignKey("goals.id"), nullable=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True)
    # File information
    filename = Column(String, nullable=False)
    original_filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)  # Size in bytes
    mime_type = Column(String, nullable=False)  # e.g., image/jpeg, video/mp4, audio/mpeg
    file_type = Column(String, nullable=False)  # image, video, audio, document
    # Optional metadata
    title = Column(String)  # User-defined title
    description = Column(Text)  # User description for storytelling
    duration = Column(Integer)  # Duration in seconds for video/audio
    width = Column(Integer)  # Image/video width
    height = Column(Integer)  # Image/video height
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="media_attachments")
    goal = relationship("Goal", back_populates="media_attachments")
    task = relationship("Task", back_populates="media_attachments")

class MemoryItem(Base):
    __tablename__ = "memory_items"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.uid"), nullable=False)
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="memory_items")
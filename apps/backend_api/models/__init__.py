"""
Models package for SelfOS Backend API

This package contains all SQLAlchemy models organized by domain.
"""

# Import Base first
from .base import Base

# Import User model
from .user import User

# Import all domain models
from .goals import Goal
from .projects import Project
from .tasks import Task
from .life_areas import LifeArea
from .preferences import UserPreferences, UserPreferencesHistory
from .assistant import AssistantProfile
from .conversation import ConversationLog, ConversationSession, IntentFeedback
from .content import MediaAttachment, MemoryItem, StorySession, FeedbackLog
from .entities import (
    EntityType, Entity, EntityRelationship,
    GoalEntity, ProjectEntity, TaskEntity
)
from .journal import JournalEntry
from .habits import Habit, HabitCompletion
from .tags import Tag

# Export all models for easy importing
__all__ = [
    # Base
    'Base',
    
    # User
    'User',
    
    # Goals & Planning
    'Goal',
    'Project', 
    'Task',
    'LifeArea',
    
    # User Configuration
    'UserPreferences',
    'UserPreferencesHistory',
    'AssistantProfile',
    
    # Conversation & AI
    'ConversationLog',
    'ConversationSession',
    'IntentFeedback',
    
    # Content & Memory
    'MemoryItem',
    'StorySession',
    'FeedbackLog',
    'MediaAttachment',
    
    # Habits & Journal
    'JournalEntry',
    'Habit',
    'HabitCompletion',
    'Tag',
    
    # Knowledge Graph
    'EntityType',
    'Entity',
    'EntityRelationship',
    'GoalEntity',
    'ProjectEntity',
    'TaskEntity',
]

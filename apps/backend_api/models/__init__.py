"""
Models package for SelfOS Backend API

This package contains all SQLAlchemy models organized by domain.
"""

# Import associations module to ensure all association tables are available
from . import associations
from .assistant import AssistantProfile
from .assistant_permissions import AssistantPermission, PermissionLevel

# Import Base first
from .base import Base
from .content import FeedbackLog, MediaAttachment, MemoryItem, StorySession
from .conversation import ConversationLog, ConversationSession, IntentFeedback
from .entities import (
    Entity,
    EntityRelationship,
    EntityType,
    GoalEntity,
    ProjectEntity,
    TaskEntity,
)

# Import all domain models
from .goals import Goal
from .habits import Habit, HabitCompletion
from .journal import JournalEntry
from .life_areas import LifeArea
from .preferences import UserPreferences, UserPreferencesHistory
from .projects import Project
from .tags import Tag
from .tasks import Task

# Import User model
from .user import User

# Export all models for easy importing
__all__ = [
    # Base
    "Base",
    # User
    "User",
    # Goals & Planning
    "Goal",
    "Project",
    "Task",
    "LifeArea",
    # User Configuration
    "UserPreferences",
    "UserPreferencesHistory",
    "AssistantProfile",
    "AssistantPermission",
    "PermissionLevel",
    # Conversation & AI
    "ConversationLog",
    "ConversationSession",
    "IntentFeedback",
    # Content & Memory
    "MemoryItem",
    "StorySession",
    "FeedbackLog",
    "MediaAttachment",
    # Habits & Journal
    "JournalEntry",
    "Habit",
    "HabitCompletion",
    "Tag",
    # Knowledge Graph
    "EntityType",
    "Entity",
    "EntityRelationship",
    "GoalEntity",
    "ProjectEntity",
    "TaskEntity",
]

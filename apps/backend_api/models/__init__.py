"""
Models package for SelfOS Backend API

This package contains all SQLAlchemy models organized by domain:
- base: Common imports and base setup
- user: User model and user-related models  
- goals: Goal, Project, Task models
- content: Media, Memory, Story models
- onboarding: Onboarding, PersonalProfile, CustomLifeArea models
- analytics: Analytics and feedback models
"""

# Import db and Base first
from db import Base

# Import all models to ensure they are registered with SQLAlchemy
from .user import User, UserPreferences
from .goals import Goal, Project, Task, LifeArea
from .content import MediaAttachment, MemoryItem, StorySession, FeedbackLog
from .onboarding import PersonalProfile, CustomLifeArea, OnboardingAnalytics, AssistantProfile, OnboardingState
from .conversation import ConversationLog, ConversationSession, IntentFeedback

# Export all models for easy importing
__all__ = [
    'Base',
    'User', 'UserPreferences',
    'Goal', 'Project', 'Task', 'LifeArea', 
    'MediaAttachment', 'MemoryItem', 'StorySession', 'FeedbackLog',
    'PersonalProfile', 'CustomLifeArea', 'OnboardingAnalytics', 'AssistantProfile', 'OnboardingState',
    'ConversationLog', 'ConversationSession', 'IntentFeedback'
]
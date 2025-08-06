"""
Services package for business logic and AI-oriented data processing.

This package contains various services that handle core business logic
and provide intelligent features for the SelfOS platform.
"""

# Import business logic services
from .goal_service import goal_service
from .project_service import project_service
from .task_service import task_service
from .habit_service import habit_service
from .tag_service import tag_service
from .journal_service import journal_service
from .preferences_service import preferences_service

# Import AI-oriented services
from . import progress
from . import storytelling
from . import notifications
from . import memory
from . import enhanced_memory

__all__ = [
    # Business logic services
    'goal_service',
    'project_service', 
    'task_service',
    'habit_service',
    'tag_service',
    'journal_service',
    'preferences_service',
    # AI services
    'progress',
    'storytelling',
    'notifications',
    'memory',
    'enhanced_memory'
]

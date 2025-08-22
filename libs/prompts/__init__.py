"""
SelfOS Prompt Templates Library

This module contains all AI prompt templates used throughout the SelfOS system
for goal decomposition, task generation, and conversational interactions.
"""

from .conversation import ConversationPrompts
from .goal_decomposition import GoalDecompositionPrompts
from .task_generation import TaskGenerationPrompts

__version__ = "0.1.0"
__all__ = ["GoalDecompositionPrompts", "TaskGenerationPrompts", "ConversationPrompts"]

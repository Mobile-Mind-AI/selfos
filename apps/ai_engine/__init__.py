"""
SelfOS AI Engine

This module provides AI orchestration services for goal decomposition,
task generation, and conversational interactions using LLMs.
"""

from orchestrator import AIOrchestrator
from models import *
from config import AIConfig

__version__ = "0.1.0"
__all__ = ["AIOrchestrator", "AIConfig"]
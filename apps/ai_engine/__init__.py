"""
SelfOS AI Engine

This module provides AI orchestration services for goal decomposition,
task generation, and conversational interactions using LLMs.
"""

import importlib.util

# Import AIConfig from current directory to avoid conflicts
import os

from models import *
from orchestrator import AIOrchestrator

current_dir = os.path.dirname(__file__)
config_path = os.path.join(current_dir, "config.py")
config_spec = importlib.util.spec_from_file_location("ai_config", config_path)
ai_config_module = importlib.util.module_from_spec(config_spec)
config_spec.loader.exec_module(ai_config_module)
AIConfig = ai_config_module.AIConfig

__version__ = "0.1.0"
__all__ = ["AIOrchestrator", "AIConfig"]

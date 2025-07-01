"""
Pydantic schemas for the SelfOS backend API.
"""

# Import all schemas from the main schemas.py file in parent directory
import sys
import os

# Add parent directory to path to import schemas.py
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Import specific schemas from parent schemas.py to avoid circular imports
try:
    # Import the parent schemas module by file path to avoid name conflicts
    import importlib.util
    schemas_path = os.path.join(parent_dir, 'schemas.py')
    spec = importlib.util.spec_from_file_location("parent_schemas", schemas_path)
    parent_schemas = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(parent_schemas)
    
    # Import all schema classes that are used across the application
    # Authentication schemas
    RegisterRequest = parent_schemas.RegisterRequest
    LoginRequest = parent_schemas.LoginRequest
    TokenResponse = parent_schemas.TokenResponse
    AuthResponse = parent_schemas.AuthResponse
    User = parent_schemas.User
    UserOut = parent_schemas.UserOut
    UserCreate = parent_schemas.UserCreate
    
    # Goal schemas
    Goal = parent_schemas.Goal
    GoalCreate = parent_schemas.GoalCreate
    GoalOut = parent_schemas.GoalOut
    
    # Task schemas  
    Task = parent_schemas.Task
    TaskCreate = parent_schemas.TaskCreate
    TaskOut = parent_schemas.TaskOut
    
    # Project schemas
    Project = parent_schemas.Project
    ProjectCreate = parent_schemas.ProjectCreate
    ProjectOut = parent_schemas.ProjectOut
    
    # Life Area schemas
    LifeArea = parent_schemas.LifeArea
    LifeAreaCreate = parent_schemas.LifeAreaCreate
    LifeAreaUpdate = parent_schemas.LifeAreaUpdate
    LifeAreaOut = parent_schemas.LifeAreaOut
    
    # Media Attachment schemas
    MediaAttachment = parent_schemas.MediaAttachment
    MediaAttachmentCreate = parent_schemas.MediaAttachmentCreate
    MediaAttachmentUpdate = parent_schemas.MediaAttachmentUpdate
    MediaAttachmentOut = parent_schemas.MediaAttachmentOut
    
    # User Preferences schemas
    UserPreferencesCreate = parent_schemas.UserPreferencesCreate
    UserPreferencesUpdate = parent_schemas.UserPreferencesUpdate
    UserPreferencesOut = parent_schemas.UserPreferencesOut
    
    # User Preferences base model
    UserPreferences = parent_schemas.UserPreferences
    
    # Feedback Log schemas
    FeedbackLog = parent_schemas.FeedbackLog
    FeedbackLogCreate = parent_schemas.FeedbackLogCreate
    FeedbackLogUpdate = parent_schemas.FeedbackLogUpdate
    FeedbackLogSummary = parent_schemas.FeedbackLogSummary
    
    # Story Session schemas
    StorySession = parent_schemas.StorySession
    StorySessionCreate = parent_schemas.StorySessionCreate
    StorySessionUpdate = parent_schemas.StorySessionUpdate
    
    # Export all imported schemas
    __all__ = [
        'RegisterRequest', 'LoginRequest', 'TokenResponse', 'AuthResponse', 'User', 'UserOut', 'UserCreate',
        'Goal', 'GoalCreate', 'GoalOut',
        'Task', 'TaskCreate', 'TaskOut', 
        'Project', 'ProjectCreate', 'ProjectOut',
        'LifeArea', 'LifeAreaCreate', 'LifeAreaUpdate', 'LifeAreaOut',
        'MediaAttachment', 'MediaAttachmentCreate', 'MediaAttachmentUpdate', 'MediaAttachmentOut',
        'UserPreferences', 'UserPreferencesCreate', 'UserPreferencesUpdate', 'UserPreferencesOut',
        'FeedbackLog', 'FeedbackLogCreate', 'FeedbackLogUpdate', 'FeedbackLogSummary',
        'StorySession', 'StorySessionCreate', 'StorySessionUpdate'
    ]
    
except (ImportError, AttributeError) as e:
    # Fallback: define minimal schemas if parent import fails
    from pydantic import BaseModel
    from typing import Optional
    
    class RegisterRequest(BaseModel):
        username: Optional[str] = None
        password: Optional[str] = None
    
    class LoginRequest(BaseModel):
        username: str
        password: str
    
    class TokenResponse(BaseModel):
        access_token: str
        token_type: str = "bearer"
    
    class AuthResponse(BaseModel):
        token: str
        user: dict
    
    class User(BaseModel):
        uid: str
        email: str
    
    class UserOut(BaseModel):
        uid: str
        email: str

# Import from local schema files
from .intent_schemas import *
from .assistant_schemas import *
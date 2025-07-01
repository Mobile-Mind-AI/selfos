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
    
    # Import specific schema classes that are needed
    RegisterRequest = parent_schemas.RegisterRequest
    LoginRequest = parent_schemas.LoginRequest
    TokenResponse = parent_schemas.TokenResponse
    AuthResponse = parent_schemas.AuthResponse
    User = parent_schemas.User
    UserOut = parent_schemas.UserOut
    
    # Import other commonly used schemas
    GoalCreate = parent_schemas.GoalCreate
    GoalUpdate = parent_schemas.GoalUpdate
    GoalOut = parent_schemas.GoalOut
    TaskCreate = parent_schemas.TaskCreate
    TaskUpdate = parent_schemas.TaskUpdate
    TaskOut = parent_schemas.TaskOut
    ProjectCreate = parent_schemas.ProjectCreate
    ProjectUpdate = parent_schemas.ProjectUpdate
    ProjectOut = parent_schemas.ProjectOut
    
    # Export all imported schemas
    __all__ = [
        'RegisterRequest', 'LoginRequest', 'TokenResponse', 'AuthResponse', 'User', 'UserOut',
        'GoalCreate', 'GoalUpdate', 'GoalOut',
        'TaskCreate', 'TaskUpdate', 'TaskOut', 
        'ProjectCreate', 'ProjectUpdate', 'ProjectOut'
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
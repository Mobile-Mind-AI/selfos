"""
Pydantic schemas for the SelfOS backend API.
"""

# Import all schemas from the main schemas.py file and intent_schemas.py  
import sys
import os

# Get the parent directory to import schemas.py
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

# Import from schemas.py in parent directory
try:
    import schemas as parent_schemas
    # Re-export all classes from parent schemas module
    for name in dir(parent_schemas):
        if not name.startswith('_'):
            globals()[name] = getattr(parent_schemas, name)
except ImportError:
    pass

# Import from local schema files
from .intent_schemas import *
from .assistant_schemas import *
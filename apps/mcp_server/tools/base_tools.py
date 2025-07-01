"""
Base Tools Handler

Base class for MCP tool handlers with common functionality
for database access, authentication, and error handling.
"""

import logging
from typing import Dict, List, Any, Optional
from abc import ABC, abstractmethod

# Import database dependencies from backend_api
import sys
import os

# Add the backend_api path to sys.path
backend_api_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../backend_api'))
if backend_api_path not in sys.path:
    sys.path.insert(0, backend_api_path)

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class BaseToolsHandler(ABC):
    """Base class for MCP tool handlers."""
    
    def __init__(self):
        """Initialize the base tools handler."""
        self.tool_prefix = ""
    
    @abstractmethod
    async def list_tools(self) -> List[Dict]:
        """Return list of tools provided by this handler."""
        pass
    
    @abstractmethod
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict:
        """Execute a tool with given arguments."""
        pass
    
    def get_db_session(self):
        """Get a database session."""
        try:
            # Import here to avoid circular imports
            from db import SessionLocal
            return SessionLocal()
        except ImportError as e:
            logger.error(f"Could not import database session: {e}")
            return None
    
    async def validate_user_access(self, user_id: str, db=None) -> bool:
        """Validate that user exists and has access."""
        try:
            # For now, just validate that user_id is provided
            # In production, this should check against the database
            return bool(user_id and len(user_id) > 0)
        except Exception as e:
            logger.error(f"User validation error: {e}")
            return False
    
    def handle_error(self, error: Exception, operation: str) -> Dict:
        """Handle errors consistently across all tools."""
        logger.error(f"Error in {operation}: {error}")
        return {
            "error": str(error),
            "operation": operation,
            "success": False
        }
    
    def format_success_response(self, data: Any, operation: str) -> Dict:
        """Format successful response consistently."""
        return {
            "success": True,
            "operation": operation,
            "data": data
        }
    
    def validate_required_args(self, arguments: Dict, required_args: List[str]) -> Optional[str]:
        """Validate that required arguments are present."""
        missing_args = [arg for arg in required_args if arg not in arguments]
        if missing_args:
            return f"Missing required arguments: {', '.join(missing_args)}"
        return None
    
    def sanitize_arguments(self, arguments: Dict) -> Dict:
        """Sanitize arguments to prevent injection attacks."""
        # Basic sanitization - remove potentially dangerous characters
        sanitized = {}
        for key, value in arguments.items():
            if isinstance(value, str):
                # Remove potentially dangerous SQL patterns
                dangerous_patterns = ["DROP", "DELETE", "INSERT", "UPDATE", "SELECT", "--", ";"]
                sanitized_value = value
                for pattern in dangerous_patterns:
                    if pattern.upper() in value.upper():
                        logger.warning(f"Potentially dangerous pattern '{pattern}' found in argument '{key}'")
                        sanitized_value = value.replace(pattern.upper(), "").replace(pattern.lower(), "")
                sanitized[key] = sanitized_value
            else:
                sanitized[key] = value
        return sanitized
"""
MCP Authentication Provider

Handles authentication for MCP client connections using Firebase tokens
and API keys, ensuring secure access to SelfOS resources.
"""

import logging
from typing import Dict, Optional, Tuple
import json

try:
    from firebase_admin import auth, credentials
    import firebase_admin
    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False

logger = logging.getLogger(__name__)


class MCPAuthProvider:
    """Authentication provider for MCP connections."""
    
    def __init__(self):
        """Initialize the authentication provider."""
        self._firebase_initialized = False
        self._initialize_firebase()
    
    def _initialize_firebase(self):
        """Initialize Firebase Admin SDK if not already done."""
        if not FIREBASE_AVAILABLE:
            logger.warning("Firebase Admin SDK not available - authentication disabled")
            return
        
        try:
            # Check if Firebase is already initialized
            firebase_admin.get_app()
            self._firebase_initialized = True
            logger.info("Firebase Admin SDK already initialized")
        except ValueError:
            # Firebase not initialized yet
            try:
                # Try to initialize with default credentials
                cred = credentials.ApplicationDefault()
                firebase_admin.initialize_app(cred)
                self._firebase_initialized = True
                logger.info("Firebase Admin SDK initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Firebase Admin SDK: {e}")
                self._firebase_initialized = False
    
    async def authenticate_client(
        self, 
        credentials_data: Dict
    ) -> Tuple[bool, Optional[str], Optional[Dict]]:
        """
        Authenticate MCP client connection.
        
        Args:
            credentials_data: Authentication credentials
            
        Returns:
            Tuple of (success, user_id, user_info)
        """
        auth_type = credentials_data.get("type")
        
        if auth_type == "firebase_token":
            return await self._authenticate_firebase_token(credentials_data)
        elif auth_type == "api_key":
            return await self._authenticate_api_key(credentials_data)
        else:
            logger.warning(f"Unknown authentication type: {auth_type}")
            return False, None, None
    
    async def _authenticate_firebase_token(
        self, 
        credentials_data: Dict
    ) -> Tuple[bool, Optional[str], Optional[Dict]]:
        """Authenticate using Firebase ID token."""
        if not self._firebase_initialized:
            logger.error("Firebase not initialized - cannot authenticate token")
            return False, None, None
        
        token = credentials_data.get("token")
        if not token:
            logger.warning("No token provided for Firebase authentication")
            return False, None, None
        
        try:
            # Verify the Firebase ID token
            decoded_token = auth.verify_id_token(token)
            user_id = decoded_token["uid"]
            
            user_info = {
                "uid": user_id,
                "email": decoded_token.get("email"),
                "email_verified": decoded_token.get("email_verified", False),
                "name": decoded_token.get("name"),
                "picture": decoded_token.get("picture"),
                "auth_provider": "firebase"
            }
            
            logger.info(f"Successfully authenticated Firebase user: {user_id}")
            return True, user_id, user_info
            
        except auth.InvalidIdTokenError:
            logger.warning("Invalid Firebase ID token")
            return False, None, None
        except auth.ExpiredIdTokenError:
            logger.warning("Expired Firebase ID token")
            return False, None, None
        except Exception as e:
            logger.error(f"Firebase authentication error: {e}")
            return False, None, None
    
    async def _authenticate_api_key(
        self, 
        credentials_data: Dict
    ) -> Tuple[bool, Optional[str], Optional[Dict]]:
        """Authenticate using API key (for development/testing)."""
        api_key = credentials_data.get("key")
        if not api_key:
            logger.warning("No API key provided")
            return False, None, None
        
        # For now, we'll validate against a simple pattern
        # In production, this should validate against a secure API key store
        if api_key.startswith("sk-selfos-"):
            # Extract user_id from API key (simplified approach)
            try:
                # Format: sk-selfos-{user_id}-{random}
                parts = api_key.split("-")
                if len(parts) >= 3:
                    user_id = parts[2]
                    
                    user_info = {
                        "uid": user_id,
                        "auth_provider": "api_key",
                        "api_key": api_key[:20] + "..."  # Truncated for logging
                    }
                    
                    logger.info(f"Successfully authenticated API key user: {user_id}")
                    return True, user_id, user_info
            except Exception as e:
                logger.error(f"Error parsing API key: {e}")
        
        logger.warning("Invalid API key format")
        return False, None, None
    
    async def validate_permissions(
        self, 
        user_id: str, 
        resource: str, 
        action: str
    ) -> bool:
        """
        Validate if user has permission for specific resource/action.
        
        Args:
            user_id: User identifier
            resource: Resource being accessed (e.g., "goals", "projects")
            action: Action being performed (e.g., "read", "write", "delete")
            
        Returns:
            True if permission is granted
        """
        # For now, we'll implement basic permission logic
        # In production, this should check against a proper authorization system
        
        # All authenticated users can read their own data
        if action in ["read", "list"]:
            return True
        
        # All authenticated users can create/update their own data
        if action in ["create", "update"]:
            return True
        
        # Delete operations might be restricted
        if action == "delete":
            # Allow deletion of own data
            return True
        
        # AI operations require special permission (for now, allow all)
        if resource == "ai":
            return True
        
        logger.warning(f"Permission denied: {user_id} -> {resource}:{action}")
        return False
    
    def create_session_context(
        self, 
        user_id: str, 
        user_info: Dict,
        client_info: Optional[Dict] = None
    ) -> Dict:
        """Create session context for authenticated user."""
        return {
            "user_id": user_id,
            "user_info": user_info,
            "client_info": client_info or {},
            "authenticated_at": logger.info("Session context created"),
            "permissions": {
                "read": True,
                "write": True,
                "delete": True,
                "ai": True
            }
        }
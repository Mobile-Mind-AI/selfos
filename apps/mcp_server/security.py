"""
MCP Security and Permissions

Security management and permission system for MCP server operations,
ensuring safe and controlled access to SelfOS resources.
"""

import logging
from typing import Dict, List, Optional, Set, Tuple
from enum import Enum
from dataclasses import dataclass, field
import fnmatch

logger = logging.getLogger(__name__)


class PermissionLevel(Enum):
    """Permission levels for MCP operations."""
    READ_ONLY = "read_only"
    READ_WRITE = "read_write"
    ADMIN = "admin"


@dataclass
class PermissionRule:
    """Individual permission rule."""
    pattern: str
    allowed: bool = True
    description: str = ""


@dataclass
class ClientPermissions:
    """Permissions for a specific client."""
    level: PermissionLevel
    allowed_tools: List[str] = field(default_factory=list)
    allowed_resources: List[str] = field(default_factory=list)
    denied_tools: List[str] = field(default_factory=list)
    denied_resources: List[str] = field(default_factory=list)
    custom_rules: List[PermissionRule] = field(default_factory=list)


class MCPPermissions:
    """MCP permission management system."""
    
    # Default permission configurations
    PERMISSION_CONFIGS = {
        PermissionLevel.READ_ONLY: ClientPermissions(
            level=PermissionLevel.READ_ONLY,
            allowed_tools=[
                "goals_list", "goals_get", "goals_search",
                "projects_list", "projects_get", "projects_progress", "projects_timeline",
                "tasks_list", "tasks_get", "tasks_search",
                "ai_analyze_progress"
            ],
            allowed_resources=[
                "user_profile", "goal_context", "project_context", "daily_summary"
            ]
        ),
        
        PermissionLevel.READ_WRITE: ClientPermissions(
            level=PermissionLevel.READ_WRITE,
            allowed_tools=[
                "goals_*", "projects_*", "tasks_*",
                "ai_decompose_goal", "ai_suggest_tasks", "ai_analyze_progress"
            ],
            allowed_resources=["*"]
        ),
        
        PermissionLevel.ADMIN: ClientPermissions(
            level=PermissionLevel.ADMIN,
            allowed_tools=["*"],
            allowed_resources=["*"]
        )
    }
    
    def __init__(self):
        """Initialize the permissions system."""
        self.client_permissions: Dict[str, ClientPermissions] = {}
        self.rate_limits: Dict[str, Dict] = {}
    
    def get_client_permissions(
        self, 
        client_id: str, 
        default_level: PermissionLevel = PermissionLevel.READ_WRITE
    ) -> ClientPermissions:
        """Get permissions for a client."""
        if client_id in self.client_permissions:
            return self.client_permissions[client_id]
        
        # Return default permissions
        return self.PERMISSION_CONFIGS[default_level]
    
    def set_client_permissions(
        self, 
        client_id: str, 
        permissions: ClientPermissions
    ):
        """Set permissions for a specific client."""
        self.client_permissions[client_id] = permissions
        logger.info(f"Updated permissions for client {client_id}: {permissions.level}")
    
    async def check_tool_permission(
        self,
        user_id: str,
        client_id: str,
        tool_name: str,
        arguments: Dict
    ) -> bool:
        """
        Check if client has permission to use a specific tool.
        
        Args:
            user_id: User identifier
            client_id: Client identifier
            tool_name: Name of the tool being called
            arguments: Tool arguments
            
        Returns:
            True if permission is granted
        """
        permissions = self.get_client_permissions(client_id)
        
        # Check explicit denials first
        if self._matches_patterns(tool_name, permissions.denied_tools):
            logger.warning(f"Tool {tool_name} explicitly denied for client {client_id}")
            return False
        
        # Check allowed tools
        if self._matches_patterns(tool_name, permissions.allowed_tools):
            return True
        
        # Check custom rules
        for rule in permissions.custom_rules:
            if fnmatch.fnmatch(tool_name, rule.pattern):
                if not rule.allowed:
                    logger.warning(f"Tool {tool_name} denied by custom rule: {rule.description}")
                return rule.allowed
        
        logger.warning(f"Tool {tool_name} not allowed for client {client_id}")
        return False
    
    async def check_resource_permission(
        self,
        user_id: str,
        client_id: str,
        resource_uri: str
    ) -> bool:
        """
        Check if client has permission to access a specific resource.
        
        Args:
            user_id: User identifier
            client_id: Client identifier
            resource_uri: URI of the resource being accessed
            
        Returns:
            True if permission is granted
        """
        permissions = self.get_client_permissions(client_id)
        
        # Extract resource type from URI
        resource_type = self._extract_resource_type(resource_uri)
        
        # Check explicit denials first
        if self._matches_patterns(resource_type, permissions.denied_resources):
            logger.warning(f"Resource {resource_type} explicitly denied for client {client_id}")
            return False
        
        # Check allowed resources
        if self._matches_patterns(resource_type, permissions.allowed_resources):
            return True
        
        logger.warning(f"Resource {resource_type} not allowed for client {client_id}")
        return False
    
    def _matches_patterns(self, item: str, patterns: List[str]) -> bool:
        """Check if item matches any of the given patterns."""
        for pattern in patterns:
            if pattern == "*" or fnmatch.fnmatch(item, pattern):
                return True
        return False
    
    def _extract_resource_type(self, resource_uri: str) -> str:
        """Extract resource type from URI."""
        # Example: selfos://users/123/profile -> user_profile
        # Example: selfos://goals/456/context -> goal_context
        
        if resource_uri.startswith("selfos://"):
            path_parts = resource_uri[9:].split("/")
            if len(path_parts) >= 2:
                # Convert "users" to "user" for consistency with allowed_resources
                resource_prefix = path_parts[0].rstrip('s') if path_parts[0].endswith('s') else path_parts[0]
                return f"{resource_prefix}_{path_parts[-1]}"
        
        return "unknown"
    
    async def validate_rate_limit(
        self,
        client_id: str,
        operation: str,
        window_seconds: int = 60
    ) -> bool:
        """
        Validate rate limiting for client operations.
        
        Args:
            client_id: Client identifier
            operation: Operation being performed
            window_seconds: Rate limit window in seconds
            
        Returns:
            True if within rate limit
        """
        # For now, implement simple in-memory rate limiting
        # In production, this should use Redis or similar
        
        import time
        current_time = time.time()
        
        if client_id not in self.rate_limits:
            self.rate_limits[client_id] = {}
        
        client_limits = self.rate_limits[client_id]
        
        if operation not in client_limits:
            client_limits[operation] = []
        
        # Clean old entries
        client_limits[operation] = [
            timestamp for timestamp in client_limits[operation]
            if current_time - timestamp < window_seconds
        ]
        
        # Check rate limit (default: 60 requests per minute)
        max_requests = 60
        if len(client_limits[operation]) >= max_requests:
            logger.warning(f"Rate limit exceeded for client {client_id}, operation {operation}")
            return False
        
        # Add current request
        client_limits[operation].append(current_time)
        return True
    
    def create_security_context(
        self,
        user_id: str,
        client_id: str,
        user_info: Dict
    ) -> Dict:
        """Create security context for a session."""
        permissions = self.get_client_permissions(client_id)
        
        return {
            "user_id": user_id,
            "client_id": client_id,
            "permission_level": permissions.level.value,
            "allowed_tools": permissions.allowed_tools,
            "allowed_resources": permissions.allowed_resources,
            "security_policies": {
                "data_isolation": True,  # Users can only access their own data
                "audit_logging": True,   # All operations are logged
                "rate_limiting": True,   # Rate limits are enforced
                "input_validation": True # All inputs are validated
            }
        }
    
    def audit_log(
        self,
        user_id: str,
        client_id: str,
        operation: str,
        resource: str,
        success: bool,
        details: Optional[Dict] = None
    ):
        """Log security-relevant operations for auditing."""
        log_entry = {
            "timestamp": logger.info("Audit log entry created"),
            "user_id": user_id,
            "client_id": client_id,
            "operation": operation,
            "resource": resource,
            "success": success,
            "details": details or {}
        }
        
        # In production, this should go to a secure audit log
        if success:
            logger.info(f"AUDIT: {operation} on {resource} by {user_id} via {client_id}")
        else:
            logger.warning(f"AUDIT: FAILED {operation} on {resource} by {user_id} via {client_id}")
    
    def validate_input_safety(self, input_data: Dict) -> Tuple[bool, List[str]]:
        """
        Validate input data for safety and security.
        
        Args:
            input_data: Input data to validate
            
        Returns:
            Tuple of (is_safe, list_of_issues)
        """
        issues = []
        
        # Check for potentially dangerous patterns
        dangerous_patterns = [
            "DROP TABLE", "DELETE FROM", "INSERT INTO", "UPDATE SET",
            "<script", "javascript:", "eval(", "exec(",
            "../", "\\", "__import__", "subprocess"
        ]
        
        def check_value(value, path=""):
            if isinstance(value, str):
                value_lower = value.lower()
                for pattern in dangerous_patterns:
                    if pattern.lower() in value_lower:
                        issues.append(f"Dangerous pattern '{pattern}' found in {path}")
            elif isinstance(value, dict):
                for k, v in value.items():
                    check_value(v, f"{path}.{k}" if path else k)
            elif isinstance(value, list):
                for i, v in enumerate(value):
                    check_value(v, f"{path}[{i}]" if path else f"[{i}]")
        
        check_value(input_data)
        
        return len(issues) == 0, issues
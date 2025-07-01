"""
Tests for MCP Security

Unit tests for security and permission management.
"""

import pytest
import sys
from pathlib import Path

# Add the mcp_server directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from security import MCPPermissions, PermissionLevel, ClientPermissions
from auth import MCPAuthProvider


class TestMCPPermissions:
    """Test MCP permission system."""
    
    @pytest.fixture
    def permissions(self):
        """Create permissions manager."""
        return MCPPermissions()
    
    def test_default_permissions(self, permissions):
        """Test default permission configurations."""
        # Test read-only permissions
        read_only = permissions.get_client_permissions("test_client_ro", PermissionLevel.READ_ONLY)
        assert read_only.level == PermissionLevel.READ_ONLY
        assert "goals_list" in read_only.allowed_tools
        assert "goals_create" not in read_only.allowed_tools
        
        # Test read-write permissions
        read_write = permissions.get_client_permissions("test_client_rw", PermissionLevel.READ_WRITE)
        assert read_write.level == PermissionLevel.READ_WRITE
        assert "goals_*" in read_write.allowed_tools
        
        # Test admin permissions
        admin = permissions.get_client_permissions("test_client_admin", PermissionLevel.ADMIN)
        assert admin.level == PermissionLevel.ADMIN
        assert "*" in admin.allowed_tools
    
    @pytest.mark.asyncio
    async def test_tool_permission_checking(self, permissions):
        """Test tool permission validation."""
        # Test read-only client
        permissions.set_client_permissions("readonly_client", 
            permissions.PERMISSION_CONFIGS[PermissionLevel.READ_ONLY]
        )
        
        # Should allow read operations
        can_list = await permissions.check_tool_permission(
            "user123", "readonly_client", "goals_list", {}
        )
        assert can_list is True
        
        # Should deny write operations
        can_create = await permissions.check_tool_permission(
            "user123", "readonly_client", "goals_create", {}
        )
        assert can_create is False
    
    @pytest.mark.asyncio
    async def test_resource_permission_checking(self, permissions):
        """Test resource permission validation."""
        # Test read-only client
        permissions.set_client_permissions("readonly_client",
            permissions.PERMISSION_CONFIGS[PermissionLevel.READ_ONLY]
        )
        
        # Should allow access to user profile
        can_access = await permissions.check_resource_permission(
            "user123", "readonly_client", "selfos://users/123/profile"
        )
        assert can_access is True
    
    @pytest.mark.asyncio
    async def test_rate_limiting(self, permissions):
        """Test rate limiting functionality."""
        client_id = "test_client"
        operation = "test_operation"
        
        # First request should pass
        allowed = await permissions.validate_rate_limit(client_id, operation)
        assert allowed is True
        
        # After many requests, should be rate limited
        for _ in range(70):  # Exceed default limit of 60
            await permissions.validate_rate_limit(client_id, operation)
        
        # Should now be rate limited
        allowed = await permissions.validate_rate_limit(client_id, operation)
        assert allowed is False
    
    def test_input_validation(self, permissions):
        """Test input safety validation."""
        # Test safe input
        safe_input = {"title": "My Goal", "description": "Learn Python"}
        is_safe, issues = permissions.validate_input_safety(safe_input)
        assert is_safe is True
        assert len(issues) == 0
        
        # Test dangerous input
        dangerous_input = {"query": "DROP TABLE users;"}
        is_safe, issues = permissions.validate_input_safety(dangerous_input)
        assert is_safe is False
        assert len(issues) > 0
        assert any("DROP TABLE" in issue for issue in issues)
    
    def test_security_context_creation(self, permissions):
        """Test security context creation."""
        user_info = {"uid": "user123", "email": "test@example.com"}
        context = permissions.create_security_context("user123", "client456", user_info)
        
        assert context["user_id"] == "user123"
        assert context["client_id"] == "client456"
        assert "permission_level" in context
        assert "security_policies" in context
        assert context["security_policies"]["data_isolation"] is True


class TestMCPAuth:
    """Test MCP authentication."""
    
    @pytest.fixture
    def auth_provider(self):
        """Create auth provider."""
        return MCPAuthProvider()
    
    @pytest.mark.asyncio
    async def test_api_key_authentication(self, auth_provider):
        """Test API key authentication."""
        # Test valid API key format
        valid_credentials = {
            "type": "api_key",
            "key": "sk-selfos-user123-randomstring"
        }
        
        success, user_id, user_info = await auth_provider.authenticate_client(valid_credentials)
        assert success is True
        assert user_id == "user123"
        assert user_info["auth_provider"] == "api_key"
        
        # Test invalid API key format
        invalid_credentials = {
            "type": "api_key",
            "key": "invalid-key-format"
        }
        
        success, user_id, user_info = await auth_provider.authenticate_client(invalid_credentials)
        assert success is False
        assert user_id is None
    
    @pytest.mark.asyncio
    async def test_unknown_auth_type(self, auth_provider):
        """Test unknown authentication type."""
        unknown_credentials = {
            "type": "unknown_type",
            "token": "some_token"
        }
        
        success, user_id, user_info = await auth_provider.authenticate_client(unknown_credentials)
        assert success is False
        assert user_id is None
    
    @pytest.mark.asyncio
    async def test_permission_validation(self, auth_provider):
        """Test permission validation."""
        # Test basic permissions (should allow most operations for authenticated users)
        can_read = await auth_provider.validate_permissions("user123", "goals", "read")
        assert can_read is True
        
        can_write = await auth_provider.validate_permissions("user123", "goals", "create")
        assert can_write is True
        
        can_delete = await auth_provider.validate_permissions("user123", "goals", "delete")
        assert can_delete is True
    
    def test_session_context_creation(self, auth_provider):
        """Test session context creation."""
        user_info = {"uid": "user123", "email": "test@example.com", "auth_provider": "api_key"}
        context = auth_provider.create_session_context("user123", user_info)
        
        assert context["user_id"] == "user123"
        assert context["user_info"] == user_info
        assert "permissions" in context
        assert context["permissions"]["read"] is True
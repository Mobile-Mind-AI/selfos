"""
Tests for MCP Configuration

Unit tests for configuration management and validation.
"""

import pytest
import os
import sys
from pathlib import Path

# Add the mcp_server directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import MCPConfig, TransportConfig, SecurityConfig


class TestMCPConfig:
    """Test MCP configuration management."""
    
    def test_default_configuration(self):
        """Test default configuration values."""
        config = MCPConfig()
        
        assert config.server_name == "selfos-mcp-server"
        assert config.server_version == "1.0.0"
        assert config.database_url == "sqlite:///:memory:"
        assert config.log_level == "INFO"
        assert config.max_concurrent_connections == 100
    
    def test_transport_configurations(self):
        """Test transport configurations."""
        config = MCPConfig()
        
        # Check default transports
        assert "stdio" in config.transports
        assert "sse" in config.transports
        assert "websocket" in config.transports
        
        # Check transport details
        stdio_config = config.get_transport_config("stdio")
        assert stdio_config.enabled is True
        assert "Standard I/O" in stdio_config.description
        
        sse_config = config.get_transport_config("sse")
        assert sse_config.enabled is True
        assert sse_config.endpoint == "/mcp/sse"
        
        websocket_config = config.get_transport_config("websocket")
        assert websocket_config.enabled is True
        assert websocket_config.endpoint == "/mcp/ws"
    
    def test_transport_enabled_check(self):
        """Test transport enabled checking."""
        config = MCPConfig()
        
        assert config.is_transport_enabled("stdio") is True
        assert config.is_transport_enabled("sse") is True
        assert config.is_transport_enabled("websocket") is True
        assert config.is_transport_enabled("nonexistent") is False
    
    def test_configuration_validation(self):
        """Test configuration validation."""
        # Valid configuration
        valid_config = MCPConfig()
        errors = valid_config.validate()
        assert len(errors) == 0
        
        # Invalid configuration
        invalid_config = MCPConfig()
        invalid_config.server_name = ""
        invalid_config.database_url = ""
        invalid_config.max_concurrent_connections = -1
        
        errors = invalid_config.validate()
        assert len(errors) > 0
        assert any("server_name is required" in error for error in errors)
        assert any("database_url is required" in error for error in errors)
        assert any("max_concurrent_connections must be positive" in error for error in errors)
    
    def test_from_env_configuration(self):
        """Test loading configuration from environment variables."""
        # Set test environment variables
        test_env = {
            "MCP_DATABASE_URL": "postgresql://test:test@localhost/test",
            "MCP_LOG_LEVEL": "DEBUG",
            "MCP_MAX_CONNECTIONS": "200",
            "MCP_REQUIRE_AUTH": "false",
            "MCP_ALLOWED_ORIGINS": "localhost,example.com"
        }
        
        # Temporarily set environment variables
        original_env = {}
        for key, value in test_env.items():
            original_env[key] = os.environ.get(key)
            os.environ[key] = value
        
        try:
            config = MCPConfig.from_env()
            
            assert config.database_url == "postgresql://test:test@localhost/test"
            assert config.log_level == "DEBUG"
            assert config.max_concurrent_connections == 200
            assert config.security.require_authentication is False
            assert "localhost" in config.security.allowed_origins
            assert "example.com" in config.security.allowed_origins
            
        finally:
            # Restore original environment
            for key, original_value in original_env.items():
                if original_value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = original_value
    
    def test_tools_configuration(self):
        """Test tools configuration settings."""
        config = MCPConfig()
        
        assert "goals" in config.tools_config
        assert "projects" in config.tools_config
        assert "tasks" in config.tools_config
        assert "ai" in config.tools_config
        
        # Check goals config
        goals_config = config.tools_config["goals"]
        assert goals_config["max_results"] == 50
        assert goals_config["allow_bulk_operations"] is True
        assert goals_config["cache_ttl"] == 300
    
    def test_resources_configuration(self):
        """Test resources configuration settings."""
        config = MCPConfig()
        
        assert "user_profile" in config.resources_config
        assert "goal_context" in config.resources_config
        assert "daily_summary" in config.resources_config
        
        # Check user profile config
        user_profile_config = config.resources_config["user_profile"]
        assert user_profile_config["cache_ttl"] == 300
        assert user_profile_config["include_sensitive_data"] is False


class TestTransportConfig:
    """Test transport configuration."""
    
    def test_transport_config_creation(self):
        """Test transport config creation."""
        config = TransportConfig(
            enabled=True,
            endpoint="/test/endpoint",
            description="Test transport",
            options={"option1": "value1"}
        )
        
        assert config.enabled is True
        assert config.endpoint == "/test/endpoint"
        assert config.description == "Test transport"
        assert config.options["option1"] == "value1"
    
    def test_transport_config_defaults(self):
        """Test transport config defaults."""
        config = TransportConfig()
        
        assert config.enabled is True
        assert config.endpoint is None
        assert config.description == ""
        assert config.options == {}


class TestSecurityConfig:
    """Test security configuration."""
    
    def test_security_config_defaults(self):
        """Test security config defaults."""
        config = SecurityConfig()
        
        assert config.require_authentication is True
        assert config.allowed_origins == ["*"]
        assert config.max_connections == 100
        assert config.rate_limit_requests_per_minute == 60
        assert config.rate_limit_requests_per_hour == 1000
    
    def test_security_config_custom(self):
        """Test custom security configuration."""
        config = SecurityConfig(
            require_authentication=False,
            allowed_origins=["localhost", "example.com"],
            max_connections=50,
            rate_limit_requests_per_minute=30
        )
        
        assert config.require_authentication is False
        assert config.allowed_origins == ["localhost", "example.com"]
        assert config.max_connections == 50
        assert config.rate_limit_requests_per_minute == 30
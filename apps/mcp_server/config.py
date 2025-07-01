"""
MCP Server Configuration

Configuration settings and environment variables for the SelfOS MCP server.
"""

import os
from typing import Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class TransportConfig:
    """Configuration for MCP transport layers."""
    enabled: bool = True
    endpoint: Optional[str] = None
    description: str = ""
    options: Dict = field(default_factory=dict)


@dataclass
class SecurityConfig:
    """Security configuration for MCP server."""
    require_authentication: bool = True
    allowed_origins: List[str] = field(default_factory=lambda: ["*"])
    max_connections: int = 100
    rate_limit_requests_per_minute: int = 60
    rate_limit_requests_per_hour: int = 1000


@dataclass
class MCPConfig:
    """Main configuration class for SelfOS MCP Server."""
    
    # Server identification
    server_name: str = "selfos-mcp-server"
    server_version: str = "1.0.0"
    
    # Database connection
    database_url: str = field(default_factory=lambda: os.getenv("DATABASE_URL", "sqlite:///:memory:"))
    
    # Firebase configuration
    google_credentials_path: str = field(default_factory=lambda: os.getenv("GOOGLE_APPLICATION_CREDENTIALS", ""))
    
    # Transport configurations
    transports: Dict[str, TransportConfig] = field(default_factory=lambda: {
        "stdio": TransportConfig(
            enabled=True,
            description="Standard I/O transport for local AI agents"
        ),
        "sse": TransportConfig(
            enabled=True,
            endpoint="/mcp/sse",
            description="Server-Sent Events for web clients"
        ),
        "websocket": TransportConfig(
            enabled=True,
            endpoint="/mcp/ws",
            description="WebSocket for real-time clients"
        )
    })
    
    # Security settings
    security: SecurityConfig = field(default_factory=SecurityConfig)
    
    # Tool configurations
    tools_config: Dict = field(default_factory=lambda: {
        "goals": {
            "max_results": 50,
            "allow_bulk_operations": True,
            "cache_ttl": 300  # 5 minutes
        },
        "projects": {
            "max_results": 50,
            "allow_bulk_operations": True,
            "cache_ttl": 600  # 10 minutes
        },
        "tasks": {
            "max_results": 100,
            "allow_bulk_operations": True,
            "cache_ttl": 180  # 3 minutes
        },
        "ai": {
            "max_concurrent_requests": 5,
            "timeout_seconds": 30,
            "cache_ttl": 1800  # 30 minutes
        }
    })
    
    # Resource configurations
    resources_config: Dict = field(default_factory=lambda: {
        "user_profile": {
            "cache_ttl": 300,
            "include_sensitive_data": False
        },
        "goal_context": {
            "cache_ttl": 600,
            "max_depth": 3  # How deep to traverse relationships
        },
        "daily_summary": {
            "cache_ttl": 3600,
            "include_analytics": True
        }
    })
    
    # Logging configuration
    log_level: str = field(default_factory=lambda: os.getenv("MCP_LOG_LEVEL", "INFO"))
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Performance settings
    max_concurrent_connections: int = 100
    connection_timeout: int = 30
    request_timeout: int = 60
    
    @classmethod
    def from_env(cls) -> "MCPConfig":
        """Create configuration from environment variables."""
        config = cls()
        
        # Override with environment variables if present
        if db_url := os.getenv("MCP_DATABASE_URL"):
            config.database_url = db_url
        
        if log_level := os.getenv("MCP_LOG_LEVEL"):
            config.log_level = log_level
        
        if max_conn := os.getenv("MCP_MAX_CONNECTIONS"):
            try:
                config.max_concurrent_connections = int(max_conn)
            except ValueError:
                pass
        
        # Security overrides
        if require_auth := os.getenv("MCP_REQUIRE_AUTH"):
            config.security.require_authentication = require_auth.lower() == "true"
        
        if origins := os.getenv("MCP_ALLOWED_ORIGINS"):
            config.security.allowed_origins = origins.split(",")
        
        return config
    
    def validate(self) -> List[str]:
        """Validate configuration and return list of errors."""
        errors = []
        
        if not self.server_name:
            errors.append("server_name is required")
        
        if not self.database_url:
            errors.append("database_url is required")
        
        if self.security.require_authentication and not self.google_credentials_path:
            errors.append("google_credentials_path is required when authentication is enabled")
        
        if self.max_concurrent_connections <= 0:
            errors.append("max_concurrent_connections must be positive")
        
        return errors
    
    def get_transport_config(self, transport_name: str) -> Optional[TransportConfig]:
        """Get configuration for a specific transport."""
        return self.transports.get(transport_name)
    
    def is_transport_enabled(self, transport_name: str) -> bool:
        """Check if a transport is enabled."""
        config = self.get_transport_config(transport_name)
        return config is not None and config.enabled
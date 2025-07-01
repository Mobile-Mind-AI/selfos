"""
Tests for MCP Server Core

Unit tests for the main SelfOS MCP Server functionality.
"""

import pytest
import asyncio
import sys
import os
from pathlib import Path

# Add the mcp_server directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from server import SelfOSMcpServer
from config import MCPConfig


class TestMCPServerCore:
    """Test core MCP server functionality."""
    
    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return MCPConfig(
            server_name="test-mcp-server",
            database_url="sqlite:///:memory:",
            log_level="DEBUG"
        )
    
    @pytest.fixture
    def server(self, config):
        """Create test server instance."""
        return SelfOSMcpServer(config)
    
    def test_server_initialization(self, config):
        """Test server initializes correctly."""
        server = SelfOSMcpServer(config)
        assert server.config.server_name == "test-mcp-server"
        assert server.server is not None
        assert server.auth_provider is not None
        assert server.permissions is not None
    
    def test_server_capabilities(self, server):
        """Test server capabilities reporting."""
        capabilities = server.get_capabilities()
        
        assert "tools" in capabilities
        assert "resources" in capabilities
        assert "transports" in capabilities
        assert "authentication" in capabilities
        assert "version" in capabilities
        
        # Check tool categories
        assert "goals" in capabilities["tools"]
        assert "projects" in capabilities["tools"]
        assert "tasks" in capabilities["tools"]
        assert "ai" in capabilities["tools"]
        
        # Check resource types
        assert "user_profile" in capabilities["resources"]
        assert "goal_context" in capabilities["resources"]
        
        # Check transports
        assert "stdio" in capabilities["transports"]
        assert "sse" in capabilities["transports"]
        assert "websocket" in capabilities["transports"]
    
    @pytest.mark.asyncio
    async def test_list_tools(self, server):
        """Test tool listing functionality."""
        tools = await server.goals_tools.list_tools()
        assert len(tools) > 0
        
        # Check that goals tools are present
        tool_names = [tool.name for tool in tools]
        assert "goals_list" in tool_names
        assert "goals_create" in tool_names
        assert "goals_update" in tool_names
        assert "goals_delete" in tool_names
        assert "goals_search" in tool_names
    
    @pytest.mark.asyncio
    async def test_list_resources(self, server):
        """Test resource listing functionality."""
        user_resources = await server.user_resources.list_resources()
        context_resources = await server.context_resources.list_resources()
        
        assert len(user_resources) > 0
        assert len(context_resources) > 0
        
        # Check resource URIs
        user_uris = [str(res.uri) for res in user_resources]
        assert any("users" in uri for uri in user_uris)
        
        context_uris = [str(res.uri) for res in context_resources]
        assert any("context" in uri for uri in context_uris)


class TestMCPServerIntegration:
    """Test MCP server integration scenarios."""
    
    @pytest.fixture
    def server(self):
        """Create server for integration tests."""
        config = MCPConfig(database_url="sqlite:///:memory:")
        return SelfOSMcpServer(config)
    
    @pytest.mark.asyncio
    async def test_tool_call_error_handling(self, server):
        """Test that tool calls handle errors gracefully."""
        # This should fail gracefully due to missing database tables
        result = await server.goals_tools.call_tool("goals_list", {
            "user_id": "test_user_123",
            "limit": 10
        })
        
        # Should return error but not crash
        assert "error" in result
        assert "success" in result
        assert result["success"] is False
    
    @pytest.mark.asyncio
    async def test_invalid_tool_call(self, server):
        """Test calling non-existent tool."""
        result = await server.goals_tools.call_tool("invalid_tool", {})
        
        assert "error" in result
        assert "Unknown goal tool" in result["error"]
        assert result["success"] is False
    
    @pytest.mark.asyncio
    async def test_tool_argument_validation(self, server):
        """Test tool argument validation."""
        # Missing required user_id argument
        result = await server.goals_tools.call_tool("goals_list", {})
        
        assert "error" in result
        assert "Missing required arguments" in result["error"]
        assert result["success"] is False
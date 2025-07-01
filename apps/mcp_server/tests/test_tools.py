"""
Tests for MCP Tools

Unit tests for MCP tool handlers and functionality.
"""

import pytest
import sys
from pathlib import Path

# Add the mcp_server directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.goals_tools import GoalsToolsHandler
from tools.projects_tools import ProjectsToolsHandler
from tools.tasks_tools import TasksToolsHandler
from tools.ai_tools import AIToolsHandler


class TestGoalsTools:
    """Test Goals tools handler."""
    
    @pytest.fixture
    def handler(self):
        """Create goals tools handler."""
        return GoalsToolsHandler()
    
    @pytest.mark.asyncio
    async def test_list_tools(self, handler):
        """Test goals tools listing."""
        tools = await handler.list_tools()
        
        assert len(tools) == 6  # Expected number of goal tools
        
        tool_names = [tool.name for tool in tools]
        expected_tools = [
            "goals_list", "goals_get", "goals_create", 
            "goals_update", "goals_delete", "goals_search"
        ]
        
        for expected_tool in expected_tools:
            assert expected_tool in tool_names
    
    @pytest.mark.asyncio
    async def test_tool_schemas(self, handler):
        """Test that tools have proper schemas."""
        tools = await handler.list_tools()
        
        for tool in tools:
            assert hasattr(tool, 'name')
            assert hasattr(tool, 'description')
            assert hasattr(tool, 'inputSchema')
            
            # Check that required user_id is present
            schema = tool.inputSchema
            assert "properties" in schema
            assert "user_id" in schema["properties"]
            assert "required" in schema
            assert "user_id" in schema["required"]
    
    @pytest.mark.asyncio
    async def test_argument_validation(self, handler):
        """Test argument validation."""
        # Test missing required arguments
        result = await handler.call_tool("goals_list", {})
        assert "error" in result
        assert "Missing required arguments" in result["error"]
        
        # Test with valid arguments but no database
        result = await handler.call_tool("goals_list", {"user_id": "test_user"})
        assert "error" in result  # Will fail due to no database, but gracefully
    
    @pytest.mark.asyncio
    async def test_unknown_tool(self, handler):
        """Test calling unknown tool."""
        result = await handler.call_tool("unknown_tool", {"user_id": "test"})
        assert "error" in result
        assert "Unknown goal tool" in result["error"]


class TestProjectsTools:
    """Test Projects tools handler."""
    
    @pytest.fixture
    def handler(self):
        """Create projects tools handler."""
        return ProjectsToolsHandler()
    
    @pytest.mark.asyncio
    async def test_list_tools(self, handler):
        """Test projects tools listing."""
        tools = await handler.list_tools()
        
        assert len(tools) >= 3  # At least basic CRUD tools
        
        tool_names = [tool.name for tool in tools]
        assert "projects_list" in tool_names
        assert "projects_get" in tool_names
        assert "projects_progress" in tool_names
    
    @pytest.mark.asyncio
    async def test_placeholder_implementation(self, handler):
        """Test that placeholder tools return not implemented message."""
        result = await handler.call_tool("projects_list", {"user_id": "test"})
        assert "not yet implemented" in result["message"]
        assert result["success"] is False


class TestTasksTools:
    """Test Tasks tools handler."""
    
    @pytest.fixture
    def handler(self):
        """Create tasks tools handler."""
        return TasksToolsHandler()
    
    @pytest.mark.asyncio
    async def test_list_tools(self, handler):
        """Test tasks tools listing."""
        tools = await handler.list_tools()
        
        assert len(tools) >= 2
        
        tool_names = [tool.name for tool in tools]
        assert "tasks_list" in tool_names
        assert "tasks_get" in tool_names


class TestAITools:
    """Test AI tools handler."""
    
    @pytest.fixture
    def handler(self):
        """Create AI tools handler."""
        return AIToolsHandler()
    
    @pytest.mark.asyncio
    async def test_list_tools(self, handler):
        """Test AI tools listing."""
        tools = await handler.list_tools()
        
        assert len(tools) >= 3
        
        tool_names = [tool.name for tool in tools]
        assert "ai_decompose_goal" in tool_names
        assert "ai_suggest_tasks" in tool_names
        assert "ai_analyze_progress" in tool_names
    
    @pytest.mark.asyncio
    async def test_ai_tool_schemas(self, handler):
        """Test AI tool schemas."""
        tools = await handler.list_tools()
        
        decompose_tool = next(tool for tool in tools if tool.name == "ai_decompose_goal")
        schema = decompose_tool.inputSchema
        
        assert "goal_description" in schema["properties"]
        assert "user_id" in schema["required"]
        assert "goal_description" in schema["required"]
"""
SelfOS MCP Server Core

Main MCP server implementation providing standardized access to SelfOS APIs,
database, and AI services through the Model Context Protocol.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import json

from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.types import (
    Tool, Resource, Prompt, TextContent, ImageContent, EmbeddedResource,
    CallToolRequest, ListResourcesRequest, ListToolsRequest, ReadResourceRequest,
    GetPromptRequest, ListPromptsRequest
)

from config import MCPConfig
from auth import MCPAuthProvider
from security import MCPPermissions
from tools.goals_tools import GoalsToolsHandler
from tools.projects_tools import ProjectsToolsHandler
from tools.tasks_tools import TasksToolsHandler
from tools.ai_tools import AIToolsHandler
from resources.user_resources import UserResourcesHandler
from resources.context_resources import ContextResourcesHandler
from transport.stdio_transport import StdioTransport
from transport.sse_transport import SSETransport
from transport.websocket_transport import WebSocketTransport

logger = logging.getLogger(__name__)


class SelfOSMcpServer:
    """
    Main SelfOS MCP Server implementation.
    
    Provides standardized access to SelfOS APIs, database, and AI services
    through the Model Context Protocol specification.
    """
    
    def __init__(self, config: Optional[MCPConfig] = None):
        """Initialize the MCP server with configuration."""
        self.config = config or MCPConfig()
        self.server = Server(self.config.server_name)
        self.auth_provider = MCPAuthProvider()
        self.permissions = MCPPermissions()
        
        # Tool handlers
        self.goals_tools = GoalsToolsHandler()
        self.projects_tools = ProjectsToolsHandler()
        self.tasks_tools = TasksToolsHandler()
        self.ai_tools = AIToolsHandler()
        
        # Resource handlers
        self.user_resources = UserResourcesHandler()
        self.context_resources = ContextResourcesHandler()
        
        # Transport layers
        self.transports = {
            "stdio": StdioTransport(self.server),
            "sse": SSETransport(self.server),
            "websocket": WebSocketTransport(self.server)
        }
        
        # Initialize handlers
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Set up MCP protocol handlers."""
        
        @self.server.list_tools()
        async def handle_list_tools() -> List[Tool]:
            """List all available tools."""
            tools = []
            
            # Add tools from all handlers
            tools.extend(await self.goals_tools.list_tools())
            tools.extend(await self.projects_tools.list_tools())
            tools.extend(await self.tasks_tools.list_tools())
            tools.extend(await self.ai_tools.list_tools())
            
            return tools
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            """Handle tool execution requests."""
            try:
                # Extract user context from arguments
                user_id = arguments.get("user_id")
                if not user_id:
                    return [TextContent(
                        type="text",
                        text=json.dumps({"error": "user_id is required"})
                    )]
                
                # Route to appropriate handler
                if name.startswith("goals_"):
                    result = await self.goals_tools.call_tool(name, arguments)
                elif name.startswith("projects_"):
                    result = await self.projects_tools.call_tool(name, arguments)
                elif name.startswith("tasks_"):
                    result = await self.tasks_tools.call_tool(name, arguments)
                elif name.startswith("ai_"):
                    result = await self.ai_tools.call_tool(name, arguments)
                else:
                    result = {"error": f"Unknown tool: {name}"}
                
                return [TextContent(
                    type="text",
                    text=json.dumps(result, default=str)
                )]
                
            except Exception as e:
                logger.error(f"Error calling tool {name}: {e}")
                return [TextContent(
                    type="text",
                    text=json.dumps({"error": str(e)})
                )]
        
        @self.server.list_resources()
        async def handle_list_resources() -> List[Resource]:
            """List all available resources."""
            resources = []
            
            # Add resources from all handlers
            resources.extend(await self.user_resources.list_resources())
            resources.extend(await self.context_resources.list_resources())
            
            return resources
        
        @self.server.read_resource()
        async def handle_read_resource(uri: str) -> str:
            """Handle resource read requests."""
            try:
                # Route to appropriate handler based on URI pattern
                if uri.startswith("selfos://users/"):
                    return await self.user_resources.read_resource(uri)
                elif uri.startswith("selfos://context/"):
                    return await self.context_resources.read_resource(uri)
                else:
                    raise ValueError(f"Unknown resource URI: {uri}")
                    
            except Exception as e:
                logger.error(f"Error reading resource {uri}: {e}")
                raise
        
        @self.server.list_prompts()
        async def handle_list_prompts() -> List[Prompt]:
            """List all available prompts."""
            return [
                Prompt(
                    name="decompose_goal",
                    description="Decompose a high-level goal into actionable tasks",
                    arguments=[
                        {"name": "goal_description", "description": "The goal to decompose", "required": True},
                        {"name": "context", "description": "Additional context about the user", "required": False}
                    ]
                ),
                Prompt(
                    name="suggest_project_structure",
                    description="Suggest optimal project structure for a complex goal",
                    arguments=[
                        {"name": "project_description", "description": "The project to structure", "required": True},
                        {"name": "user_preferences", "description": "User's working preferences", "required": False}
                    ]
                ),
                Prompt(
                    name="daily_planning",
                    description="Generate a daily plan based on user's goals and tasks",
                    arguments=[
                        {"name": "user_id", "description": "User identifier", "required": True},
                        {"name": "date", "description": "Target date for planning", "required": False}
                    ]
                )
            ]
        
        @self.server.get_prompt()
        async def handle_get_prompt(name: str, arguments: Dict[str, str]) -> str:
            """Handle prompt requests."""
            if name == "decompose_goal":
                goal = arguments.get("goal_description", "")
                context = arguments.get("context", "")
                return f"""
                Please help decompose this goal into actionable tasks:
                
                Goal: {goal}
                Context: {context}
                
                Break this down into specific, measurable tasks that can be completed within reasonable timeframes.
                Consider dependencies between tasks and suggest a logical order.
                """
                
            elif name == "suggest_project_structure":
                project = arguments.get("project_description", "")
                preferences = arguments.get("user_preferences", "")
                return f"""
                Please suggest an optimal project structure for:
                
                Project: {project}
                User Preferences: {preferences}
                
                Organize this into phases, milestones, and actionable components.
                Consider the user's working style and preferences.
                """
                
            elif name == "daily_planning":
                user_id = arguments.get("user_id", "")
                date = arguments.get("date", datetime.now().strftime("%Y-%m-%d"))
                return f"""
                Create a daily plan for user {user_id} on {date}.
                
                Consider:
                - Current pending tasks and their priorities
                - Goal deadlines and milestones
                - User's energy levels and working patterns
                - Time estimates for tasks
                
                Provide a structured daily schedule with time blocks and priorities.
                """
            
            else:
                raise ValueError(f"Unknown prompt: {name}")
    
    async def start(self, transport_type: str = "stdio"):
        """Start the MCP server with specified transport."""
        if transport_type not in self.transports:
            raise ValueError(f"Unknown transport type: {transport_type}")
        
        transport = self.transports[transport_type]
        logger.info(f"Starting SelfOS MCP Server on {transport_type} transport")
        
        try:
            await transport.start()
        except Exception as e:
            logger.error(f"Failed to start MCP server: {e}")
            raise
    
    async def stop(self):
        """Stop the MCP server and cleanup resources."""
        logger.info("Stopping SelfOS MCP Server")
        
        # Stop all transports
        for transport in self.transports.values():
            try:
                await transport.stop()
            except Exception as e:
                logger.error(f"Error stopping transport: {e}")
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Get server capabilities information."""
        return {
            "tools": {
                "goals": ["create", "list", "update", "delete", "search"],
                "projects": ["create", "list", "update", "delete", "progress", "timeline"],
                "tasks": ["create", "list", "update", "delete", "dependencies"],
                "ai": ["decompose_goal", "suggest_tasks", "analyze_progress"]
            },
            "resources": {
                "user_profile": "Complete user context and preferences",
                "goal_context": "Detailed goal information with tasks and progress",
                "project_context": "Project details with timeline and milestones",
                "daily_summary": "Daily activity summary and insights"
            },
            "transports": list(self.transports.keys()),
            "authentication": ["firebase_token", "api_key"],
            "version": "1.0.0"
        }


async def main():
    """Main entry point for running the MCP server."""
    import sys
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create and start server
    server = SelfOSMcpServer()
    
    # Determine transport from command line args
    transport_type = "stdio"
    if len(sys.argv) > 1:
        transport_type = sys.argv[1]
    
    try:
        await server.start(transport_type)
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
    finally:
        await server.stop()


if __name__ == "__main__":
    asyncio.run(main())
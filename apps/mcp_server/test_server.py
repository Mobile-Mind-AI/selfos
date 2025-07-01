"""
Simple test script for SelfOS MCP Server

Tests basic server initialization and capability reporting.
"""

import asyncio
import sys
from pathlib import Path

# Add backend_api to path for imports
sys.path.append(str(Path(__file__).parent.parent / "backend_api"))

from server import SelfOSMcpServer
from config import MCPConfig


async def test_server_initialization():
    """Test basic server initialization."""
    print("Testing SelfOS MCP Server initialization...")
    
    try:
        # Create configuration
        config = MCPConfig()
        print(f"✓ Configuration created: {config.server_name}")
        
        # Create server
        server = SelfOSMcpServer(config)
        print(f"✓ Server created successfully")
        
        # Test capabilities
        capabilities = server.get_capabilities()
        print(f"✓ Server capabilities: {len(capabilities['tools'])} tool categories")
        
        # Test tool listing
        tools = await server.goals_tools.list_tools()
        print(f"✓ Goals tools: {len(tools)} tools available")
        
        projects_tools = await server.projects_tools.list_tools()
        print(f"✓ Projects tools: {len(projects_tools)} tools available")
        
        tasks_tools = await server.tasks_tools.list_tools()
        print(f"✓ Tasks tools: {len(tasks_tools)} tools available")
        
        ai_tools = await server.ai_tools.list_tools()
        print(f"✓ AI tools: {len(ai_tools)} tools available")
        
        # Test resource listing
        user_resources = await server.user_resources.list_resources()
        print(f"✓ User resources: {len(user_resources)} resources available")
        
        context_resources = await server.context_resources.list_resources()
        print(f"✓ Context resources: {len(context_resources)} resources available")
        
        print("\\n🎉 All tests passed! MCP server is ready.")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_goal_tool():
    """Test a specific goal tool."""
    print("\\nTesting goal tool functionality...")
    
    try:
        config = MCPConfig()
        server = SelfOSMcpServer(config)
        
        # Test listing tools
        tools = await server.goals_tools.list_tools()
        print(f"✓ Found {len(tools)} goal tools")
        
        # Test calling a tool (should fail gracefully without database)
        result = await server.goals_tools.call_tool("goals_list", {
            "user_id": "test_user_123",
            "limit": 10
        })
        
        # This should fail because we don't have a database connection
        # but the error should be handled gracefully
        if "error" in result:
            print(f"✓ Tool call handled gracefully: {result['error'][:50]}...")
        else:
            print(f"✓ Tool call succeeded: {result}")
        
        return True
        
    except Exception as e:
        print(f"❌ Goal tool test failed: {e}")
        return False


if __name__ == "__main__":
    async def run_tests():
        success = True
        success &= await test_server_initialization()
        success &= await test_goal_tool()
        
        if success:
            print("\\n✅ All tests passed!")
            sys.exit(0)
        else:
            print("\\n❌ Some tests failed!")
            sys.exit(1)
    
    asyncio.run(run_tests())
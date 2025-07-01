# MCP (Model Context Protocol) Implementation Plan

**Date:** 2025-07-01  
**Priority:** High - Next-Generation AI Integration  
**Status:** Planning Phase

## 1. Executive Summary

The Model Context Protocol (MCP) is Anthropic's open standard for connecting AI models to data sources and tools securely. Implementing MCP in SelfOS will transform our AI capabilities by providing standardized, secure access to APIs and databases, enabling more sophisticated AI interactions and automations.

### Key Benefits
- **Standardized AI Integration**: Universal protocol for AI-data connections
- **Enhanced Security**: Secure, controlled access to sensitive resources
- **Improved AI Capabilities**: Rich context and tool access for AI agents
- **Future-Proof Architecture**: Open standard adopted by major AI providers
- **Developer Experience**: Simplified AI integration for third-party developers

## 2. MCP Protocol Overview

### Architecture Components
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   MCP Client    │◄──►│   MCP Server    │◄──►│  Data Sources   │
│  (AI Agent)     │    │   (SelfOS)      │    │ (APIs/Database) │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Core Primitives
1. **Resources**: Structured data for LLM context
2. **Tools**: Executable functions LLMs can call
3. **Prompts**: Instruction templates for AI agents
4. **Sampling**: AI model interaction capabilities

### Communication Model
- **Transport**: JSON-RPC 2.0 over stdio, SSE, or WebSocket
- **Security**: Controlled access with permission models
- **Scalability**: Supports multiple concurrent connections

## 3. SelfOS MCP Architecture

### High-Level Design
```
┌─────────────────────────────────────────────────────────────┐
│                    SelfOS MCP Server                        │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ API Tools   │  │ DB Tools    │  │ Resources   │         │
│  │ Handler     │  │ Handler     │  │ Manager     │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ Security    │  │ Auth        │  │ Permissions │         │
│  │ Manager     │  │ Provider    │  │ Engine      │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ Transport   │  │ Protocol    │  │ Session     │         │
│  │ Layer       │  │ Handler     │  │ Manager     │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   SelfOS Core Services                      │
├─────────────────────────────────────────────────────────────┤
│  FastAPI Backend  │  PostgreSQL DB  │  Redis Cache         │
│  AI Engine        │  Memory Service │  Auth Service        │
└─────────────────────────────────────────────────────────────┘
```

## 4. Implementation Plan

### Phase 1: MCP Server Foundation (Week 1-2)

#### Core Infrastructure
```python
# apps/mcp_server/server.py
from mcp import McpServer, Resource, Tool
from mcp.server.models import InitializationOptions
import asyncio

class SelfOSMcpServer:
    def __init__(self):
        self.server = McpServer("selfos-mcp-server")
        self.setup_resources()
        self.setup_tools()
        
    async def run(self):
        """Start the MCP server"""
        async with self.server.transport() as transport:
            await transport.serve()
```

#### Transport Configuration
```python
# Transport options
TRANSPORT_CONFIG = {
    "stdio": {
        "enabled": True,
        "description": "Standard I/O transport for local AI agents"
    },
    "sse": {
        "enabled": True, 
        "endpoint": "/mcp/sse",
        "description": "Server-Sent Events for web clients"
    },
    "websocket": {
        "enabled": True,
        "endpoint": "/mcp/ws", 
        "description": "WebSocket for real-time clients"
    }
}
```

### Phase 2: API Tools Implementation (Week 2-3)

#### Goals API Tools
```python
@mcp_tool("list_goals")
async def list_goals(
    user_id: str,
    status: Optional[str] = None,
    limit: int = 10
) -> List[Dict]:
    """List user goals with optional filtering"""
    goals = await goals_service.list_goals(
        user_id=user_id,
        status=status,
        limit=limit
    )
    return [goal.dict() for goal in goals]

@mcp_tool("create_goal")
async def create_goal(
    user_id: str,
    title: str,
    description: str,
    target_date: Optional[str] = None,
    life_area_id: Optional[int] = None
) -> Dict:
    """Create a new goal"""
    goal_data = GoalCreate(
        title=title,
        description=description,
        target_date=target_date,
        life_area_id=life_area_id
    )
    goal = await goals_service.create_goal(user_id, goal_data)
    return goal.dict()

@mcp_tool("update_goal")
async def update_goal(
    user_id: str,
    goal_id: int,
    **updates
) -> Dict:
    """Update an existing goal"""
    goal = await goals_service.update_goal(user_id, goal_id, updates)
    return goal.dict()
```

#### Tasks API Tools
```python
@mcp_tool("list_tasks")
async def list_tasks(
    user_id: str,
    goal_id: Optional[int] = None,
    status: Optional[str] = None,
    due_date: Optional[str] = None,
    limit: int = 20
) -> List[Dict]:
    """List user tasks with comprehensive filtering"""
    tasks = await tasks_service.list_tasks(
        user_id=user_id,
        goal_id=goal_id,
        status=status,
        due_date=due_date,
        limit=limit
    )
    return [task.dict() for task in tasks]

@mcp_tool("create_task")
async def create_task(
    user_id: str,
    title: str,
    description: str,
    goal_id: Optional[int] = None,
    due_date: Optional[str] = None,
    priority: str = "medium",
    estimated_duration: Optional[int] = None
) -> Dict:
    """Create a new task"""
    task_data = TaskCreate(
        title=title,
        description=description,
        goal_id=goal_id,
        due_date=due_date,
        priority=priority,
        estimated_duration=estimated_duration
    )
    task = await tasks_service.create_task(user_id, task_data)
    return task.dict()
```

#### AI and Memory Tools
```python
@mcp_tool("decompose_goal")
async def decompose_goal(
    user_id: str,
    goal_description: str,
    context: Optional[Dict] = None
) -> Dict:
    """Use AI to decompose a goal into actionable tasks"""
    result = await ai_service.decompose_goal(
        user_id=user_id,
        goal_description=goal_description,
        context=context
    )
    return result.dict()

@mcp_tool("search_memory")
async def search_memory(
    user_id: str,
    query: str,
    limit: int = 5
) -> List[Dict]:
    """Search user's memory/context using semantic search"""
    memories = await memory_service.search(
        user_id=user_id,
        query=query,
        limit=limit
    )
    return [memory.dict() for memory in memories]

@mcp_tool("add_memory")
async def add_memory(
    user_id: str,
    content: str,
    memory_type: str = "reflection",
    metadata: Optional[Dict] = None
) -> Dict:
    """Add a new memory/reflection for the user"""
    memory = await memory_service.add_memory(
        user_id=user_id,
        content=content,
        memory_type=memory_type,
        metadata=metadata
    )
    return memory.dict()
```

### Phase 3: Database Access Tools (Week 3-4)

#### Direct Database Query Tools
```python
@mcp_tool("query_user_stats")
async def query_user_stats(user_id: str) -> Dict:
    """Get comprehensive user statistics"""
    query = """
    SELECT 
        COUNT(CASE WHEN g.status = 'active' THEN 1 END) as active_goals,
        COUNT(CASE WHEN g.status = 'completed' THEN 1 END) as completed_goals,
        COUNT(CASE WHEN t.status = 'pending' THEN 1 END) as pending_tasks,
        COUNT(CASE WHEN t.status = 'completed' THEN 1 END) as completed_tasks,
        COUNT(DISTINCT m.id) as memory_items
    FROM users u
    LEFT JOIN goals g ON u.uid = g.user_id
    LEFT JOIN tasks t ON u.uid = t.user_id  
    LEFT JOIN memory_items m ON u.uid = m.user_id
    WHERE u.uid = $1
    """
    result = await db.fetch_one(query, user_id)
    return dict(result)

@mcp_tool("analyze_progress")
async def analyze_progress(
    user_id: str,
    period: str = "30d"
) -> Dict:
    """Analyze user progress over time period"""
    query = """
    SELECT 
        DATE_TRUNC('day', t.completed_at) as date,
        COUNT(*) as tasks_completed,
        AVG(t.estimated_duration) as avg_duration
    FROM tasks t
    WHERE t.user_id = $1 
        AND t.status = 'completed'
        AND t.completed_at >= NOW() - INTERVAL %s
    GROUP BY DATE_TRUNC('day', t.completed_at)
    ORDER BY date DESC
    """
    results = await db.fetch_all(query, user_id, period)
    return {"progress_data": [dict(row) for row in results]}
```

#### Safe Database Operations
```python
@mcp_tool("backup_user_data")
async def backup_user_data(user_id: str) -> Dict:
    """Create a backup of user's data"""
    backup_data = {
        "user": await get_user_data(user_id),
        "goals": await get_user_goals(user_id),
        "tasks": await get_user_tasks(user_id),
        "memories": await get_user_memories(user_id),
        "created_at": datetime.utcnow().isoformat()
    }
    
    backup_id = await store_backup(user_id, backup_data)
    return {"backup_id": backup_id, "status": "completed"}
```

### Phase 4: Resources Implementation (Week 4-5)

#### User Context Resources
```python
@mcp_resource("user_profile")
async def get_user_profile(user_id: str) -> Resource:
    """Get comprehensive user profile context"""
    user = await users_service.get_user(user_id)
    goals = await goals_service.list_goals(user_id, limit=50)
    recent_tasks = await tasks_service.list_tasks(
        user_id, status="completed", limit=10
    )
    
    profile_data = {
        "user": user.dict(),
        "active_goals": [g.dict() for g in goals if g.status == "active"],
        "recent_achievements": [t.dict() for t in recent_tasks],
        "preferences": await get_user_preferences(user_id)
    }
    
    return Resource(
        uri=f"selfos://users/{user_id}/profile",
        name="User Profile",
        description="Complete user context and preferences",
        mimeType="application/json",
        text=json.dumps(profile_data, indent=2)
    )

@mcp_resource("goal_context")
async def get_goal_context(user_id: str, goal_id: int) -> Resource:
    """Get detailed context for a specific goal"""
    goal = await goals_service.get_goal(user_id, goal_id)
    tasks = await tasks_service.list_tasks(user_id, goal_id=goal_id)
    progress = await calculate_goal_progress(goal_id)
    
    context_data = {
        "goal": goal.dict(),
        "tasks": [t.dict() for t in tasks],
        "progress": progress,
        "timeline": await get_goal_timeline(goal_id)
    }
    
    return Resource(
        uri=f"selfos://goals/{goal_id}/context",
        name=f"Goal: {goal.title}",
        description="Complete goal context with tasks and progress",
        mimeType="application/json", 
        text=json.dumps(context_data, indent=2)
    )
```

#### Dynamic Data Resources
```python
@mcp_resource("daily_summary")
async def get_daily_summary(user_id: str, date: str = None) -> Resource:
    """Get daily summary for user"""
    target_date = datetime.fromisoformat(date) if date else datetime.utcnow()
    
    summary = await generate_daily_summary(user_id, target_date)
    
    return Resource(
        uri=f"selfos://users/{user_id}/daily/{target_date.isoformat()}",
        name=f"Daily Summary - {target_date.strftime('%Y-%m-%d')}",
        description="Daily activity summary and insights",
        mimeType="text/markdown",
        text=summary
    )
```

### Phase 5: Security and Authentication (Week 5-6)

#### Permission System
```python
class MCPPermissions:
    """MCP permission management system"""
    
    PERMISSION_LEVELS = {
        "read_only": {
            "allowed_tools": [
                "list_goals", "list_tasks", "search_memory",
                "query_user_stats", "get_user_profile"
            ],
            "allowed_resources": ["user_profile", "goal_context", "daily_summary"]
        },
        "read_write": {
            "allowed_tools": [
                "*_goals", "*_tasks", "*_memory", 
                "query_user_stats", "analyze_progress"
            ],
            "allowed_resources": ["*"]
        },
        "admin": {
            "allowed_tools": ["*"],
            "allowed_resources": ["*"]
        }
    }
    
    @classmethod
    async def check_permission(
        cls, 
        user_id: str, 
        tool_name: str, 
        client_info: Dict
    ) -> bool:
        """Check if client has permission for tool"""
        client_permissions = await cls.get_client_permissions(client_info)
        return cls.is_allowed(tool_name, client_permissions)
```

#### Secure Authentication
```python
class MCPAuthProvider:
    """Authentication provider for MCP connections"""
    
    async def authenticate_client(
        self, 
        credentials: Dict
    ) -> Tuple[bool, Optional[str]]:
        """Authenticate MCP client connection"""
        
        if credentials.get("type") == "firebase_token":
            # Validate Firebase ID token
            try:
                decoded_token = auth.verify_id_token(credentials["token"])
                return True, decoded_token["uid"]
            except Exception:
                return False, None
                
        elif credentials.get("type") == "api_key":
            # Validate API key
            api_key = credentials.get("key")
            user_id = await self.validate_api_key(api_key)
            return user_id is not None, user_id
            
        return False, None
```

### Phase 6: Integration and Testing (Week 6-7)

#### FastAPI MCP Integration
```python
# apps/backend_api/mcp_integration.py
from fastapi import FastAPI
from mcp.server.fastapi import MCPRoute

app = FastAPI()

# Add MCP endpoints
app.add_route("/mcp/sse", MCPRoute(mcp_server, transport="sse"))
app.add_route("/mcp/ws", MCPRoute(mcp_server, transport="websocket"))

# Health check for MCP
@app.get("/mcp/health")
async def mcp_health():
    return {
        "status": "healthy",
        "server": "selfos-mcp-server",
        "version": "1.0.0",
        "capabilities": mcp_server.get_capabilities()
    }
```

#### Client Testing
```python
# test_mcp_client.py
import asyncio
from mcp import ClientSession

async def test_mcp_integration():
    """Test MCP client integration"""
    
    async with ClientSession("stdio", "python -m selfos.mcp_server") as session:
        # Test tool calling
        result = await session.call_tool(
            "list_goals",
            {"user_id": "test_user", "limit": 5}
        )
        assert len(result["content"]) <= 5
        
        # Test resource access
        resource = await session.read_resource(
            "selfos://users/test_user/profile"
        )
        assert resource.mimeType == "application/json"
        
        # Test AI integration
        goal_result = await session.call_tool(
            "decompose_goal",
            {
                "user_id": "test_user",
                "goal_description": "Learn Python programming"
            }
        )
        assert "suggested_tasks" in goal_result["content"]
```

## 5. Advanced Features and Use Cases

### AI Agent Workflows
```python
# Example: AI-powered daily planning
async def ai_daily_planning_workflow(user_id: str):
    """AI agent workflow for daily planning"""
    
    # 1. Get user context
    profile = await mcp_client.read_resource(f"user_profile#{user_id}")
    daily_summary = await mcp_client.read_resource(f"daily_summary#{user_id}")
    
    # 2. Analyze current tasks and goals
    pending_tasks = await mcp_client.call_tool("list_tasks", {
        "user_id": user_id,
        "status": "pending",
        "limit": 20
    })
    
    # 3. AI generates optimized daily plan
    plan = await ai_agent.generate_daily_plan(
        context={
            "user_profile": profile,
            "pending_tasks": pending_tasks,
            "yesterday_summary": daily_summary
        }
    )
    
    # 4. Create or update tasks based on plan
    for task_update in plan["task_updates"]:
        await mcp_client.call_tool("update_task", task_update)
    
    return plan
```

### Third-Party Integrations
```python
# Example: Calendar integration via MCP
@mcp_tool("sync_with_calendar")
async def sync_with_calendar(
    user_id: str,
    calendar_provider: str = "google"
) -> Dict:
    """Sync tasks and goals with external calendar"""
    
    # Get user's tasks and goals
    tasks = await mcp_client.call_tool("list_tasks", {
        "user_id": user_id,
        "status": "pending"
    })
    
    # Sync with calendar API
    calendar_events = await calendar_api.sync_tasks(tasks)
    
    return {
        "synced_events": len(calendar_events),
        "status": "completed"
    }
```

## 6. Performance and Scalability

### Connection Management
```python
class MCPConnectionManager:
    """Manage multiple MCP client connections"""
    
    def __init__(self):
        self.connections = {}
        self.connection_pool = asyncio.Semaphore(100)  # Max 100 concurrent
        
    async def handle_connection(self, client_id: str, transport):
        """Handle new MCP connection with rate limiting"""
        async with self.connection_pool:
            try:
                self.connections[client_id] = {
                    "transport": transport,
                    "created_at": datetime.utcnow(),
                    "last_activity": datetime.utcnow()
                }
                await self.serve_client(client_id, transport)
            finally:
                self.connections.pop(client_id, None)
```

### Caching Strategy
```python
class MCPCache:
    """Intelligent caching for MCP responses"""
    
    CACHE_POLICIES = {
        "user_profile": {"ttl": 300, "invalidate_on": ["user_update"]},
        "daily_summary": {"ttl": 3600, "invalidate_on": ["task_complete"]},
        "goal_context": {"ttl": 600, "invalidate_on": ["goal_update", "task_update"]}
    }
    
    async def get_cached_resource(self, resource_uri: str) -> Optional[Resource]:
        """Get cached resource if valid"""
        cache_key = f"mcp:resource:{resource_uri}"
        cached_data = await redis.get(cache_key)
        
        if cached_data:
            return Resource.parse_raw(cached_data)
        return None
```

## 7. Monitoring and Observability

### MCP Analytics
```python
class MCPAnalytics:
    """Analytics and monitoring for MCP usage"""
    
    async def track_tool_usage(
        self,
        user_id: str,
        tool_name: str,
        duration: float,
        success: bool
    ):
        """Track tool usage metrics"""
        await metrics_service.increment(
            "mcp.tool.calls",
            tags={
                "tool": tool_name,
                "user_id": user_id,
                "success": success
            }
        )
        
        await metrics_service.histogram(
            "mcp.tool.duration",
            duration,
            tags={"tool": tool_name}
        )
```

### Health Monitoring
```python
@app.get("/mcp/metrics")
async def mcp_metrics():
    """MCP server metrics endpoint"""
    return {
        "active_connections": len(connection_manager.connections),
        "total_tools": len(mcp_server.list_tools()),
        "total_resources": len(mcp_server.list_resources()),
        "uptime": time.time() - server_start_time,
        "memory_usage": psutil.Process().memory_info().rss
    }
```

## 8. Implementation Timeline

### Phase 1: Foundation (Weeks 1-2)
- [ ] Set up MCP server infrastructure
- [ ] Implement basic transport layers (stdio, SSE, WebSocket)
- [ ] Create authentication and permission system
- [ ] Basic health monitoring and logging

### Phase 2: Core Tools (Weeks 2-3)  
- [ ] Implement Goals API tools (CRUD operations)
- [ ] Implement Tasks API tools (CRUD operations)
- [ ] Implement AI integration tools (decompose_goal, etc.)
- [ ] Add basic error handling and validation

### Phase 3: Database Access (Weeks 3-4)
- [ ] Implement safe database query tools
- [ ] Add analytics and reporting tools
- [ ] Create backup and export tools
- [ ] Implement data validation and sanitization

### Phase 4: Resources (Weeks 4-5)
- [ ] User profile and context resources
- [ ] Goal and task context resources
- [ ] Dynamic daily/weekly summary resources
- [ ] Real-time data resources

### Phase 5: Security & Testing (Weeks 5-6)
- [ ] Comprehensive security audit
- [ ] Permission system testing
- [ ] Load testing and performance optimization
- [ ] Integration testing with AI clients

### Phase 6: Integration (Weeks 6-7)
- [ ] FastAPI MCP endpoint integration
- [ ] AI agent workflow implementation
- [ ] Third-party integration examples
- [ ] Documentation and developer guides

### Phase 7: Production (Week 7-8)
- [ ] Production deployment configuration
- [ ] Monitoring and alerting setup
- [ ] Performance optimization
- [ ] User acceptance testing

## 9. Success Metrics

### Technical Metrics
- **Response Time**: <100ms for tool calls, <500ms for complex queries
- **Throughput**: Support 1000+ concurrent connections
- **Reliability**: 99.9% uptime for MCP server
- **Security**: Zero security incidents, proper access control

### User Experience Metrics  
- **AI Agent Effectiveness**: >90% successful tool calls
- **Integration Adoption**: >50% of power users use MCP clients
- **Developer Experience**: <30min setup time for new integrations
- **Performance**: Users report improved AI interaction quality

### Business Metrics
- **Feature Usage**: MCP tools used in >80% of AI interactions
- **Developer Adoption**: >10 third-party MCP clients built
- **User Retention**: Increased by >25% with MCP features
- **Support Reduction**: 40% fewer API-related support tickets

## 10. Future Roadmap

### Advanced AI Capabilities
- **Multi-Agent Workflows**: Coordinated AI agents using MCP
- **Learning and Adaptation**: AI agents that learn user preferences
- **Proactive Assistance**: AI agents that anticipate user needs
- **Cross-Platform Integration**: MCP bridges for other protocols

### Enterprise Features
- **Team MCP Servers**: Shared tools and resources for teams
- **Advanced Analytics**: Comprehensive MCP usage analytics
- **Custom Tool Development**: SDK for custom tool development
- **Enterprise Security**: SSO, audit logging, compliance features

### Ecosystem Development
- **MCP Marketplace**: Curated tools and integrations
- **Community Contributions**: Open-source tool ecosystem
- **Plugin Architecture**: Extensible MCP server framework
- **Standards Compliance**: Full MCP specification compliance

---

This MCP implementation will position SelfOS as a leading platform for AI-native productivity tools, providing secure, standardized access to user data and enabling sophisticated AI agent workflows that truly understand and assist with personal productivity and life management.
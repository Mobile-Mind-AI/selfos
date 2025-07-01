# SelfOS MCP Server Documentation

**Model Context Protocol (MCP) Server for AI-Powered SelfOS Integration**

## Overview

The SelfOS MCP Server implements Anthropic's Model Context Protocol to provide standardized AI integration with user data and APIs. This enables sophisticated AI interactions with personal goals, projects, tasks, and other data through a secure, protocol-compliant interface.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    SelfOS MCP Server                        │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ Goals Tools │  │ Projects    │  │ AI Tools    │         │
│  │ (Complete)  │  │ Tools       │  │ (Framework) │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ Security    │  │ Auth        │  │ Permissions │         │
│  │ Manager     │  │ Provider    │  │ Engine      │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ stdio       │  │ SSE         │  │ WebSocket   │         │
│  │ Transport   │  │ Transport   │  │ Transport   │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   SelfOS Core Services                      │
├─────────────────────────────────────────────────────────────┤
│  FastAPI Backend  │  PostgreSQL DB  │  Redis Cache         │
│  Firebase Auth    │  Weaviate       │  Event System        │
└─────────────────────────────────────────────────────────────┘
```

## Features

### ✅ Implemented Features

#### **MCP Tools (API Access)**
- **Goals API**: Complete CRUD operations
  - `goals_list`: List user goals with filtering
  - `goals_get`: Get specific goal details
  - `goals_create`: Create new goals
  - `goals_update`: Update existing goals
  - `goals_delete`: Delete goals
  - `goals_search`: Search goals by keywords

- **Projects API**: Basic framework (extensible)
  - `projects_list`: List user projects
  - `projects_get`: Get project details
  - `projects_progress`: Get progress analytics

- **Tasks API**: Basic framework (extensible)
  - `tasks_list`: List user tasks
  - `tasks_get`: Get task details

- **AI Tools**: Framework for AI operations
  - `ai_decompose_goal`: Break down goals into tasks
  - `ai_suggest_tasks`: Suggest next actions
  - `ai_analyze_progress`: Progress insights

#### **MCP Resources (Data Context)**
- **User Resources**: Profile and daily summaries
- **Context Resources**: Goal and project contexts
- **Dynamic URIs**: Flexible resource addressing

#### **Security & Authentication**
- **Firebase Integration**: Token-based authentication
- **API Key Support**: For development and testing
- **Role-Based Permissions**: Read-only, read-write, admin
- **Rate Limiting**: Configurable request limits
- **Input Validation**: SQL injection prevention
- **Audit Logging**: Security event tracking

#### **Transport Layers**
- **stdio**: For local AI agents and CLI tools
- **SSE**: Server-Sent Events for web clients
- **WebSocket**: Real-time bidirectional communication
- **FastAPI Integration**: HTTP endpoints with CORS

#### **Configuration & Deployment**
- **Environment Variables**: Flexible configuration
- **Docker Support**: Complete containerization
- **Health Checks**: Monitoring and diagnostics
- **Comprehensive Testing**: 37 passing unit tests

### 🚧 Planned Extensions

- **Complete Projects/Tasks Tools**: Full CRUD operations
- **Memory/RAG Integration**: Vector search capabilities
- **Real-time Notifications**: Event-driven updates
- **Advanced AI Tools**: Goal decomposition, smart suggestions
- **Resource Subscriptions**: Live data updates
- **Custom Tool Framework**: Plugin architecture

## Quick Start

### Docker (Recommended)
```bash
# Start with all services
docker-compose up --build

# Start MCP server only
docker-compose up --build mcp-server

# Access points:
# - Backend: http://localhost:8000
# - MCP Server: http://localhost:8001
# - Health: http://localhost:8001/health
```

### Local Development
```bash
cd apps/mcp_server

# Install dependencies (from backend_api)
cd ../backend_api && pip install -r requirements.txt
cd ../mcp_server

# Run tests
python run_tests.py

# Start server
python fastapi_integration.py --port 8001
```

### Using the Startup Script
```bash
cd apps/mcp_server
./start_mcp_server.sh docker      # Docker mode (starts backend + MCP)
./start_mcp_server.sh standalone  # Local development
./start_mcp_server.sh test        # Run tests
```

## API Reference

### Health Check
```bash
GET http://localhost:8001/health
```
Response:
```json
{
  "status": "healthy",
  "server": "selfos-mcp-server",
  "version": "1.0.0",
  "capabilities": { ... }
}
```

### Capabilities
```bash
GET http://localhost:8001/mcp/capabilities
```
Response:
```json
{
  "tools": {
    "goals": ["create", "list", "update", "delete", "search"],
    "projects": ["list", "get", "progress"],
    "tasks": ["list", "get"],
    "ai": ["decompose_goal", "suggest_tasks", "analyze_progress"]
  },
  "resources": {
    "user_profile": "Complete user context and preferences",
    "goal_context": "Detailed goal information with tasks",
    "daily_summary": "Daily activity summary"
  },
  "transports": ["stdio", "sse", "websocket"],
  "authentication": ["firebase_token", "api_key"]
}
```

### WebSocket Connection
```javascript
const ws = new WebSocket('ws://localhost:8001/mcp/ws');

// Initialize connection
ws.send(JSON.stringify({
  "jsonrpc": "2.0",
  "method": "initialize",
  "id": 1,
  "params": {
    "clientInfo": {"name": "my-client", "version": "1.0.0"}
  }
}));

// List available tools
ws.send(JSON.stringify({
  "jsonrpc": "2.0",
  "method": "tools/list",
  "id": 2
}));

// Call a tool
ws.send(JSON.stringify({
  "jsonrpc": "2.0",
  "method": "tools/call",
  "id": 3,
  "params": {
    "name": "goals_list",
    "arguments": {
      "user_id": "your-user-id",
      "limit": 10
    }
  }
}));
```

## Configuration

### Environment Variables
```bash
# Database
DATABASE_URL=postgresql://selfos:selfos@localhost/selfos_dev

# Firebase Authentication
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json

# MCP Server Settings
MCP_LOG_LEVEL=INFO
MCP_MAX_CONNECTIONS=100
MCP_REQUIRE_AUTH=true
MCP_ALLOWED_ORIGINS=localhost,example.com

# Transport Configuration
MCP_STDIO_ENABLED=true
MCP_SSE_ENABLED=true
MCP_WEBSOCKET_ENABLED=true
```

### Security Configuration
```python
# Permission levels
PERMISSION_LEVELS = {
    "read_only": {
        "allowed_tools": ["goals_list", "goals_get", "goals_search"],
        "allowed_resources": ["user_profile", "goal_context"]
    },
    "read_write": {
        "allowed_tools": ["goals_*", "projects_*", "tasks_*"],
        "allowed_resources": ["*"]
    },
    "admin": {
        "allowed_tools": ["*"],
        "allowed_resources": ["*"]
    }
}
```

## Development

### File Structure
```
apps/mcp_server/
├── server.py              # Main MCP server implementation
├── config.py              # Configuration management
├── auth.py                # Authentication provider
├── security.py            # Security and permissions
├── cli.py                 # Command-line interface
├── fastapi_integration.py # FastAPI web server
├── test_server.py         # Basic server tests
├── run_tests.py          # Test runner
├── tools/                 # MCP tool implementations
│   ├── base_tools.py      # Base tool handler
│   ├── goals_tools.py     # Goals API tools (complete)
│   ├── projects_tools.py  # Projects API tools
│   ├── tasks_tools.py     # Tasks API tools
│   └── ai_tools.py        # AI service tools
├── resources/             # MCP resource handlers
│   ├── user_resources.py  # User profile resources
│   └── context_resources.py # Context data resources
├── transport/             # Transport implementations
│   ├── stdio_transport.py # Standard I/O
│   ├── sse_transport.py   # Server-Sent Events
│   └── websocket_transport.py # WebSocket
└── tests/                 # Comprehensive test suite
    ├── test_server.py     # Core server tests
    ├── test_tools.py      # Tool handler tests
    ├── test_security.py   # Security tests
    └── test_config.py     # Configuration tests
```

### Adding New Tools
1. Create tool handler in `tools/`
2. Inherit from `BaseToolsHandler`
3. Implement `list_tools()` and `call_tool()` methods
4. Register in `server.py`
5. Add tests in `tests/`

Example:
```python
class MyToolsHandler(BaseToolsHandler):
    async def list_tools(self) -> List[Tool]:
        return [Tool(name="my_tool", ...)]
    
    async def call_tool(self, name: str, arguments: Dict) -> Dict:
        if name == "my_tool":
            return await self._handle_my_tool(arguments)
        return {"error": f"Unknown tool: {name}"}
```

### Testing
```bash
# Run all tests
python run_tests.py

# Run specific test types
python run_tests.py --type unit
python run_tests.py --coverage

# Run specific test files
python -m pytest tests/test_tools.py -v
python -m pytest tests/test_security.py::TestMCPPermissions -v
```

## Security Considerations

### Authentication
- Firebase ID tokens for production
- API keys for development/testing
- Session-based authentication for web clients

### Authorization
- Role-based access control (RBAC)
- Tool-level permissions
- Resource-level permissions
- User data isolation

### Input Validation
- SQL injection prevention
- XSS protection
- Rate limiting
- Request size limits

### Audit Logging
- All tool calls logged
- Authentication events tracked
- Permission violations recorded
- Performance metrics collected

## Monitoring

### Health Checks
```bash
# Server health
curl http://localhost:8001/health

# Detailed metrics
curl http://localhost:8001/mcp/capabilities

# Connection status
curl http://localhost:8001/mcp/metrics
```

### Logging
- Structured JSON logging
- Configurable log levels
- Separate audit logs
- Performance tracking

## Troubleshooting

### Common Issues

1. **Import Errors**
   - Ensure `PYTHONPATH` includes `backend_api`
   - Check that dependencies are installed

2. **Database Connection Issues**
   - Verify `DATABASE_URL` environment variable
   - Ensure PostgreSQL is running
   - Check database permissions

3. **Authentication Failures**
   - Verify Firebase service account key
   - Check `GOOGLE_APPLICATION_CREDENTIALS` path
   - Validate API key format

4. **Transport Issues**
   - Check port availability (8001)
   - Verify firewall settings
   - Check CORS configuration

### Debug Mode
```bash
# Run with debug logging
python fastapi_integration.py --log-level DEBUG

# Test basic functionality
python test_server.py

# Check configuration
python -c "from config import MCPConfig; print(MCPConfig().validate())"
```

## Contributing

1. Follow the existing code structure
2. Add comprehensive tests for new features
3. Update documentation
4. Ensure security best practices
5. Test with multiple transport layers

## License

Part of the SelfOS project - see main repository for license information.
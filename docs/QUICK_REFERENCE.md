# SelfOS Quick Reference Guide

**Essential commands and endpoints for SelfOS development**

## 🚀 Quick Start

### Start Everything
```bash
# Core services (Backend + Database)
docker-compose up --build

# Add MCP server for AI integration
docker-compose up --build backend mcp-server

# Add frontend
docker-compose --profile frontend up --build

# Or use convenience script
./apps/mcp_server/start_mcp_server.sh docker
```

### Health Checks
```bash
curl http://localhost:8000/        # Backend API
curl http://localhost:8001/health  # MCP Server
```

## 🧪 Testing

### Backend API Tests
```bash
cd apps/backend_api
python run_tests.py              # All tests (30+)
python run_tests.py --coverage   # With coverage
pytest tests/unit/test_goals.py  # Specific tests
```

### MCP Server Tests
```bash
cd apps/mcp_server
python run_tests.py              # All tests (37+)
python run_tests.py --type unit  # Unit tests only
python test_server.py            # Basic functionality
```

## 📊 Database Operations

### Migrations
```bash
cd apps/backend_api
alembic upgrade head                        # Apply migrations
alembic revision --autogenerate -m "desc"  # Create migration
alembic history                             # View history
```

### Direct Database Access
```bash
# Connect to PostgreSQL (if running via Docker)
docker exec -it selfos_db_1 psql -U selfos -d selfos_dev

# Common queries
\dt                           # List tables
SELECT * FROM users LIMIT 5; # View users
SELECT * FROM goals WHERE user_id = 'user123';
```

## 🔧 Development Modes

### Backend API Local Development
```bash
cd apps/backend_api
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### MCP Server Local Development
```bash
cd apps/mcp_server
# Requires backend_api dependencies
python fastapi_integration.py --reload --port 8001  # Web server
python cli.py --transport stdio                     # CLI mode
python cli.py --transport websocket                 # WebSocket only
```

## 📝 API Endpoints

### Backend API (Port 8000)
```bash
# Health
GET  /

# Authentication
POST /auth/register
POST /auth/login

# Goals
GET    /api/goals/              # List goals
POST   /api/goals/              # Create goal
GET    /api/goals/{id}          # Get goal
PUT    /api/goals/{id}          # Update goal
DELETE /api/goals/{id}          # Delete goal

# Projects
GET    /api/projects/           # List projects
POST   /api/projects/           # Create project
GET    /api/projects/{id}       # Get project
GET    /api/projects/{id}/progress   # Project progress
GET    /api/projects/{id}/timeline   # Project timeline

# Tasks
GET    /api/tasks/              # List tasks
POST   /api/tasks/              # Create task
GET    /api/tasks/{id}          # Get task
```

### MCP Server (Port 8001)
```bash
# Health & Info
GET /health                     # Server health
GET /mcp/capabilities          # Available tools/resources

# WebSocket
ws://localhost:8001/mcp/ws     # MCP WebSocket endpoint

# Server-Sent Events
GET /mcp/sse                   # MCP SSE endpoint
```

## 🔐 Authentication

### Firebase Setup
```bash
# Set service account key
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/serviceAccountKey.json"

# Test authentication
curl -X POST http://localhost:8000/auth/test \
  -H "Authorization: Bearer YOUR_FIREBASE_TOKEN"
```

### API Key (Development)
```bash
# Format: sk-selfos-{user_id}-{random}
API_KEY="sk-selfos-user123-randomstring"

# Use with MCP server
curl -X POST http://localhost:8001/mcp/authenticate \
  -H "Content-Type: application/json" \
  -d '{"type": "api_key", "key": "'$API_KEY'"}'
```

## 🛠️ MCP Protocol Usage

### WebSocket Client Example
```javascript
const ws = new WebSocket('ws://localhost:8001/mcp/ws');

// Initialize
ws.send(JSON.stringify({
  "jsonrpc": "2.0",
  "method": "initialize",
  "id": 1,
  "params": {"clientInfo": {"name": "my-client", "version": "1.0.0"}}
}));

// List tools
ws.send(JSON.stringify({
  "jsonrpc": "2.0", "method": "tools/list", "id": 2
}));

// Call goals_list tool
ws.send(JSON.stringify({
  "jsonrpc": "2.0",
  "method": "tools/call",
  "id": 3,
  "params": {
    "name": "goals_list",
    "arguments": {"user_id": "user123", "limit": 10}
  }
}));
```

### Python MCP Client Example
```python
import asyncio
import json
import websockets

async def mcp_client():
    uri = "ws://localhost:8001/mcp/ws"
    async with websockets.connect(uri) as websocket:
        # Initialize
        await websocket.send(json.dumps({
            "jsonrpc": "2.0",
            "method": "initialize",
            "id": 1,
            "params": {"clientInfo": {"name": "python-client"}}
        }))
        
        # Get response
        response = await websocket.recv()
        print(json.loads(response))

asyncio.run(mcp_client())
```

## 📁 File Structure Reference

### Key Directories
```
apps/
├── backend_api/           # Main FastAPI backend
│   ├── main.py           # FastAPI app
│   ├── models.py         # SQLAlchemy models
│   ├── schemas.py        # Pydantic schemas
│   ├── routers/          # API endpoints
│   └── tests/            # Backend tests
├── mcp_server/           # MCP server
│   ├── server.py         # Main MCP server
│   ├── tools/            # MCP tools
│   ├── resources/        # MCP resources
│   ├── transport/        # Transport layers
│   └── tests/            # MCP tests
└── selfos/               # Flutter frontend (future)

infra/
├── docker/               # Dockerfiles
└── k8s/                 # Kubernetes configs (future)

docs/                     # Documentation
├── MCP_SERVER.md        # MCP server docs
└── QUICK_REFERENCE.md   # This file
```

### Important Files
```
docker-compose.yml        # Service orchestration
start_mcp_server.sh      # Startup convenience script
CLAUDE.md                # Developer instructions
README.md                # Project overview
.env                     # Environment variables
```

## 🐛 Troubleshooting

### Common Issues

**Import errors:**
```bash
# Fix Python path issues
export PYTHONPATH="/path/to/selfos/apps/backend_api:$PYTHONPATH"
cd apps/mcp_server && python test_server.py
```

**Database connection:**
```bash
# Check if PostgreSQL is running
docker ps | grep postgres
# Check connection
psql postgresql://selfos:selfos@localhost:5432/selfos_dev
```

**Port conflicts:**
```bash
# Check what's using ports
lsof -i :8000  # Backend API
lsof -i :8001  # MCP Server
lsof -i :5432  # PostgreSQL
```

**Firebase authentication:**
```bash
# Check service account key
echo $GOOGLE_APPLICATION_CREDENTIALS
ls -la $GOOGLE_APPLICATION_CREDENTIALS
```

### Debug Commands
```bash
# Backend API debug
cd apps/backend_api
uvicorn main:app --reload --log-level debug

# MCP Server debug
cd apps/mcp_server
python fastapi_integration.py --log-level DEBUG

# Database debug
docker logs selfos_db_1
docker logs selfos_mcp-server_1
```

## 📊 Monitoring

### Logs
```bash
# Backend logs
docker logs selfos_backend_1 -f

# MCP server logs
docker logs selfos_mcp-server_1 -f

# Database logs
docker logs selfos_db_1 -f

# All logs
docker-compose logs -f
```

### Metrics
```bash
# Server health
curl http://localhost:8000/health
curl http://localhost:8001/health

# Detailed capabilities
curl http://localhost:8001/mcp/capabilities | jq

# Database stats
docker exec selfos_db_1 psql -U selfos -d selfos_dev -c "
  SELECT schemaname,tablename,n_tup_ins,n_tup_upd,n_tup_del 
  FROM pg_stat_user_tables;"
```

## 🚀 Deployment

### Environment Variables
```bash
# Required
export DATABASE_URL="postgresql://user:pass@host:5432/db"
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/firebase-key.json"

# Optional
export MCP_LOG_LEVEL="INFO"
export MCP_MAX_CONNECTIONS="100"
export REDIS_URL="redis://localhost:6379"
```

### Production Checklist
- [ ] Set strong database passwords
- [ ] Configure Firebase for production domain
- [ ] Set up SSL/TLS certificates
- [ ] Configure CORS properly
- [ ] Set up monitoring and alerting
- [ ] Configure backup strategy
- [ ] Set resource limits
- [ ] Enable logging aggregation

---

**Need help?** Check the full documentation in `docs/` or run tests to verify your setup!
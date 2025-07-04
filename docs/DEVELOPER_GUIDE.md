# SelfOS Developer Guide

This comprehensive guide covers everything you need to know to develop, deploy, and maintain SelfOS effectively.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Development Environment](#development-environment)
3. [Command Reference](#command-reference)
4. [Development Workflows](#development-workflows)
5. [Testing](#testing)
6. [Troubleshooting](#troubleshooting)

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Git
- Python 3.11+ (for local development)
- Node.js 18+ (for frontend development)

### 30-Second Setup

```bash
# Clone and start the stack
git clone <repository-url>
cd selfos
docker-compose up --build

# Verify services
curl http://localhost:8000/  # Backend API
curl http://localhost:8001/health  # MCP Server
```

Expected responses:
- Backend API: `{"message": "SelfOS Backend API"}`
- MCP Server: `{"status": "healthy", "server": "selfos-mcp-server"}`

## Development Environment

### Docker Development (Recommended)

#### Core Services
```bash
# Start core services (PostgreSQL, Redis, Backend API)
docker-compose up --build

# Start with MCP server for AI integration
docker-compose up --build backend mcp-server

# Start with frontend (Flutter web)
docker-compose --profile frontend up --build
```

#### Service-Specific Development
```bash
# Backend API only
docker-compose up --build backend

# Database only
docker-compose up --build db

# Full stack with frontend
docker-compose --profile frontend up --build
```

### Local Development

#### Backend API Setup
```bash
cd apps/backend_api
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Run with uvicorn
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### MCP Server Setup
```bash
cd apps/mcp_server

# Run tests
python run_tests.py                    # All tests
python run_tests.py --type unit        # Unit tests only
python run_tests.py --coverage         # With coverage report

# Run MCP server
python cli.py --transport stdio        # For local AI agents
python cli.py --transport websocket    # For WebSocket clients
python fastapi_integration.py          # With FastAPI (Web + WebSocket)
```

### Environment Configuration

#### Required Environment Variables
```bash
# Firebase Authentication
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/serviceAccountKey.json

# Database
DATABASE_URL=postgresql://selfos:selfos@localhost:5432/selfos_dev

# Redis
REDIS_URL=redis://localhost:6379
```

#### Firebase Setup
1. Create Firebase project
2. Enable Authentication
3. Download service account key
4. Mount key in Docker or set `GOOGLE_APPLICATION_CREDENTIALS`

## Command Reference

### Docker Commands

#### Container Management
```bash
# Build and start services
docker-compose up --build

# Start in background
docker-compose up -d

# Stop all services
docker-compose down

# View logs
docker-compose logs backend
docker-compose logs -f mcp-server  # Follow logs

# Restart specific service
docker-compose restart backend
```

#### Database Operations
```bash
# Database migrations (Alembic)
cd apps/backend_api
alembic upgrade head                     # Apply migrations
alembic revision --autogenerate -m "description"  # Create new migration

# Access database directly
docker-compose exec db psql -U selfos -d selfos_dev
```

#### Clean Slate Reset
```bash
# Complete environment reset
docker-compose down -v --remove-orphans
docker system prune -a
docker-compose up --build
```

### Testing Commands

#### Backend API Tests
```bash
cd apps/backend_api

# Quick test commands
python -m pytest tests/ -v               # Run all tests
python run_tests.py                       # Use custom test runner
python run_tests.py --unit                # Unit tests only
python run_tests.py --integration         # Integration tests only
python run_tests.py --coverage            # With coverage report

# Specific test categories
python -m pytest tests/unit/test_auth.py -v      # Authentication tests
python -m pytest tests/unit/test_goals.py -v     # Goals CRUD tests
python -m pytest tests/unit/test_tasks.py -v     # Tasks CRUD tests
python -m pytest tests/test_main.py -v           # Main API tests

# Advanced options
python -m pytest tests/ --tb=short        # Short traceback
python -m pytest tests/ -x                # Stop on first failure
python -m pytest tests/ --lf              # Run last failed tests
```

#### MCP Server Tests
```bash
cd apps/mcp_server

# Run all MCP server tests
python run_tests.py                    # All tests (37 passing)
python run_tests.py --type unit        # Unit tests only
python run_tests.py --coverage         # With coverage report

# Specific test categories
python -m pytest tests/test_server.py -v     # Core server tests
python -m pytest tests/test_tools.py -v      # Tool handler tests
python -m pytest tests/test_security.py -v   # Security and auth tests
python -m pytest tests/test_config.py -v     # Configuration tests
```

### API Development

#### Health Checks
```bash
# Backend API
curl http://localhost:8000/
curl http://localhost:8000/health

# MCP Server
curl http://localhost:8001/health

# Database connectivity
curl http://localhost:8000/api/health/db
```

#### Authentication Testing
```bash
# Test endpoints (requires valid Firebase token)
curl -H "Authorization: Bearer $FIREBASE_TOKEN" \
     http://localhost:8000/api/auth/me

# Test MCP tools
curl -H "Authorization: Bearer $FIREBASE_TOKEN" \
     -X POST http://localhost:8001/api/tools/goals/list \
     -H "Content-Type: application/json" \
     -d '{"user_id": "test-user"}'
```

## Development Workflows

### Feature Development Workflow

1. **Create Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Development Cycle**
   ```bash
   # Start development environment
   docker-compose up --build backend mcp-server
   
   # Make changes and test
   python -m pytest tests/ -v
   
   # Check code quality
   python -m pytest tests/ --coverage
   ```

3. **Database Changes**
   ```bash
   # Create migration
   cd apps/backend_api
   alembic revision --autogenerate -m "Add new feature"
   
   # Apply migration
   alembic upgrade head
   ```

4. **Testing Integration**
   ```bash
   # Run full test suite
   python run_tests.py --coverage
   
   # Test MCP integration
   cd apps/mcp_server
   python run_tests.py
   ```

### Code Quality Standards

#### Python Code Style
```bash
# Format code
black apps/backend_api apps/mcp_server

# Lint code
flake8 apps/backend_api apps/mcp_server

# Type checking
mypy apps/backend_api apps/mcp_server
```

#### Testing Requirements
- **Unit Tests**: All new functions must have unit tests
- **Integration Tests**: API endpoints must have integration tests
- **Coverage**: Maintain >80% test coverage
- **MCP Tests**: All tools must have corresponding tests

### Debugging Workflows

#### Backend API Debugging
```bash
# Enable debug mode
export DEBUG=true
uvicorn main:app --reload --log-level debug

# Database query debugging
export SQL_DEBUG=true

# View detailed logs
docker-compose logs -f backend
```

#### MCP Server Debugging
```bash
# Debug mode
export MCP_DEBUG=true
python fastapi_integration.py

# Test specific tools
python test_server.py
```

## Testing

### Test Structure

#### Backend API Testing
```
tests/
├── conftest.py                    # Shared test configuration
├── test_main.py                   # Main API and health tests
├── unit/                          # Individual component tests
│   ├── test_auth.py              # Firebase authentication (mocked)
│   ├── test_goals.py             # Goals CRUD with database testing
│   └── test_tasks.py             # Tasks CRUD with goal relationships
├── integration/                   # Full workflow tests
│   └── test_integration_goals_and_tasks.py  # End-to-end scenarios
└── run_tests.py                   # Custom test runner script
```

#### Test Database
- Uses in-memory SQLite for fast, isolated testing
- Each test gets clean database state
- No external database setup required
- Tables created automatically from SQLAlchemy models

#### Coverage Status
- ✅ **30+ passing tests** across all categories
- ✅ Authentication with Firebase mocking
- ✅ Goals/Tasks CRUD operations
- ✅ Database relationships and constraints
- ✅ User data isolation
- ✅ Error handling and validation
- ✅ Integration workflows

### MCP Server Testing
- ✅ **37 passing tests** across all MCP components
- ✅ Server initialization and capabilities
- ✅ Tool handlers (Goals, Projects, Tasks, AI)
- ✅ Security permissions and authentication
- ✅ Configuration management
- ✅ Transport layer integration

## Troubleshooting

### Common Issues

#### Docker Issues
```bash
# Port conflicts
docker-compose down
lsof -ti:8000 | xargs kill -9  # Kill process on port 8000

# Permission errors (Linux/macOS)
sudo chown -R $USER:$USER .

# Clean build
docker-compose down -v
docker system prune -a
docker-compose up --build
```

#### Database Issues
```bash
# Reset database
docker-compose down -v
docker-compose up --build db
cd apps/backend_api && alembic upgrade head

# Connection issues
# Check DATABASE_URL environment variable
# Verify PostgreSQL is running: docker-compose ps
```

#### Environment Issues
```bash
# Python dependencies
cd apps/backend_api
pip install -r requirements.txt --force-reinstall

# Firebase authentication
# Verify GOOGLE_APPLICATION_CREDENTIALS path
# Check Firebase project configuration
```

### Debug Commands

#### Service Health
```bash
# Check all services
docker-compose ps

# Service logs
docker-compose logs backend
docker-compose logs mcp-server
docker-compose logs db

# Resource usage
docker stats
```

#### API Debugging
```bash
# Test API endpoints
curl -v http://localhost:8000/health
curl -v http://localhost:8001/health

# Check authentication
export TOKEN="your-firebase-token"
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/auth/me
```

### Performance Optimization

#### Development Performance
```bash
# Use BuildKit for faster builds
export DOCKER_BUILDKIT=1
docker-compose build

# Parallel testing
python -m pytest tests/ -n auto

# Database optimization
# Enable query logging for slow queries
export SQL_DEBUG=true
```

## Next Steps

1. **Read [API_REFERENCE.md](API_REFERENCE.md)** for complete API documentation
2. **Review [ARCHITECTURE.md](ARCHITECTURE.md)** for system design understanding
3. **Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md)** for detailed problem-solving
4. **Explore [MCP_SERVER.md](MCP_SERVER.md)** for AI integration details

---

For questions or issues not covered in this guide, please check the troubleshooting section or create an issue in the repository.
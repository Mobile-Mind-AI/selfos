# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Docker Development
```bash
# Start core services (PostgreSQL, Redis, Backend API)
docker-compose up --build

# Start with MCP server for AI integration
docker-compose up --build backend mcp-server

# Start with frontend (Flutter web)
docker-compose --profile frontend up --build

# Health checks
curl http://localhost:8000/  # Backend API
# Expected: {"message": "SelfOS Backend API"}

curl http://localhost:8001/health  # MCP Server
# Expected: {"status": "healthy", "server": "selfos-mcp-server"}
```

### Backend API Development
```bash
# Local development (requires Python 3.11+)
cd apps/backend_api
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run tests
pytest -q

# Run with uvicorn
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### MCP Server Development
```bash
# Local development (requires Python 3.11+ and backend_api dependencies)
cd apps/mcp_server

# Run tests
python run_tests.py                    # All tests
python run_tests.py --type unit        # Unit tests only
python run_tests.py --coverage         # With coverage report

# Run MCP server standalone
python cli.py --transport stdio        # For local AI agents
python cli.py --transport websocket    # For WebSocket clients
python fastapi_integration.py          # With FastAPI (Web + WebSocket)

# Test server initialization
python test_server.py                  # Basic functionality test
```

### Database Operations
```bash
# Database migrations (Alembic)
cd apps/backend_api
alembic upgrade head        # Apply migrations
alembic revision --autogenerate -m "description"  # Create new migration
```

## Architecture Overview

### Core Components
- **Backend API**: FastAPI application with SQLAlchemy ORM
- **MCP Server**: Model Context Protocol server for AI integration
- **Database**: PostgreSQL with SQLAlchemy models
- **Authentication**: Firebase Admin SDK
- **Caching**: Redis for session storage
- **Frontend**: Flutter multi-platform (web/mobile/desktop)

### Key Services (Planned)
- **AI Engine**: LangChain-based conversational AI
- **Memory Service**: RAG system with vector embeddings
- **Story Engine**: Automated content/video generation
- **Notification Service**: Real-time user notifications
- **RLHF Trainer**: Reinforcement learning from human feedback

### Database Schema
Current tables:
- `users`: Firebase UID, email
- `goals`: User goals with progress tracking, media attachments
- `tasks`: Goal-linked tasks with dependencies, progress tracking
- `memory_items`: User conversation/reflection storage

## Code Structure

### Backend API (`apps/backend_api/`)
- `main.py`: FastAPI application setup, router registration
- `models.py`: SQLAlchemy ORM models
- `schemas.py`: Pydantic request/response schemas
- `db.py`: Database connection and session management
- `dependencies.py`: FastAPI dependencies (auth, database)
- `routers/`: API endpoints organized by domain
  - `auth.py`: Firebase authentication
  - `goals.py`: Goal CRUD operations
  - `tasks.py`: Task management
- `alembic/`: Database migration scripts

### Authentication Flow
1. Frontend registers/authenticates with Firebase
2. Backend verifies Firebase ID tokens
3. User data stored in local PostgreSQL
4. Current user injected via `get_current_user` dependency

### Key Patterns
- **Authentication**: All protected routes use `Depends(get_current_user)`
- **Database**: Session dependency injection with `Depends(get_db)`
- **Row-level Security**: Queries filtered by `current_user["uid"]`
- **Media Handling**: JSON arrays for media URLs in models

## Environment Setup

### Required Environment Variables
```bash
# Firebase Authentication
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/serviceAccountKey.json

# Database
DATABASE_URL=postgresql://selfos:selfos@localhost:5432/selfos_dev

# Redis
REDIS_URL=redis://localhost:6379
```

### Firebase Setup
1. Create Firebase project
2. Enable Authentication
3. Download service account key
4. Mount key in Docker or set `GOOGLE_APPLICATION_CREDENTIALS`

## Testing

### Backend Tests
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

### Test Structure
- `tests/conftest.py`: Shared test configuration
- `tests/test_main.py`: Main API and health tests
- `tests/unit/`: Individual component tests
  - `test_auth.py`: Firebase authentication (mocked)
  - `test_goals.py`: Goals CRUD with database testing
  - `test_tasks.py`: Tasks CRUD with goal relationships
- `tests/integration/`: Full workflow tests
  - `test_integration_goals_and_tasks.py`: End-to-end scenarios
- `run_tests.py`: Custom test runner script
- `TESTING.md`: Comprehensive testing guide

### Test Database
- Uses in-memory SQLite for fast, isolated testing
- Each test gets clean database state
- No external database setup required
- Tables created automatically from SQLAlchemy models

### Test Coverage Status
- ✅ **30+ passing tests** across all categories
- ✅ Authentication with Firebase mocking
- ✅ Goals/Tasks CRUD operations
- ✅ Database relationships and constraints
- ✅ User data isolation
- ✅ Error handling and validation
- ✅ Integration workflows
- ⚠️ **4 failing tests** (auth endpoint edge cases - minor issues)

### MCP Server Tests
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

### MCP Test Coverage Status
- ✅ **37 passing tests** across all MCP components
- ✅ Server initialization and capabilities
- ✅ Tool handlers (Goals, Projects, Tasks, AI)
- ✅ Security permissions and authentication
- ✅ Configuration management
- ✅ Transport layer integration
- ✅ Error handling and validation

## Development Notes

### Current Status
- ✅ **Backend API**: Complete FastAPI backend with authentication
- ✅ **Data Models**: Users, Goals, Projects, Tasks, Life Areas with full relationships
- ✅ **MCP Server**: Model Context Protocol server for AI integration
- ✅ **Database**: PostgreSQL with SQLAlchemy ORM and Alembic migrations
- ✅ **Testing**: Comprehensive test suites (30+ backend, 37+ MCP tests)
- ✅ **Docker**: Complete containerized development environment
- ✅ **AI Ready**: MCP tools for Goals API with security and permissions

### Planned Features
- 🚧 **Projects/Tasks MCP Tools**: Complete CRUD operations via MCP
- 🚧 **AI Engine**: LangChain-based conversational AI integration
- 🚧 **Memory/RAG**: Vector embeddings with Weaviate for personalized responses
- 🚧 **Story Engine**: Automated content/video generation pipeline
- 🚧 **Flutter Frontend**: Multi-platform (web/mobile/desktop) client
- 🚧 **Real-time**: Notifications and live updates
- 🚧 **Social Integration**: Export to TikTok, Instagram, YouTube

### Key Dependencies
- **FastAPI**: Web framework and API gateway
- **MCP**: Model Context Protocol for AI integration
- **SQLAlchemy**: Database ORM with PostgreSQL
- **Alembic**: Database schema migrations
- **Firebase Admin**: Authentication and user management
- **Weaviate**: Vector database for AI memory
- **Redis**: Caching and session storage
- **pytest**: Testing framework with async support
- **uvicorn**: ASGI server for production deployment

### Migration Notes
- Recent migration from `backend-api` to `backend_api` (underscores)
- Dockerfile may reference old `backend-api` path
- Update paths if encountering build issues

## Development Roadmap

### AI & Memory Engine Development (Week 3: Jul 15–21)
- [ ] Define prompt templates for goal decomposition (libs/prompts)
- [ ] ai-engine: implement orchestrator service to call OpenAI/GPT
- [ ] Memory service: integrate Pinecone (or local vector store)
- [ ] API endpoint /ai/decompose-goal
- [ ] Integration tests: simulate chat requests
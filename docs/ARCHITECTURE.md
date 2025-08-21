# SelfOS Architecture Overview

**Version:** v1.1
**Last Updated:** 2025-08-12
**Status:** Updated to reflect current project state

## System Overview

SelfOS is a modular, API-driven personal AI assistant platform designed for conversational life planning, goal management, and memory retrieval.

```
┌─────────────────┐    ┌─────────────────┐
│   Backend API   │◄──►│   AI Services   │
│   (FastAPI)     │    │   (Python)      │
└─────────────────┘    └─────────────────┘
         │                      │
┌─────────────────┐    ┌─────────────────┐
│   Database      │    │   Memory Store  │
│ (PostgreSQL)    │    │ (Vector DB)     │
└─────────────────┘    └─────────────────┘
```

## Core Components

### 1. Backend API (`apps/backend_api/`)
- **Technology**: FastAPI with Python 3.11+
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Authentication**: Firebase Admin SDK
- **API Documentation**: Auto-generated with OpenAPI/Swagger
- **Testing**: pytest, but with significant failures needing attention.

**Status**: 🟢 Core functionality is implemented, but requires testing and bug fixes.

### 2. AI Engine (`apps/ai_engine/`)
- **Technology**: Python with multiple AI provider support
- **Features**: Goal decomposition, Conversational AI, Context awareness.
- **Orchestration**: Provider-agnostic interface.

**Status**: 🟢 Implemented.

### 3. MCP Server (`apps/mcp_server/`)
- **Technology**: Python-based server for the Model Context Protocol.
- **Features**: Extends the AI capabilities with additional tools and resources.

**Status**: 🟢 Implemented.

## Data Architecture

### Database Schema
The database schema is managed with Alembic and includes tables for:
- `users`
- `goals`, `projects`, `tasks` (with hierarchical relationships)
- `life_areas`
- `habits`
- `journal_entries`
- `media_attachments`
- `tags`
- `entities` (for the knowledge graph)
- `assistant_profiles`
- `feedback_logs`
- `story_sessions`
- `user_preferences`

### Performance Optimizations
- **Database Indexes**: Composite indexes are used for common query patterns.
- **Archival Strategy**: A strategy for archiving high-volume tables like `story_sessions` and `feedback_logs` is in place.

## Security Architecture

### Authentication Flow
- User authenticates via Firebase.
- The backend validates the Firebase token.
- All API calls are authorized using this token.

### Security Features
- **JWT Authentication**: Secure, stateless token-based authentication.
- **Input Validation**: Pydantic models provide strict validation.
- **SQL Injection Prevention**: SQLAlchemy ORM ensures parameterized queries.

## Deployment Architecture

### Development Environment
```yaml
# docker-compose.yml
services:
  postgres:     # Database
  redis:        # Caching
  backend_api:  # FastAPI application
  mcp_server:   # MCP Server
```

### Production Architecture (Planned)
A scalable production architecture using container orchestration (like Kubernetes), a load balancer, and a CDN is planned for the future.

## System Assessment & Future Improvements

### Current State
The backend is feature-rich, with most core systems implemented. However, a significant number of tests are failing, indicating potential bugs or integration issues that need to be addressed. The frontend has been removed and will be rebuilt.

### Immediate Action Items
1.  **Fix Failing Tests**: This is the highest priority. The test suite must be stable to ensure reliability.
2.  **Review and Refactor**: With the core features in place, a review of the codebase for consistency and best practices is recommended.
3.  **Rebuild Frontend**: Plan and begin development of the new UI.

### Long-term Vision
- **Advanced AI Features**: Proactive suggestions, habit analysis, and more.
- **Third-party Integrations**: Connect with other services like calendars and note-taking apps.
- **Enterprise Features**: Role-based access control, audit logging, and SSO.

## Development Principles

- **Clean Architecture**: Maintain a clear separation of concerns.
- **Testing**: Ensure high test coverage and a stable test suite.
- **Documentation**: Keep documentation up-to-date with the codebase.

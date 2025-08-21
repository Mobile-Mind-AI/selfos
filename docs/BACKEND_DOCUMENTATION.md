# Backend API Documentation

**Version:** 1.1
**Last Updated:** 2025-08-12

## Overview
The SelfOS Backend API is a FastAPI-based service that provides comprehensive personal management features including goals, projects, tasks, life areas, habits, journal entries, and AI-powered assistance.

## Architecture

### Core Components
- **FastAPI Framework**: Modern, fast web framework for building APIs.
- **SQLAlchemy ORM**: Database abstraction and query builder.
- **Alembic**: Database migration management.
- **Firebase Admin SDK**: Authentication and user management.
- **Redis**: Caching and session storage.
- **PostgreSQL**: Primary database.

### Project Structure
```
apps/backend_api/
├── main.py                 # FastAPI application entry point
├── db.py                   # Database connection and session management
├── dependencies.py         # FastAPI dependencies (auth, database)
├── config.py               # Centralized configuration management
├── models/                 # SQLAlchemy ORM models (now modularized)
├── routers/                # API endpoints for each resource
├── services/               # Business logic services
├── schemas/                # Pydantic models for validation
├── alembic/                # Database migrations
└── tests/                  # Test suites
```

## Database Schema

The database schema is managed via Alembic and includes models for all core features of the application. The models have been modularized for clarity and maintainability.

### Core Models
- **User**: Manages user data and authentication.
- **Goals, Projects, Tasks**: Hierarchical structures for planning and execution.
- **Life Areas**: For categorizing and balancing life goals.
- **Habits**: For tracking and building routines.
- **Journal**: For personal reflection.
- **Entities**: Forms the basis of the knowledge graph.
- **Media Attachments**: For linking files to other resources.
- **Tags**: For flexible categorization.
- **User Preferences**: For customizing the user experience.
- **Assistant Profiles**: For personalizing AI interactions.

## Services Layer

The services layer encapsulates the business logic of the application, keeping the routers thin and focused on handling HTTP requests.

- **`goal_service.py`**: Manages goal hierarchy and progress.
- **`project_service.py`**: Manages project hierarchy and progress.
- **`task_service.py`**: Manages task dependencies.
- **`entity_extraction.py`**: Handles NLP-based entity extraction.
- **`preferences_service.py`**: Manages user preferences and history.

## API Endpoints

The API is organized into routers, each corresponding to a specific resource. For a complete and up-to-date list of endpoints, please refer to `docs/API_REFERENCE.md` or the interactive Swagger documentation available at `/docs` when the server is running.

## Database Migrations

Database schema changes are managed with Alembic.

### Running Migrations
```bash
# Apply all migrations
alembic upgrade head

# Create a new migration after model changes
alembic revision --autogenerate -m "Your migration message"
```

## Testing

The project uses `pytest` for testing.

### Running Tests
```bash
# From the apps/backend_api directory
python run_tests.py
```

### Test Status
A significant number of tests are currently failing. Resolving these failures is a top priority to ensure the stability and reliability of the backend.

## Development Workflow

### Local Development
1.  **Install dependencies**: `pip install -r requirements.txt`
2.  **Run migrations**: `alembic upgrade head`
3.  **Start the server**: `uvicorn main:app --reload`

### Docker Development
Use `docker-compose up --build` to build and start all services.

## Performance and Optimization

### Database Indexing
The database schema is heavily indexed to ensure fast query performance. Key indexing strategies include:
- Composite indexes on `(user_id, created_at)` for most tables.
- Indexes on foreign key relationships.
- Status and type field indexes for efficient filtering.

### Archival Strategy
A data archival strategy is in place for high-volume tables like `story_sessions` and `feedback_logs` to maintain performance over time. A `manage_db.py` script is available for managing this process.

---

*This document provides a high-level overview. For more specific details, please refer to the source code and the other documentation files.*

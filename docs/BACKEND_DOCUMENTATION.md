# Backend API Documentation

## Overview
The SelfOS Backend API is a FastAPI-based service that provides comprehensive personal management features including goals, projects, tasks, life areas, habits, journal entries, and AI-powered assistance.

## Architecture

### Core Components
- **FastAPI Framework**: Modern, fast web framework for building APIs
- **SQLAlchemy ORM**: Database abstraction and query builder
- **Alembic**: Database migration management
- **Firebase Admin SDK**: Authentication and user management
- **Redis**: Caching and session storage
- **PostgreSQL**: Primary database

### Project Structure
```
apps/backend_api/
├── main.py                 # FastAPI application entry point
├── db.py                   # Database connection and session management
├── dependencies.py         # FastAPI dependencies (auth, database)
├── config.py              # Centralized configuration management
├── middleware.py          # Custom middleware (error handling, logging, rate limiting)
├── models/                # SQLAlchemy ORM models
│   ├── base.py           # Base model class
│   ├── user.py           # User model
│   ├── goals.py          # Goal model with hierarchy support
│   ├── projects.py       # Project model with hierarchy support
│   ├── tasks.py          # Task model with dependencies
│   ├── life_areas.py     # Life areas (categories)
│   ├── preferences.py    # User preferences and history
│   ├── habits.py         # Habits and completions
│   ├── journal.py        # Journal entries
│   ├── tags.py           # Tagging system
│   ├── entities.py       # Knowledge graph entities
│   ├── assistant.py      # AI assistant profiles
│   ├── conversation.py   # Conversation logs and sessions
│   └── content.py        # Media, memory, stories, feedback
├── routers/               # API endpoints
│   ├── auth.py           # Authentication endpoints
│   ├── goals.py          # Goals CRUD operations
│   ├── projects.py       # Projects management
│   ├── tasks.py          # Tasks management
│   ├── life_areas.py     # Life areas management
│   ├── entities.py       # Entity management (TODO)
│   └── ...               # Other routers
├── services/              # Business logic services
│   ├── goal_service.py   # Goal hierarchy operations
│   ├── project_service.py # Project hierarchy operations
│   ├── task_service.py   # Task dependency management
│   ├── entity_extraction.py # NLP entity extraction
│   └── ...               # Other services
├── schemas/               # Pydantic models for validation
├── alembic/              # Database migrations
└── tests/                # Test suites
```

## Database Schema

### Core Models

#### User
- Primary user model linked to Firebase authentication
- Relationships with all user-owned data
- System user ('system') for shared default data

#### Goals
- Hierarchical structure with parent-child relationships
- Progress tracking (0-100%)
- Life area associations
- Media attachments support
- Entity associations for knowledge graph

#### Projects
- Hierarchical structure similar to goals
- Status tracking (planning, active, completed, archived)
- Goal and task associations
- Life area categorization
- Entity associations for knowledge graph

#### Tasks
- Linked to goals and projects
- Dependency management
- Priority and due date tracking
- Progress and completion status
- Entity associations for knowledge graph

#### Life Areas
- System defaults (shared across all users)
- User-specific custom areas
- Weight-based importance ranking
- Color coding for visualization

#### Entities (Knowledge Graph) - NEW
- **EntityType**: Defines types of entities (person, place, organization, etc.)
- **Entity**: Individual entities with attributes and importance scoring
- **EntityRelationship**: Connections between entities with strength metrics
- **Association Tables**: GoalEntity, ProjectEntity, TaskEntity for linking
- Automatic extraction from text using NLP
- Relationship detection and strength calculation

#### Habits
- Recurrence rules (daily, weekly, monthly)
- Streak tracking
- Completion records with notes
- Goal and life area associations

#### Journal Entries
- Mood tracking
- Media attachments
- Tag associations
- Full-text search capability

#### Tags
- User-defined categorization
- Multi-model associations
- Usage statistics

#### User Preferences
- Notification settings
- UI preferences
- AI assistant configuration
- Default associations
- Change history tracking (UserPreferencesHistory)

## Services Layer

### Goal Service
- Hierarchical operations (get children, descendants, path)
- Tree structure generation
- Cycle detection for parent changes
- Progress aggregation
- User isolation enforcement

### Project Service
- Similar hierarchy features as goals
- Timeline generation
- Progress calculation
- Status management

### Task Service
- Dependency graph management
- Circular dependency prevention
- Completion order calculation
- Subtask management

### Entity Extraction Service (NEW)
- **Pattern-based extraction**: People, places, organizations, dates, URLs, emails, phones
- **Context-aware processing**: Links entities to goals, projects, tasks
- **Relationship detection**: Identifies connections between entities
- **Importance scoring**: Calculates entity relevance based on usage
- **Batch processing**: Efficient extraction from multiple sources

### Preferences Service
- User preferences management
- Change history logging
- Default life area validation
- Preference change summaries

## API Endpoints

### Authentication
- `POST /auth/register` - User registration
- `POST /auth/login` - Email/password login
- `POST /auth/social-login` - OAuth login (Google, Apple)
- `GET /auth/me` - Current user info
- `POST /auth/forgot-password` - Password reset

### Goals
- `GET /api/goals` - List user's goals
- `POST /api/goals` - Create new goal
- `GET /api/goals/{id}` - Get specific goal
- `PUT /api/goals/{id}` - Update goal
- `DELETE /api/goals/{id}` - Delete goal
- `GET /api/goals/{id}/children` - Get child goals
- `GET /api/goals/{id}/descendants` - Get all descendants
- `GET /api/goals/{id}/path` - Get path to root
- `GET /api/goals/{id}/tree` - Get tree structure
- `PUT /api/goals/{id}/move` - Change parent

### Projects
- Similar endpoints to goals with hierarchy support
- `GET /api/projects/{id}/progress` - Calculate progress
- `GET /api/projects/{id}/timeline` - Get timeline

### Tasks
- Standard CRUD operations
- `GET /api/tasks/{id}/dependencies` - Get dependencies
- `POST /api/tasks/{id}/complete` - Mark complete
- `GET /api/tasks/completion-order` - Get optimal order

### Life Areas
- `GET /api/life-areas` - List areas (system + custom)
- `POST /api/life-areas` - Create custom area
- `PUT /api/life-areas/{id}` - Update custom area
- `DELETE /api/life-areas/{id}` - Delete custom area
- `GET /api/life-areas/stats/summary` - Get statistics

### Entities (Planned)
- `GET /api/entities` - List user's entities
- `POST /api/entities/extract` - Extract from text
- `GET /api/entities/{id}/relationships` - Get relationships
- `PUT /api/entities/{id}/importance` - Update importance

### User Preferences
- `GET /api/user-preferences` - Get preferences
- `POST /api/user-preferences` - Create preferences
- `PUT /api/user-preferences` - Update preferences
- `DELETE /api/user-preferences` - Delete preferences
- `POST /api/user-preferences/quick-setup` - Quick setup
- `GET /api/user-preferences/history` - Get change history

## Database Migrations

### Recent Migrations
- `001_initial_schema.py` - Base tables
- `016_add_default_life_areas.py` - System default life areas
- `017_add_entity_knowledge_graph.py` - Entity system and knowledge graph

### Running Migrations
```bash
# Apply all migrations
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "description"

# Check current version
alembic current

# Rollback one version
alembic downgrade -1
```

## Configuration

### Environment Variables
```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost/dbname

# Firebase
GOOGLE_APPLICATION_CREDENTIALS=/path/to/serviceAccountKey.json

# Redis
REDIS_URL=redis://localhost:6379

# Security
SECRET_KEY=your-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# API Settings
API_V1_STR=/api/v1
PROJECT_NAME=SelfOS
```

### Configuration Management
The `config.py` file provides centralized configuration with:
- Environment-based settings
- Pydantic validation
- Type safety
- Default values
- Rate limiting configuration

## Testing

### Test Structure
```
tests/
├── conftest.py           # Shared fixtures and configuration
├── unit/                 # Unit tests
│   ├── test_auth.py     # Authentication tests
│   ├── test_goals.py    # Goals CRUD tests
│   ├── test_goal_hierarchy.py    # Goal hierarchy tests
│   ├── test_projects.py          # Projects tests
│   ├── test_project_hierarchy.py # Project hierarchy tests
│   ├── test_tasks.py             # Tasks tests
│   ├── test_life_areas.py        # Life areas tests
│   ├── test_preferences_service.py # Preferences tests
│   └── ...
└── integration/         # Integration tests
```

### Running Tests
```bash
# All tests
python run_tests.py

# Specific categories
python run_tests.py --unit
python run_tests.py --integration
python run_tests.py --goals
python run_tests.py --coverage
```

### Test Status
- ✅ 85+ passing tests
- ✅ Authentication with Firebase mocking
- ✅ Hierarchical operations for goals/projects
- ✅ Cycle detection and prevention
- ✅ User data isolation
- ✅ Intent classification
- ⚠️ Some database-related failures (being fixed)

## Security

### Authentication
- Firebase ID token verification
- JWT token generation for internal use
- Row-level security via user_id filtering

### Rate Limiting
- Configurable per-minute and per-hour limits
- Burst limit support
- IP-based tracking

### Data Isolation
- All queries filtered by current user
- System data (user_id='system') read-only
- Foreign key constraints ensure data integrity

## Performance Optimizations

### Database Indexes
- User ID indexes on all tables
- Composite indexes for common queries
- Timestamp indexes for sorting
- Full-text search indexes on content fields

### Query Optimization
- Eager loading with `joinedload()`
- Pagination support
- Selective field loading
- Query result caching with Redis

### Caching Strategy
- Redis for session storage
- Query result caching
- Configuration caching
- Rate limit tracking

## AI Integration

### Intent Service
- Message classification (create goal, create task, etc.)
- Entity extraction (dates, priorities, life areas)
- Conversation state management
- Rule-based fallback for common patterns

### Entity Extraction
- Automatic extraction from user content
- Pattern matching for people, places, organizations
- Relationship detection between entities
- Importance scoring based on usage patterns

### Assistant Profiles
- Customizable AI personality
- Communication style preferences
- Conversation history tracking
- Intent feedback collection

## Error Handling

### Middleware
- Global exception handling
- Request/response logging
- Error formatting
- Rate limit enforcement

### HTTP Status Codes
- 200: Success
- 201: Created
- 204: No Content (successful deletion)
- 400: Bad Request
- 401: Unauthorized
- 403: Forbidden
- 404: Not Found
- 422: Validation Error
- 429: Too Many Requests
- 500: Internal Server Error

## Development Workflow

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Start development server
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Run tests
python run_tests.py
```

### Docker Development
```bash
# Build and start services
docker-compose up --build

# Run migrations in container
docker exec selfos-backend-1 alembic upgrade head

# View logs
docker-compose logs -f backend
```

## Future Enhancements

### Planned Features
- [ ] Real-time notifications via WebSocket
- [ ] Advanced entity relationship visualization
- [ ] Machine learning for entity importance
- [ ] Automated goal/task suggestions
- [ ] Social features and sharing
- [ ] Export/import functionality
- [ ] Advanced analytics dashboard
- [ ] Voice input support
- [ ] Mobile app API optimizations

### Technical Improvements
- [ ] GraphQL API option
- [ ] Event sourcing for audit trail
- [ ] Microservices architecture
- [ ] Kubernetes deployment
- [ ] Advanced caching strategies
- [ ] Performance monitoring
- [ ] A/B testing framework
- [ ] API versioning strategy

## API Documentation

### Interactive Documentation
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- OpenAPI Schema: `http://localhost:8000/openapi.json`

### Example Requests

#### Create Goal with Entity Extraction
```json
POST /api/goals
{
  "title": "Meet with John Smith at Google HQ next Monday",
  "description": "Discuss partnership opportunities",
  "life_area_id": 2,
  "extract_entities": true
}
```

#### Get Entity Relationships
```json
GET /api/entities/123/relationships
Response:
{
  "entity": {
    "id": 123,
    "name": "John Smith",
    "type": "person"
  },
  "relationships": [
    {
      "target": {"id": 456, "name": "Google", "type": "organization"},
      "type": "works_at",
      "strength": 0.8
    }
  ]
}
```

## Support and Maintenance

### Monitoring
- Health check endpoint: `GET /health`
- Metrics collection via middleware
- Error tracking and alerting
- Performance monitoring

### Backup and Recovery
- Automated database backups
- Point-in-time recovery
- Data export functionality
- Disaster recovery procedures

### Documentation Updates
- Keep README.md updated
- Document API changes
- Maintain migration notes
- Update test documentation

---

*Last Updated: January 2025*
*Version: 1.0.0*

# SelfOS Backend API

FastAPI-based backend service providing the core business logic, data management, and API endpoints for the SelfOS personal AI assistant platform.

## 🚀 Features

- **RESTful API**: Complete CRUD operations for goals, tasks, and user management
- **Authentication**: JWT-based auth with Firebase integration
- **AI Integration**: Seamless connection to AI providers (OpenAI, Anthropic, Local)
- **Progress Analytics**: Advanced user insights and completion predictions
- **Story Generation**: Automated narrative creation from completed tasks
- **Notification System**: Push and email notifications for task completion
- **Database Management**: PostgreSQL with automated archival and optimization
- **Testing**: 87% test coverage with 174+ passing tests
- **Documentation**: Auto-generated OpenAPI/Swagger docs

## 🏗️ Architecture

```
├── routers/          # API endpoints (thin HTTP layer)
├── services/         # Business logic layer
├── models/           # Database models (SQLAlchemy)
├── schemas/          # Pydantic validation schemas
├── tests/            # Unit and integration tests
├── migrations/       # Database migration scripts
└── scripts/          # Utility and management scripts
```

### Clean Architecture Pattern

The backend follows clean architecture principles:

- **Routers** (`routers/`): Handle HTTP requests, authentication, and response formatting
- **Services** (`services/`): Contain all business logic, validation, and workflow orchestration
- **Models** (`models/`): Define database schema and relationships
- **Schemas** (`schemas/`): Validate input/output data with Pydantic

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 12+
- Redis 6+
- Firebase Service Account credentials

### Installation

```bash
# Navigate to backend directory
cd apps/backend_api

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration
```

### Database Setup

```bash
# Initialize database (creates tables and indexes)
python manage_db.py init

# Load demo data (optional)
python demo_life_areas.py

# Run migrations (if any)
alembic upgrade head
```

### Running the Server

```bash
# Development server with auto-reload
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Or use the convenience script
python scripts/start_server.py

# Production server
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker
```

### Health Check

```bash
curl http://localhost:8000/health
# Expected: {"status": "healthy", "version": "1.0.0"}
```

### API Documentation

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI Schema: http://localhost:8000/openapi.json

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_goals.py

# Run tests in parallel
pytest -n auto
```

### Test Categories

- **Unit Tests**: Individual service and utility functions
- **Integration Tests**: End-to-end API workflows
- **Database Tests**: Model relationships and constraints
- **Auth Tests**: Authentication and authorization flows

## 📊 Core Services

### Goal Service (`services/goal_service.py`)
- Complete CRUD operations for goals
- Life area integration
- Progress tracking and status management
- Advanced filtering and querying

### Task Service (`services/task_service.py`)
- Task lifecycle management
- Goal association and dependency tracking
- Completion workflows with AI integration
- Automated progress updates and notifications

### Progress Service (`services/progress.py`)
- User analytics and insights generation
- Goal completion predictions based on velocity
- Weekly/monthly progress reports
- Personalized recommendations

### Storytelling Service (`services/storytelling.py`)
- Automated story generation from completed tasks
- Weekly summary narratives
- AI prompt suggestions for personalized content
- Media integration for rich storytelling

### Notification Service (`services/notifications.py`)
- Multi-channel notification delivery (push, email)
- User preference management
- Achievement celebration workflows
- Weekly progress summaries

## 🔧 Configuration

Key environment variables:

```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost/selfos

# Redis
REDIS_URL=redis://localhost:6379

# Firebase Authentication
GOOGLE_APPLICATION_CREDENTIALS=/path/to/serviceAccountKey.json

# AI Providers
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key

# Email Service (optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email
SMTP_PASSWORD=your_password
```

## 📊 API Endpoints

### Core Resources
- `GET/POST/PUT/DELETE /api/goals/` - Goal management
- `GET/POST/PUT/DELETE /api/tasks/` - Task management
- `PUT /api/tasks/{id}/complete` - Mark task complete (triggers workflows)

### Analytics
- `GET /api/progress/insights` - Comprehensive user analytics
- `GET /api/progress/goals/{id}/prediction` - Goal completion predictions
- `GET /api/progress/summary` - Dashboard-ready progress summary

### AI & Storytelling
- `GET /api/storytelling/weekly-summary` - Auto-generated weekly narratives
- `POST /api/storytelling/prompts` - AI prompt suggestions
- `GET /api/storytelling/recent-stories` - Story session history

### Authentication
- `POST /auth/register` - User registration
- `POST /auth/login` - User authentication
- `GET /auth/me` - Current user info

For complete API documentation, see [API_REFERENCE.md](../../docs/API_REFERENCE.md)

## 🔍 Database Management

### Archival System
Automatic archival for high-volume tables:

```bash
# Run archival process
python manage_db.py archive

# Check archive status
python manage_db.py status
```

### Performance Monitoring

```bash
# Analyze query performance
python manage_db.py analyze

# Generate performance report
python scripts/db_performance_report.py
```

## 🐛 Troubleshooting

### Common Issues

**Database connection failed**
```bash
# Check PostgreSQL is running
pg_isready -h localhost -p 5432

# Verify connection string
python -c "from db import engine; print(engine.url)"
```

**Tests failing**
```bash
# Run specific failing test with verbose output
pytest tests/test_specific.py::test_function -v -s

# Check test database setup
python -c "from conftest import test_db; print('Test DB OK')"
```

**Authentication errors**
```bash
# Verify Firebase credentials
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json
python -c "import firebase_admin; print('Firebase OK')"
```

### Performance Issues

- Check database query performance with `EXPLAIN ANALYZE`
- Monitor Redis memory usage and hit rates
- Review application logs for slow endpoints
- Use profiling tools like `py-spy` for bottleneck identification

## 🚀 Deployment

### Docker
```bash
# Build image
docker build -t selfos-backend .

# Run container
docker run -p 8000:8000 -e DATABASE_URL="..." selfos-backend
```

### Production Checklist
- [ ] Environment variables configured
- [ ] Database migrations applied
- [ ] SSL/HTTPS enabled
- [ ] Monitoring and logging configured
- [ ] Backup strategy implemented
- [ ] Rate limiting enabled
- [ ] Security headers configured

## 📈 Monitoring

### Health Endpoints
- `GET /health` - Basic health check
- `GET /health/detailed` - Detailed system status
- `GET /metrics` - Application metrics (Prometheus format)

### Key Metrics
- Response time per endpoint
- Database query performance
- AI provider response times
- User activity patterns
- Error rates and types

## 🤝 Contributing

### Development Workflow
1. Create feature branch from `main`
2. Write tests for new functionality
3. Implement feature with proper service layer separation
4. Update documentation and API schemas
5. Run full test suite and ensure 90%+ coverage
6. Submit pull request with detailed description

### Code Standards
- Follow PEP 8 style guidelines
- Use type hints for all functions
- Write docstrings for public APIs
- Keep router functions thin (business logic in services)
- Maintain test coverage above 87%

### Service Layer Guidelines
- All business logic goes in `services/`
- Services should be stateless and testable
- Use dependency injection for external resources
- Handle errors gracefully with proper logging
- Return structured results with clear error messages

---

For more detailed technical information, see the [Architecture Documentation](../../docs/ARCHITECTURE.md) and [Developer Guide](../../docs/DEVELOPER_GUIDE.md).

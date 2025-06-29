# Local Development Guide

Complete guide for setting up and testing the SelfOS backend API with AI event system locally.

## Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Docker & Docker Compose (optional)
- Git

## Quick Start (Docker - Recommended)

### 1. Clone and Setup

```bash
git clone <repository-url>
cd selfos
```

### 2. Environment Setup

Create Firebase service account key file and set environment variable:

```bash
# Set path to your Firebase service account key
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your/firebase-key.json"
```

### 3. Start All Services

```bash
# Start database, Redis, Weaviate, and backend API
docker-compose up -d

# View logs
docker-compose logs -f backend
```

### 4. Verify Installation

```bash
# Basic health check
curl http://localhost:8000/health

# Detailed system health
curl http://localhost:8000/health/detailed
```

## Manual Setup (Without Docker)

### 1. Database Setup

```bash
# Install PostgreSQL
brew install postgresql  # macOS
# sudo apt-get install postgresql  # Linux

# Start PostgreSQL
brew services start postgresql  # macOS
# sudo systemctl start postgresql  # Linux

# Create database
psql postgres
CREATE DATABASE selfos_dev;
CREATE USER selfos WITH PASSWORD 'selfos';
GRANT ALL PRIVILEGES ON DATABASE selfos_dev TO selfos;
\q
```

### 2. Redis Setup (Optional but Recommended)

```bash
# Install Redis
brew install redis  # macOS
# sudo apt-get install redis-server  # Linux

# Start Redis
brew services start redis  # macOS
# sudo systemctl start redis  # Linux
```

### 3. Weaviate Setup (Optional)

```bash
# Run Weaviate with Docker
docker run -d \
  --name weaviate \
  -p 8080:8080 \
  -e AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED=true \
  -e PERSISTENCE_DATA_PATH=/var/lib/weaviate \
  -e DEFAULT_VECTORIZER_MODULE=none \
  semitechnologies/weaviate:1.22.4
```

### 4. Python Environment

```bash
cd apps/backend_api

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

### 5. Environment Variables

```bash
# Create .env file
cat > .env << EOF
DATABASE_URL=postgresql://selfos:selfos@localhost:5432/selfos_dev
REDIS_URL=redis://localhost:6379
GOOGLE_APPLICATION_CREDENTIALS=/path/to/firebase-key.json
EVENT_SYSTEM_ENABLED=true
EVENT_TIMEOUT_SECONDS=30
LOG_LEVEL=INFO
WEAVIATE_URL=http://localhost:8080
EOF
```

### 6. Database Migration

```bash
# Run migrations
alembic upgrade head

# Or use management script
python manage_db.py migrate
```

### 7. Start Application

```bash
# Development server with auto-reload
uvicorn main:app --reload --log-level debug

# Production-like server
uvicorn main:app --host 0.0.0.0 --port 8000
```

## Testing the System

### 1. Health Checks

```bash
# Basic health
curl http://localhost:8000/health

# Detailed health with all components
curl http://localhost:8000/health/detailed | jq

# Database schema check
curl http://localhost:8000/health/database/migration-status

# Test specific services
curl http://localhost:8000/health/services/progress
curl http://localhost:8000/health/services/storytelling
curl http://localhost:8000/health/services/notifications  
curl http://localhost:8000/health/services/memory
```

### 2. Test Event System

```bash
# Test event publishing
curl -X POST http://localhost:8000/health/test-event | jq

# Check logs for event processing
docker-compose logs backend | grep "Processing.*event"
```

### 3. API Testing

#### Authentication Setup

```bash
# Register a test user
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com", 
    "password": "testpass123"
  }'

# Login to get token
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "testpass123"
  }'

# Export token for subsequent requests
export TOKEN="your-jwt-token-here"
```

#### Test Core Features

```bash
# Create a life area
curl -X POST http://localhost:8000/life-areas \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Health & Fitness",
    "description": "Physical health and fitness goals"
  }'

# Create a goal
curl -X POST http://localhost:8000/goals \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Get Fit This Year",
    "description": "Improve physical fitness and health",
    "life_area_id": 1,
    "target_date": "2024-12-31"
  }'

# Create a task
curl -X POST http://localhost:8000/tasks \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Morning Run",
    "description": "30-minute run in the park",
    "goal_id": 1,
    "duration": 30
  }'
```

#### Test Event System with Real Task

```bash
# Complete the task (this triggers AI events!)
curl -X PUT http://localhost:8000/tasks/1/complete \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json"

# Check logs immediately after
docker-compose logs backend | tail -20

# You should see event processing logs like:
# INFO - Processing task completion event: 1 for user abc123
# INFO - Service progress completed successfully
# INFO - Service storytelling completed successfully  
# INFO - Service notifications completed successfully
# INFO - Service memory completed successfully
```

### 4. Database Testing

```bash
# Check task was marked complete
curl http://localhost:8000/tasks/1 \
  -H "Authorization: Bearer $TOKEN"

# Check if story was generated
curl http://localhost:8000/story-sessions \
  -H "Authorization: Bearer $TOKEN"

# Check goal progress was updated
curl http://localhost:8000/goals/1 \
  -H "Authorization: Bearer $TOKEN"
```

### 5. Vector Memory Testing

```bash
# Test memory search (once vector DB is integrated)
curl -X GET "http://localhost:8000/memory/search?query=running" \
  -H "Authorization: Bearer $TOKEN"

# Get memory stats
curl http://localhost:8000/memory/stats \
  -H "Authorization: Bearer $TOKEN"
```

## Development Workflow

### 1. Code Changes

```bash
# Backend is running with auto-reload
# Make changes to Python files - server automatically restarts

# Check logs for errors
docker-compose logs -f backend
```

### 2. Database Changes

```bash
# Create new migration
alembic revision --autogenerate -m "Add new feature"

# Apply migration
alembic upgrade head

# Rollback if needed
alembic downgrade -1
```

### 3. Testing

```bash
# Run tests
cd apps/backend_api
pytest

# Run specific test
pytest tests/unit/test_tasks.py

# Run with coverage
pytest --cov=. --cov-report=html
```

### 4. Event System Development

```bash
# Test event publishing directly
python -c "
import asyncio
from event_bus import publish, EventType
asyncio.run(publish(EventType.TASK_COMPLETED, {'test': True}))
"

# Monitor event processing
tail -f logs/app.log | grep "event"
```

## Troubleshooting

### Common Issues

**Database Connection Error:**
```bash
# Check database is running
docker-compose ps db

# Check connection
psql postgresql://selfos:selfos@localhost:5432/selfos_dev -c "SELECT 1;"
```

**Event System Not Working:**
```bash
# Check event system initialization
curl http://localhost:8000/health/detailed | jq '.components.event_system'

# Check service logs
docker-compose logs backend | grep "Initialize"
```

**Authentication Issues:**
```bash
# Verify Firebase key is mounted
docker-compose exec backend ls -la /secrets/

# Check environment variable
docker-compose exec backend env | grep GOOGLE_APPLICATION_CREDENTIALS
```

**Services Timing Out:**
```bash
# Increase timeout in environment
EVENT_TIMEOUT_SECONDS=60

# Check individual service health
curl http://localhost:8000/health/services/progress
```

### Debug Mode

```bash
# Run with debug logging
LOG_LEVEL=DEBUG uvicorn main:app --reload

# Or with Docker
docker-compose up -d
docker-compose exec backend tail -f /var/log/app.log
```

### Reset Development Environment

```bash
# Reset database
docker-compose down -v
docker-compose up -d db
docker-compose exec backend alembic upgrade head

# Or reset everything
docker-compose down -v
docker-compose up -d
```

## Performance Testing

### Load Testing

```bash
# Install apache bench
brew install apache-bench  # macOS

# Test basic endpoint
ab -n 1000 -c 10 http://localhost:8000/health

# Test event system under load
ab -n 100 -c 5 -p test_task.json -T application/json \
  -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/health/test-event
```

### Monitoring

```bash
# Monitor Docker containers
docker stats

# Monitor PostgreSQL
docker-compose exec db psql -U selfos -d selfos_dev \
  -c "SELECT * FROM pg_stat_activity;"

# Monitor Weaviate
curl http://localhost:8080/v1/meta
```

## VS Code Setup

Create `.vscode/settings.json`:

```json
{
    "python.defaultInterpreterPath": "./apps/backend_api/venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": true,
    "python.formatting.provider": "black",
    "files.exclude": {
        "**/__pycache__": true,
        "**/*.pyc": true
    }
}
```

Create `.vscode/launch.json`:

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "FastAPI Debug",
            "type": "python",
            "request": "launch",
            "program": "${workspaceFolder}/apps/backend_api/main.py",
            "args": [],
            "env": {
                "DATABASE_URL": "postgresql://selfos:selfos@localhost:5432/selfos_dev"
            },
            "cwd": "${workspaceFolder}/apps/backend_api"
        }
    ]
}
```

## Next Steps

1. **Add Real AI Models**: Replace mock implementations with actual AI services
2. **Vector Database Integration**: Complete Weaviate integration for semantic search
3. **Real-time Features**: Add WebSocket support for live notifications
4. **Monitoring**: Set up Prometheus/Grafana for production monitoring
5. **Testing**: Add comprehensive integration tests for event system

## Support

If you encounter issues:

1. Check the logs: `docker-compose logs backend`
2. Verify health endpoints: `curl http://localhost:8000/health/detailed`
3. Test individual components with the health API
4. Check database connectivity and migrations
5. Verify Firebase authentication setup
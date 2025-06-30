# Getting Started with SelfOS

**Quick setup guide for developers and users**

## Prerequisites

- **Docker & Docker Compose** (recommended for development)
- **Python 3.11+** (for local development)
- **Node.js 18+** (for frontend development)
- **Git** for version control

## Quick Start (Docker - Recommended)

### 1. Clone and Setup
```bash
git clone https://github.com/your-org/selfos.git
cd selfos

# Copy environment files
cp apps/backend_api/.env.example apps/backend_api/.env
```

### 2. Configure Environment
Edit `apps/backend_api/.env`:
```bash
# Database
DATABASE_URL=postgresql://selfos:selfos@localhost:5432/selfos_db

# JWT
JWT_SECRET_KEY=your-super-secret-jwt-key-here
JWT_ALGORITHM=HS256

# AI Provider (choose one)
AI_PROVIDER=local  # or openai, anthropic
# OPENAI_API_KEY=your-openai-key
# ANTHROPIC_API_KEY=your-anthropic-key
```

### 3. Start Services
```bash
# Start all services
docker-compose up -d

# Check status
docker-compose ps
```

### 4. Initialize Database
```bash
# Run migrations
docker-compose exec backend_api alembic upgrade head

# Create test user (optional)
docker-compose exec backend_api python -c "
from db import get_db
from models import User
from passlib.context import CryptContext

db = next(get_db())
pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

user = User(
    email='test@example.com',
    full_name='Test User',
    hashed_password=pwd_context.hash('testpass123'),
    is_active=True
)
db.add(user)
db.commit()
print('Test user created: test@example.com / testpass123')
"
```

### 5. Test the API
```bash
# Health check
curl http://localhost:8000/health

# Login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "testpass123"}'

# Use the returned token for authenticated requests
TOKEN="your-jwt-token-here"
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/auth/me
```

## Development Setup

### Backend Development
```bash
cd apps/backend_api

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run development server
uvicorn main:app --reload --port 8000
```

### Frontend Development (Coming Soon)
```bash
cd apps/frontend

# Install Flutter dependencies
flutter pub get

# Run development server
flutter run -d web
```

### AI Engine Development
```bash
cd apps/ai_engine

# Install dependencies
pip install -r requirements.txt

# Run tests
python -m pytest tests/
```

## Configuration Options

### AI Providers

#### OpenAI Setup
```bash
# Add to .env
AI_PROVIDER=openai
OPENAI_API_KEY=sk-your-api-key-here
OPENAI_MODEL=gpt-4
```

#### Anthropic Setup  
```bash
# Add to .env
AI_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-your-api-key-here
ANTHROPIC_MODEL=claude-3-sonnet-20240229
```

#### Local/Mock Setup
```bash
# Add to .env
AI_PROVIDER=local
# No API key needed - uses mock responses
```

### Database Options

#### PostgreSQL (Recommended)
```bash
DATABASE_URL=postgresql://user:pass@localhost:5432/selfos_db
```

#### SQLite (Development)
```bash
DATABASE_URL=sqlite:///./selfos.db
```

### Memory/Vector Database

#### Pinecone
```bash
VECTOR_DB_TYPE=pinecone
PINECONE_API_KEY=your-pinecone-key
PINECONE_ENVIRONMENT=us-west1-gcp
```

#### Local Vector Store
```bash
VECTOR_DB_TYPE=local
# No additional configuration needed
```

## Testing

### Run All Tests
```bash
# Backend tests
cd apps/backend_api
python -m pytest tests/ -v

# AI engine tests  
cd apps/ai_engine
python -m pytest tests/ -v

# Integration tests
cd apps/backend_api
python scripts/test_runner.py chat
```

### Run Specific Test Categories
```bash
# Unit tests only
pytest tests/unit/ -v

# Integration tests only
pytest tests/integration/ -v

# Test with coverage
pytest --cov=. tests/
```

## Common Commands

### Database Management
```bash
# Create migration
alembic revision --autogenerate -m "Add new field"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1

# Reset database
alembic downgrade base && alembic upgrade head
```

### Docker Management
```bash
# View logs
docker-compose logs -f backend_api

# Restart service
docker-compose restart backend_api

# Rebuild containers
docker-compose build --no-cache

# Clean up
docker-compose down -v
```

### Development Workflow
```bash
# Start development environment
docker-compose up -d postgres redis

# Run backend locally
cd apps/backend_api
uvicorn main:app --reload

# Run tests
pytest tests/ -v

# Format code
black . && isort .

# Lint code
flake8 .
```

## Troubleshooting

### Common Issues

#### Database Connection Error
```bash
# Check if PostgreSQL is running
docker-compose ps postgres

# Reset database connection
docker-compose restart postgres
```

#### AI Provider Errors
```bash
# Check configuration
python -c "
import os
print('AI_PROVIDER:', os.getenv('AI_PROVIDER'))
print('OPENAI_API_KEY:', 'SET' if os.getenv('OPENAI_API_KEY') else 'NOT SET')
"

# Test AI health
curl http://localhost:8000/api/ai/health
```

#### Port Already in Use
```bash
# Find process using port 8000
lsof -i :8000

# Kill process
kill -9 <PID>

# Or use different port
uvicorn main:app --port 8001
```

### Getting Help

1. **Check the logs**: `docker-compose logs -f service_name`
2. **View API documentation**: Visit `http://localhost:8000/docs`
3. **Review test failures**: `pytest tests/ -v -s`
4. **Consult documentation**: See [API Reference](API_REFERENCE.md)

## Next Steps

1. **Explore the API**: Visit `http://localhost:8000/docs` for interactive documentation
2. **Read the Architecture**: See [ARCHITECTURE.md](ARCHITECTURE.md) for system design
3. **Review Examples**: Check `examples/` directory for code samples
4. **Join Development**: See [DEVELOPMENT.md](DEVELOPMENT.md) for contribution guidelines

## Production Deployment

For production deployment instructions, see [DEPLOYMENT.md](DEPLOYMENT.md).

---

**Need help?** Check our [Troubleshooting Guide](TROUBLESHOOTING.md) or open an issue on GitHub.
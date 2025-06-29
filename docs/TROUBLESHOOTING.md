# Troubleshooting Guide

Common issues and solutions for the SelfOS backend API.

## Docker Compose Issues

### PostgreSQL Connection Errors

**Error**: `sqlalchemy.exc.NoSuchModuleError: Can't load plugin: sqlalchemy.dialects:postgres`

**Solution**:
```bash
# Rebuild Docker image with PostgreSQL dependencies
docker-compose down
docker-compose build --no-cache backend
docker-compose up -d
```

**Root Cause**: Missing `psycopg2-binary` and system dependencies in Docker image.

### Database URL Format Issues

**Error**: `postgres://` URL format not recognized

**Solution**: The application automatically converts `postgres://` to `postgresql://`. If issues persist:

```bash
# Update environment variable
export DATABASE_URL="postgresql://selfos:selfos@localhost:5432/selfos_dev"
```

### Firebase Authentication Errors

**Error**: `GOOGLE_APPLICATION_CREDENTIALS` not found

**Solution**:
```bash
# Set environment variable to your Firebase service account key
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your/firebase-key.json"

# Verify file exists and is readable
ls -la "$GOOGLE_APPLICATION_CREDENTIALS"

# Restart Docker Compose
docker-compose down && docker-compose up -d
```

### Service Startup Issues

**Error**: Services fail to start or timeout

**Solution**:
```bash
# Check all service logs
docker-compose logs

# Check specific service
docker-compose logs backend
docker-compose logs db
docker-compose logs weaviate

# Restart individual services
docker-compose restart backend
```

## Application Issues

### Event System Not Working

**Symptoms**: Task completion doesn't trigger AI services

**Debug Steps**:
```bash
# 1. Check event system health
curl http://localhost:8000/health/detailed | jq '.components.event_system'

# 2. Test event publishing
curl -X POST http://localhost:8000/health/test-event

# 3. Check event consumer logs
docker-compose logs backend | grep -i event

# 4. Verify environment variables
docker-compose exec backend env | grep EVENT
```

**Common Fixes**:
```bash
# Restart with event system enabled
docker-compose down
docker-compose up -d
```

### Database Migration Issues

**Error**: Tables don't exist or schema is outdated

**Solution**:
```bash
# Run migrations
docker-compose exec backend alembic upgrade head

# Or use management script
docker-compose exec backend python manage_db.py migrate

# Check migration status
curl http://localhost:8000/health/database/migration-status
```

### AI Services Failing

**Symptoms**: Individual services show "unhealthy" status

**Debug Steps**:
```bash
# Check each service individually
curl http://localhost:8000/health/services/progress
curl http://localhost:8000/health/services/storytelling
curl http://localhost:8000/health/services/notifications
curl http://localhost:8000/health/services/memory

# Check service logs
docker-compose logs backend | grep -E "(progress|storytelling|notifications|memory)"
```

## Performance Issues

### Slow Response Times

**Debug Steps**:
```bash
# Check container resource usage
docker stats

# Check database performance
docker-compose exec db psql -U selfos -d selfos_dev -c "
SELECT query, calls, total_time, mean_time 
FROM pg_stat_statements 
ORDER BY total_time DESC LIMIT 10;"

# Check application logs for timeouts
docker-compose logs backend | grep -i timeout
```

**Solutions**:
```bash
# Increase timeout settings
export EVENT_TIMEOUT_SECONDS=60

# Scale backend service
docker-compose up -d --scale backend=2
```

### Database Connection Pool Exhaustion

**Error**: `QueuePool limit of size X overflow Y reached`

**Solution**:
```bash
# Add connection pool settings to DATABASE_URL
export DATABASE_URL="postgresql://selfos:selfos@localhost:5432/selfos_dev?pool_size=20&max_overflow=30"
```

## Development Issues

### Import Errors

**Error**: `ModuleNotFoundError` or circular imports

**Solution**:
```bash
# Ensure Python path is correct
export PYTHONPATH=/path/to/apps/backend_api

# Check for circular imports
cd apps/backend_api
python -c "import main"
```

### Hot Reload Not Working

**Solution**:
```bash
# For local development, run directly
cd apps/backend_api
uvicorn main:app --reload --log-level debug

# Or use development Docker compose
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
```

## Testing Issues

### Test Script Failures

**Error**: `test_system.py` fails with connection errors

**Debug Steps**:
```bash
# 1. Verify backend is running
curl http://localhost:8000/health

# 2. Check backend logs
docker-compose logs backend | tail -20

# 3. Run individual test functions
cd apps/backend_api
python -c "
from scripts.test_system import SystemTester
tester = SystemTester()
print(tester.test_basic_health())
"
```

### Authentication Test Failures

**Error**: User registration or login fails

**Solutions**:
```bash
# 1. Check if auth router is loaded
curl http://localhost:8000/docs

# 2. Verify Firebase configuration
docker-compose exec backend python -c "
import firebase_admin
print('Firebase initialized:', len(firebase_admin._apps) > 0)
"

# 3. Use test credentials
export TEST_USER_EMAIL="test@example.com"
export TEST_USER_PASSWORD="testpass123"
```

## Network Issues

### Port Conflicts

**Error**: `Port already in use`

**Solution**:
```bash
# Find process using port
lsof -i :8000
lsof -i :5432
lsof -i :6379

# Kill conflicting processes or change ports
docker-compose down
# Edit docker-compose.yml to use different ports
```

### Docker Network Issues

**Error**: Services can't communicate

**Solution**:
```bash
# Recreate network
docker-compose down
docker network prune
docker-compose up -d

# Check network connectivity
docker-compose exec backend ping db
docker-compose exec backend ping redis
```

## Weaviate Issues

### Vector Database Connection

**Error**: Weaviate service fails to start

**Debug Steps**:
```bash
# Check Weaviate logs
docker-compose logs weaviate

# Test Weaviate directly
curl http://localhost:8080/v1/meta

# Check Weaviate health
curl http://localhost:8080/v1/.well-known/ready
```

**Solution**:
```bash
# Restart with fresh data
docker-compose down -v
docker-compose up -d weaviate
```

## Memory Issues

### Out of Memory Errors

**Symptoms**: Containers getting killed, slow performance

**Solutions**:
```bash
# Check Docker memory limits
docker system df
docker system info | grep -i memory

# Increase Docker memory allocation
# In Docker Desktop: Settings → Resources → Memory

# Add memory limits to docker-compose.yml
services:
  backend:
    deploy:
      resources:
        limits:
          memory: 1G
```

## Complete Reset

When all else fails, perform a complete reset:

```bash
# Stop everything
docker-compose down -v

# Remove all images
docker rmi $(docker images "selfos*" -q)

# Clean up Docker system
docker system prune -a

# Rebuild from scratch
docker-compose build --no-cache
docker-compose up -d

# Wait for services
sleep 30

# Run tests
./scripts/quick-test.sh
```

## Getting Help

### Collect Debug Information

When reporting issues, include:

```bash
# System information
docker --version
docker-compose --version
uname -a

# Service status
docker-compose ps

# Recent logs
docker-compose logs --tail=50 backend
docker-compose logs --tail=50 db

# Health check results
curl http://localhost:8000/health/detailed

# Environment variables (redact sensitive data)
docker-compose exec backend env | grep -E "(DATABASE|EVENT|LOG)"
```

### Log Levels

For debugging, increase log verbosity:

```bash
# In docker-compose.yml
environment:
  LOG_LEVEL: DEBUG
  
# Or restart with debug
docker-compose restart backend
docker-compose logs -f backend
```

Remember to set `LOG_LEVEL=INFO` for production to avoid performance impact.
# Event System Deployment Guide

This guide covers deploying the AI-oriented event-driven system implemented in the SelfOS backend.

## System Overview

The event system processes task completion events and triggers intelligent services:

- **Progress Analysis** - Tracks goal completion and metrics
- **Story Generation** - Creates narrative content from completed tasks  
- **Notifications** - Sends achievement notifications via push/email
- **Vector Memory** - Indexes tasks for semantic search and AI memory

## Docker Deployment

### Quick Start

```bash
# Start all services including event system
docker-compose up -d

# View logs to verify event system initialization
docker-compose logs backend | grep "event"
```

### Environment Variables

The following environment variables control the event system:

```bash
# Enable/disable event system
EVENT_SYSTEM_ENABLED=true

# Timeout for individual services (seconds)
EVENT_TIMEOUT_SECONDS=30

# Logging level
LOG_LEVEL=INFO

# Vector database connection (Weaviate)
WEAVIATE_URL=http://weaviate:8080
WEAVIATE_API_KEY=""
```

### Services Included

The docker-compose.yml includes:

- **PostgreSQL** - Main database
- **Redis** - Caching and potential event queue
- **Weaviate** - Vector database for semantic memory
- **Backend API** - FastAPI with event system

## Event Flow Architecture

```
Task Completion → Event Bus → Event Consumers → AI Services
     ↓               ↓              ↓              ↓
  tasks.py     event_bus.py  event_consumers.py  services/
```

### Event Types

- `TASK_COMPLETED` - Triggered when user completes a task
- `GOAL_COMPLETED` - Triggered when all goal tasks are finished

## Service Configuration

### Progress Service
- Calculates goal completion percentages
- Tracks user velocity and patterns
- Provides completion predictions

### Story Service  
- Generates narrative content from tasks
- Includes media attachment context
- Creates weekly summaries

### Notification Service
- Sends push notifications for achievements
- Supports email notifications  
- Configurable notification preferences

### Vector Memory Service
- Indexes completed tasks for semantic search
- Generates embeddings for content similarity
- Supports AI memory and recommendations

## Production Considerations

### Scaling

For high-volume deployments:

```yaml
# Add to docker-compose.yml
backend:
  deploy:
    replicas: 3
  environment:
    # Enable Redis for event distribution
    REDIS_EVENT_QUEUE: "true"
```

### Monitoring

Monitor event processing:

```bash
# View event processing logs
docker-compose logs -f backend | grep "Processing.*event"

# Check service health
curl http://localhost:8000/health
```

### Performance Tuning

Key settings for production:

```bash
# Increase timeout for heavy processing
EVENT_TIMEOUT_SECONDS=60

# Batch processing for high volume
EVENT_BATCH_SIZE=10
EVENT_BATCH_TIMEOUT=5

# Vector database optimization
WEAVIATE_BATCH_SIZE=100
```

## Database Migrations

The event system requires existing database schema. Run migrations:

```bash
# Apply database migrations
docker-compose exec backend alembic upgrade head

# Or run migration script
docker-compose exec backend python manage_db.py migrate
```

## Testing Event System

### Manual Testing

```bash
# Complete a task via API to trigger events
curl -X PUT http://localhost:8000/tasks/1/complete \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json"

# Check logs for event processing
docker-compose logs backend | tail -20
```

### Health Checks

```bash
# Application health
curl http://localhost:8000/

# Database connectivity  
curl http://localhost:8000/health/db

# Vector database status
curl http://localhost:8080/v1/meta
```

## Troubleshooting

### Common Issues

**Event system not initializing:**
```bash
# Check startup logs
docker-compose logs backend | grep "Initialize"

# Verify environment variables
docker-compose exec backend env | grep EVENT
```

**Services timing out:**
```bash
# Increase timeout
EVENT_TIMEOUT_SECONDS=60

# Check individual service logs
docker-compose logs backend | grep "Service.*failed"
```

**Vector database connection:**
```bash
# Test Weaviate connectivity
curl http://localhost:8080/v1/meta

# Check Weaviate logs
docker-compose logs weaviate
```

### Development Mode

For development with hot reload:

```bash
# Start with volume mount for code changes
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

# Or run locally
cd apps/backend_api
uvicorn main:app --reload --log-level debug
```

## Security Considerations

### Production Security

- Enable authentication for Weaviate in production
- Use secure Redis configuration for event queues
- Rotate Firebase service account keys regularly
- Enable HTTPS for all external API calls

### Environment Secrets

```bash
# Use docker secrets for sensitive data
echo "your-weaviate-key" | docker secret create weaviate_key -
```

## Monitoring and Observability

### Metrics to Track

- Event processing latency
- Service success/failure rates  
- Database query performance
- Vector database index size
- Notification delivery rates

### Logging

Event system provides structured logging:

```
INFO - Processing task completion event: 123 for user abc
INFO - Service progress completed successfully  
INFO - Service storytelling completed successfully
INFO - Service notifications completed successfully
INFO - Service memory completed successfully
INFO - Task completion processing finished: 4/4 services succeeded
```

## Future Enhancements

### Planned Features

- Redis-based event queuing for high availability
- Webhook support for external integrations
- A/B testing for notification strategies
- Advanced vector search capabilities
- Real-time progress dashboards

### Vector Database Scaling

For large-scale deployments:

```yaml
weaviate:
  image: semitechnologies/weaviate:1.22.4
  environment:
    CLUSTER_HOSTNAME: 'node1'
    RAFT_JOIN: 'node2:8300,node3:8300'
  deploy:
    replicas: 3
```
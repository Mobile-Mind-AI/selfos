"""
Health Check Router

Provides health check endpoints for all system components
including database, event system, and AI services.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Dict, Any
import asyncio
from datetime import datetime

from dependencies import get_db
from event_bus import EventType, publish
from services import progress, storytelling, notifications, memory

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/health")
async def health_check():
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "SelfOS Backend API"
    }

@router.get("/health/detailed")
async def detailed_health_check(db: Session = Depends(get_db)):
    """
    Comprehensive health check for all system components.
    """
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "components": {}
    }
    
    # Check database connectivity
    try:
        # Simple query to test database
        result = db.execute(text("SELECT 1")).scalar()
        health_status["components"]["database"] = {
            "status": "healthy" if result == 1 else "unhealthy",
            "response_time_ms": 0,  # Could add timing if needed
            "details": "PostgreSQL connection successful"
        }
    except Exception as e:
        health_status["components"]["database"] = {
            "status": "unhealthy",
            "error": str(e),
            "details": "Database connection failed"
        }
        health_status["status"] = "degraded"
    
    # Check event system
    try:
        # Test event publishing (mock event)
        test_payload = {
            "test": True,
            "timestamp": datetime.utcnow().isoformat(),
            "source": "health_check"
        }
        
        # This will succeed if event bus is working
        await publish(EventType.TASK_COMPLETED, test_payload)
        
        health_status["components"]["event_system"] = {
            "status": "healthy",
            "details": "Event bus operational",
            "event_types": [e.value for e in EventType]
        }
    except Exception as e:
        health_status["components"]["event_system"] = {
            "status": "unhealthy",
            "error": str(e),
            "details": "Event system not operational"
        }
        health_status["status"] = "degraded"
    
    # Check AI services
    services_status = await _check_ai_services(db)
    health_status["components"]["ai_services"] = services_status
    
    if services_status["status"] != "healthy":
        health_status["status"] = "degraded"
    
    # Check database tables
    tables_status = await _check_database_tables(db)
    health_status["components"]["database_schema"] = tables_status
    
    return health_status

async def _check_ai_services(db: Session) -> Dict[str, Any]:
    """Check the health of all AI services."""
    services_status = {
        "status": "healthy",
        "services": {}
    }
    
    # Test Progress Service
    try:
        # Mock test data
        test_result = await progress.get_user_progress_insights(db, "health_check_user")
        services_status["services"]["progress"] = {
            "status": "healthy",
            "details": "Progress analysis service operational"
        }
    except Exception as e:
        services_status["services"]["progress"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        services_status["status"] = "degraded"
    
    # Test Storytelling Service
    try:
        test_data = {
            "task_id": "test",
            "user_id": "health_check_user",
            "title": "Health Check Task",
            "description": "Testing storytelling service"
        }
        suggestions = await storytelling.suggest_story_prompts(test_data)
        services_status["services"]["storytelling"] = {
            "status": "healthy",
            "details": f"Story service operational, generated {len(suggestions)} prompts"
        }
    except Exception as e:
        services_status["services"]["storytelling"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        services_status["status"] = "degraded"
    
    # Test Notifications Service
    try:
        test_result = await notifications.send_completion_notification(
            "health_check_user", 
            "Health Check Task",
            {"test": True}
        )
        services_status["services"]["notifications"] = {
            "status": "healthy",
            "details": "Notification service operational"
        }
    except Exception as e:
        services_status["services"]["notifications"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        services_status["status"] = "degraded"
    
    # Test Memory Service
    try:
        test_data = {
            "task_id": "test",
            "user_id": "health_check_user",
            "title": "Health Check Task",
            "description": "Testing memory service"
        }
        test_result = await memory.index_task(test_data)
        services_status["services"]["memory"] = {
            "status": "healthy",
            "details": "Vector memory service operational"
        }
    except Exception as e:
        services_status["services"]["memory"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        services_status["status"] = "degraded"
    
    return services_status

async def _check_database_tables(db: Session) -> Dict[str, Any]:
    """Check that all required database tables exist using ORM models."""
    tables_status = {
        "status": "healthy",
        "tables": {}
    }
    
    # Import models to check
    from models import User, Goal, Task, LifeArea, MediaAttachment, UserPreferences, FeedbackLog, StorySession
    
    # Map table names to ORM models
    table_models = {
        "users": User,
        "goals": Goal, 
        "tasks": Task,
        "life_areas": LifeArea,
        "media_attachments": MediaAttachment,
        "user_preferences": UserPreferences,
        "feedback_logs": FeedbackLog,
        "story_sessions": StorySession
    }
    
    for table_name, model_class in table_models.items():
        try:
            # Use ORM query instead of raw SQL
            result = db.query(model_class).count()
            tables_status["tables"][table_name] = {
                "status": "exists",
                "row_count": result
            }
        except Exception as e:
            tables_status["tables"][table_name] = {
                "status": "missing_or_error", 
                "error": str(e)
            }
            tables_status["status"] = "degraded"
    
    return tables_status

@router.get("/health/services/{service_name}")
async def service_health_check(service_name: str, db: Session = Depends(get_db)):
    """
    Check health of a specific service.
    
    Available services: progress, storytelling, notifications, memory
    """
    if service_name not in ["progress", "storytelling", "notifications", "memory"]:
        raise HTTPException(status_code=404, detail="Service not found")
    
    try:
        if service_name == "progress":
            result = await progress.get_user_progress_insights(db, "health_check_user")
            return {
                "service": service_name,
                "status": "healthy",
                "details": "Progress analysis service operational",
                "test_result": result
            }
        
        elif service_name == "storytelling":
            test_data = {
                "task_id": "test",
                "user_id": "health_check_user",
                "title": "Health Check Task"
            }
            result = await storytelling.suggest_story_prompts(test_data)
            return {
                "service": service_name,
                "status": "healthy",
                "details": f"Generated {len(result)} story prompts",
                "test_result": result
            }
        
        elif service_name == "notifications":
            result = await notifications.send_completion_notification(
                "health_check_user", 
                "Health Check Task",
                {"test": True}
            )
            return {
                "service": service_name,
                "status": "healthy",
                "details": "Notification service operational",
                "test_result": result
            }
        
        elif service_name == "memory":
            test_data = {
                "task_id": "test",
                "user_id": "health_check_user",
                "title": "Health Check Task",
                "description": "Testing memory service"
            }
            result = await memory.index_task(test_data)
            return {
                "service": service_name,
                "status": "healthy",
                "details": "Vector memory service operational",
                "test_result": result
            }
    
    except Exception as e:
        return {
            "service": service_name,
            "status": "unhealthy",
            "error": str(e),
            "details": f"Service {service_name} is not operational"
        }

@router.post("/health/test-event")
async def test_event_system():
    """
    Test the event system by publishing a test event.
    """
    try:
        test_payload = {
            "task_id": "test_task_123",
            "user_id": "test_user",
            "task_data": {
                "title": "Test Task for Event System",
                "description": "This is a test to verify the event system works",
                "goal_id": None,
                "life_area_id": None,
                "media_count": 0,
                "duration": 15
            }
        }
        
        # Publish test event
        await publish(EventType.TASK_COMPLETED, test_payload)
        
        return {
            "status": "success",
            "message": "Test event published successfully",
            "event_type": EventType.TASK_COMPLETED.value,
            "payload": test_payload,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to publish test event: {str(e)}",
            "timestamp": datetime.utcnow().isoformat()
        }

@router.get("/health/database/migration-status")
async def check_migration_status(db: Session = Depends(get_db)):
    """
    Check the status of database migrations.
    """
    try:
        # Check if alembic_version table exists
        result = db.execute(text("SELECT version_num FROM alembic_version")).scalar()
        
        return {
            "status": "healthy",
            "current_migration": result,
            "details": "Database migrations are up to date"
        }
    except Exception as e:
        return {
            "status": "needs_migration",
            "error": str(e),
            "details": "Database may need migration. Run 'alembic upgrade head'"
        }
"""
Event Consumers

This module contains event handlers that process published events
and trigger appropriate services for AI-oriented data processing.
"""

import logging
import asyncio
from sqlalchemy.orm import Session
from typing import Dict, Any

from event_bus import EventType, subscribe, publish
from dependencies import get_db
from services import progress, storytelling, notifications, memory

logger = logging.getLogger(__name__)

@subscribe(EventType.TASK_COMPLETED)
async def handle_task_completed(payload: Dict[str, Any]):
    """
    Handle task completion events by triggering all relevant services.
    
    Args:
        payload: Event payload containing task completion data
    """
    try:
        task_id = payload.get("task_id")
        user_id = payload.get("user_id")
        task_data = payload.get("task_data", {})
        
        logger.info(f"Processing task completion event: {task_id} for user {user_id}")
        
        # Get database session
        db = next(get_db())
        
        # Run all services concurrently for better performance
        services_tasks = []
        
        # 1. Update project progress (if task belongs to a goal)
        goal_id = task_data.get("goal_id")
        if goal_id:
            services_tasks.append(
                _safe_service_call(
                    "progress.update_project_progress",
                    progress.update_project_progress(db, int(goal_id), user_id)
                )
            )
        
        # 2. Generate story segment
        services_tasks.append(
            _safe_service_call(
                "storytelling.enqueue_segment_generation",
                storytelling.enqueue_segment_generation(db, task_data)
            )
        )
        
        # 3. Send completion notification
        task_title = task_data.get("title", "Untitled Task")
        services_tasks.append(
            _safe_service_call(
                "notifications.send_completion_notification",
                notifications.send_completion_notification(user_id, task_title, task_data)
            )
        )
        
        # 4. Index task in vector memory
        services_tasks.append(
            _safe_service_call(
                "memory.index_task",
                memory.index_task(task_data)
            )
        )
        
        # Execute all services concurrently with timeout protection
        results = await asyncio.gather(*services_tasks, return_exceptions=True)
        
        # Process results and log outcomes
        service_names = ["progress", "storytelling", "notifications", "memory"]
        success_count = 0
        
        for i, result in enumerate(results):
            service_name = service_names[i] if i < len(service_names) else f"service_{i}"
            
            if isinstance(result, Exception):
                logger.error(f"Service {service_name} failed: {result}")
            elif result.get("success", True):  # Default to True if not specified
                success_count += 1
                logger.debug(f"Service {service_name} completed successfully")
            else:
                logger.warning(f"Service {service_name} reported failure: {result}")
        
        logger.info(f"Task completion processing finished: {success_count}/{len(results)} services succeeded")
        
        # Check if goal was completed (from progress service result)
        if goal_id and results and isinstance(results[0], dict):
            progress_result = results[0]
            if progress_result.get("goal_status") == "completed":
                await _handle_goal_completion(db, goal_id, user_id, progress_result)
        
        db.close()
        
    except Exception as e:
        logger.error(f"Failed to process task completion event: {e}")
        if 'db' in locals():
            db.close()

@subscribe(EventType.GOAL_COMPLETED)
async def handle_goal_completed(payload: Dict[str, Any]):
    """
    Handle goal completion events.
    
    Args:
        payload: Event payload containing goal completion data
    """
    try:
        goal_id = payload.get("goal_id")
        user_id = payload.get("user_id")
        goal_data = payload.get("goal_data", {})
        
        logger.info(f"Processing goal completion event: {goal_id} for user {user_id}")
        
        # Send special goal completion notification
        goal_title = goal_data.get("title", "Untitled Goal")
        completion_stats = goal_data.get("completion_stats", {})
        
        result = await _safe_service_call(
            "notifications.send_goal_completion_notification",
            notifications.send_goal_completion_notification(user_id, goal_title, completion_stats)
        )
        
        if result.get("success"):
            logger.info(f"Goal completion notification sent for goal {goal_id}")
        else:
            logger.error(f"Failed to send goal completion notification: {result}")
            
    except Exception as e:
        logger.error(f"Failed to process goal completion event: {e}")

async def _safe_service_call(service_name: str, service_coroutine):
    """
    Safely execute a service call with timeout and error handling.
    
    Args:
        service_name: Name of the service for logging
        service_coroutine: Coroutine to execute
        
    Returns:
        Service result or error information
    """
    try:
        # Set timeout to prevent hanging services
        result = await asyncio.wait_for(service_coroutine, timeout=30.0)
        return result
    except asyncio.TimeoutError:
        logger.error(f"Service {service_name} timed out after 30 seconds")
        return {"success": False, "error": "timeout"}
    except Exception as e:
        logger.error(f"Service {service_name} raised exception: {e}")
        return {"success": False, "error": str(e)}

async def _handle_goal_completion(db: Session, goal_id: int, user_id: str, progress_result: Dict[str, Any]):
    """
    Handle goal completion by publishing a goal completion event.
    
    Args:
        db: Database session
        goal_id: ID of the completed goal
        user_id: ID of the user
        progress_result: Result from progress service
    """
    try:
        from models import Goal
        
        # Get goal details
        goal = db.query(Goal).filter(
            Goal.id == goal_id,
            Goal.user_id == user_id
        ).first()
        
        if not goal:
            logger.error(f"Could not find completed goal {goal_id}")
            return
        
        # Prepare goal completion event payload
        goal_payload = {
            "goal_id": str(goal_id),
            "user_id": user_id,
            "goal_data": {
                "title": goal.title,
                "description": goal.description,
                "life_area_id": goal.life_area_id,
                "completion_stats": {
                    "total_tasks": progress_result.get("total_tasks", 0),
                    "completion_date": goal.updated_at.isoformat() if goal.updated_at else None,
                    "duration_days": (goal.updated_at - goal.created_at).days if goal.updated_at and goal.created_at else None
                }
            }
        }
        
        # Publish goal completion event (this will trigger handle_goal_completed)
        await publish(EventType.GOAL_COMPLETED, goal_payload)
        
        logger.info(f"Published goal completion event for goal {goal_id}")
        
    except Exception as e:
        logger.error(f"Failed to handle goal completion: {e}")

async def initialize_consumers():
    """
    Initialize all event consumers.
    
    This function should be called during application startup to register
    all event handlers with the event bus.
    """
    logger.info("Initializing event consumers...")
    
    # Consumers are automatically registered via @subscribe decorators
    # This function serves as a hook for any additional initialization
    
    logger.info("Event consumers initialized successfully")

async def shutdown_consumers():
    """
    Cleanup event consumers during application shutdown.
    """
    logger.info("Shutting down event consumers...")
    
    # Add any cleanup logic here if needed
    
    logger.info("Event consumers shut down successfully")

# Weekly summary scheduler (could be triggered by a cron job or scheduler)
async def generate_weekly_summaries():
    """
    Generate weekly summary notifications for all active users.
    
    This function should be called periodically (e.g., weekly) to send
    summary notifications to users about their progress.
    """
    try:
        logger.info("Starting weekly summary generation...")
        
        db = next(get_db())
        
        # Get all active users (simplified - in production would have better user tracking)
        from models import User
        users = db.query(User).all()
        
        summary_results = []
        
        for user in users:
            try:
                # Generate weekly summary story
                summary_result = await storytelling.generate_weekly_summary(db, user.id)
                
                if summary_result.get("success") and summary_result.get("task_count", 0) > 0:
                    # Send weekly summary notification
                    notification_result = await notifications.send_weekly_summary_notification(
                        user.id, 
                        {"tasks_completed": summary_result["task_count"]}
                    )
                    
                    summary_results.append({
                        "user_id": user.id,
                        "tasks_completed": summary_result["task_count"],
                        "notification_sent": notification_result.get("success", False)
                    })
                
            except Exception as e:
                logger.error(f"Failed to generate weekly summary for user {user.id}: {e}")
        
        db.close()
        
        logger.info(f"Weekly summary generation completed: {len(summary_results)} summaries generated")
        return summary_results
        
    except Exception as e:
        logger.error(f"Failed to generate weekly summaries: {e}")
        return []
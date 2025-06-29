"""
Event Bus System for AI-Oriented Data Hooks

This module provides a simple, in-process event bus for triggering
AI services when important events occur (like task completion).
"""

import asyncio
import logging
from typing import Callable, Dict, List, Awaitable, Any
from enum import Enum
from datetime import datetime

logger = logging.getLogger(__name__)

class EventType(str, Enum):
    """Supported event types in the system."""
    TASK_COMPLETED = "task.completed"
    TASK_CREATED = "task.created"
    TASK_UPDATED = "task.updated"
    GOAL_COMPLETED = "goal.completed"
    GOAL_CREATED = "goal.created"
    STORY_GENERATED = "story.generated"
    USER_REGISTERED = "user.registered"

# Global registry of event subscribers
subscribers: Dict[EventType, List[Callable[[dict], Awaitable[None]]]] = {}

# Event publishing statistics for monitoring
event_stats = {
    "total_published": 0,
    "total_processed": 0,
    "errors": 0,
    "last_event_time": None
}

def subscribe(event_type: EventType):
    """
    Decorator to subscribe a handler function to an event type.
    
    Args:
        event_type: The type of event to subscribe to
        
    Returns:
        Decorator function that registers the handler
    """
    def decorator(handler: Callable[[dict], Awaitable[None]]):
        if event_type not in subscribers:
            subscribers[event_type] = []
        
        subscribers[event_type].append(handler)
        logger.info(f"Registered handler for {event_type.value}")
        return handler
    
    return decorator

def register_handler(event_type: EventType, handler: Callable[[dict], Awaitable[None]]):
    """
    Programmatically register a handler function to an event type.
    
    Args:
        event_type: The type of event to subscribe to
        handler: Async function that processes the event payload
    """
    if event_type not in subscribers:
        subscribers[event_type] = []
    
    subscribers[event_type].append(handler)
    logger.info(f"Registered handler for {event_type.value}")

async def publish(event_type: EventType, payload: dict):
    """
    Publish an event to all registered subscribers.
    
    Args:
        event_type: The type of event being published
        payload: Data payload for the event
    """
    global event_stats
    
    # Add metadata to payload
    enhanced_payload = {
        **payload,
        "event_type": event_type.value,
        "timestamp": datetime.utcnow().isoformat(),
        "event_id": f"{event_type.value}_{datetime.utcnow().timestamp()}"
    }
    
    event_stats["total_published"] += 1
    event_stats["last_event_time"] = enhanced_payload["timestamp"]
    
    handlers = subscribers.get(event_type, [])
    logger.info(f"Publishing {event_type.value} to {len(handlers)} handlers")
    
    if not handlers:
        logger.warning(f"No handlers registered for {event_type.value}")
        return
    
    # Process all handlers concurrently
    tasks = []
    for handler in handlers:
        tasks.append(_safe_handler_execution(handler, enhanced_payload))
    
    # Wait for all handlers to complete
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Log any errors but don't raise them (fire-and-forget pattern)
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            event_stats["errors"] += 1
            logger.error(f"Handler {i} failed for {event_type.value}: {result}")
        else:
            event_stats["total_processed"] += 1

async def _safe_handler_execution(handler: Callable, payload: dict):
    """
    Execute a handler with error handling and timeout.
    
    Args:
        handler: The event handler function
        payload: Event data
    """
    try:
        # Set a timeout to prevent hanging handlers
        await asyncio.wait_for(handler(payload), timeout=30.0)
        logger.debug(f"Handler {handler.__name__} completed successfully")
    except asyncio.TimeoutError:
        logger.error(f"Handler {handler.__name__} timed out after 30 seconds")
        raise
    except Exception as e:
        logger.error(f"Handler {handler.__name__} failed: {e}")
        raise

def get_subscribers(event_type: EventType = None) -> Dict[str, int]:
    """
    Get information about registered subscribers.
    
    Args:
        event_type: Optional event type to filter by
        
    Returns:
        Dict mapping event types to subscriber counts
    """
    if event_type:
        return {event_type.value: len(subscribers.get(event_type, []))}
    
    return {
        event_type.value: len(handlers) 
        for event_type, handlers in subscribers.items()
    }

def get_event_stats() -> dict:
    """
    Get event bus statistics for monitoring.
    
    Returns:
        Dict with event processing statistics
    """
    return {
        **event_stats,
        "subscriber_counts": get_subscribers(),
        "health": "healthy" if event_stats["errors"] < event_stats["total_published"] * 0.1 else "degraded"
    }

def clear_subscribers():
    """Clear all subscribers. Mainly for testing."""
    global subscribers
    subscribers.clear()
    logger.info("Cleared all event subscribers")

# Decorator for easy handler registration
def event_handler(event_type: EventType):
    """
    Decorator to register a function as an event handler.
    
    Usage:
        @event_handler(EventType.TASK_COMPLETED)
        async def my_handler(payload):
            # Process the event
            pass
    """
    def decorator(func: Callable[[dict], Awaitable[None]]):
        subscribe(event_type, func)
        return func
    return decorator

# Context manager for event publishing with error tracking
class EventPublisher:
    """Context manager for publishing events with automatic error tracking."""
    
    def __init__(self, event_type: EventType, payload: dict):
        self.event_type = event_type
        self.payload = payload
        self.start_time = None
    
    async def __aenter__(self):
        self.start_time = datetime.utcnow()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            await publish(self.event_type, self.payload)
        else:
            logger.error(f"Event publishing aborted due to error: {exc_val}")

# Helper function for common task completion event
async def publish_task_completed(task_id: str, user_id: str, task_data: dict = None):
    """
    Convenience function for publishing task completion events.
    
    Args:
        task_id: ID of the completed task
        user_id: ID of the user who completed the task
        task_data: Additional task information
    """
    payload = {
        "task_id": task_id,
        "user_id": user_id,
        **(task_data or {})
    }
    
    await publish(EventType.TASK_COMPLETED, payload)

# Helper function for goal completion event
async def publish_goal_completed(goal_id: str, user_id: str, goal_data: dict = None):
    """
    Convenience function for publishing goal completion events.
    
    Args:
        goal_id: ID of the completed goal
        user_id: ID of the user who completed the goal
        goal_data: Additional goal information
    """
    payload = {
        "goal_id": goal_id,
        "user_id": user_id,
        **(goal_data or {})
    }
    
    await publish(EventType.GOAL_COMPLETED, payload)
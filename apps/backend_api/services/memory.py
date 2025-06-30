"""
Memory service for backward compatibility with health checks.

This service provides a simple interface that wraps the enhanced memory service
for compatibility with existing health check code.
"""

import logging
from typing import Dict, Any
from .enhanced_memory import create_memory_service

logger = logging.getLogger(__name__)

# Global memory service instance
_memory_service = None


def get_memory_service():
    """Get or create the memory service instance."""
    global _memory_service
    if _memory_service is None:
        try:
            _memory_service = create_memory_service(vector_store_type="memory")
            logger.info("Memory service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize memory service: {e}")
            _memory_service = None
    return _memory_service


async def index_task(task_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Index a task for testing purposes.
    
    This is a simple wrapper for health checks that stores task data
    in the enhanced memory service.
    """
    try:
        memory_service = get_memory_service()
        if not memory_service:
            return {"status": "error", "message": "Memory service not available"}
        
        # Store the task as a memory entry
        await memory_service.store_memory(
            user_id=task_data.get("user_id", "unknown"),
            content=f"Task: {task_data.get('title', 'Untitled')}\nDescription: {task_data.get('description', '')}",
            content_type="task",
            metadata={
                "task_id": task_data.get("task_id"),
                "title": task_data.get("title"),
                "description": task_data.get("description"),
                "indexed_for": "health_check"
            }
        )
        
        return {
            "status": "success",
            "message": "Task indexed successfully",
            "task_id": task_data.get("task_id"),
            "indexed_at": "memory_service"
        }
        
    except Exception as e:
        logger.error(f"Failed to index task: {e}")
        return {
            "status": "error",
            "message": f"Failed to index task: {str(e)}"
        }


async def search_tasks(query: str, user_id: str = None) -> Dict[str, Any]:
    """
    Search tasks in memory.
    
    Simple wrapper for searching task-related memories.
    """
    try:
        memory_service = get_memory_service()
        if not memory_service:
            return {"status": "error", "message": "Memory service not available", "results": []}
        
        # Search for task memories
        results = await memory_service.search_memories(
            user_id=user_id or "unknown",
            query=query,
            content_types=["task"],
            limit=10
        )
        
        return {
            "status": "success",
            "query": query,
            "results": [
                {
                    "content": result.entry.content,
                    "similarity_score": result.similarity_score,
                    "metadata": result.entry.metadata
                }
                for result in results
            ]
        }
        
    except Exception as e:
        logger.error(f"Failed to search tasks: {e}")
        return {
            "status": "error",
            "message": f"Failed to search tasks: {str(e)}",
            "results": []
        }


async def get_health_status() -> Dict[str, Any]:
    """Get memory service health status."""
    try:
        memory_service = get_memory_service()
        if not memory_service:
            return {
                "status": "error",
                "message": "Memory service not available",
                "service_type": "none"
            }
        
        # Get memory service stats
        stats = await memory_service.get_memory_stats("health_check_user")
        
        return {
            "status": "healthy",
            "message": "Memory service operational",
            "service_type": memory_service.__class__.__name__,
            "stats": stats
        }
        
    except Exception as e:
        logger.error(f"Memory service health check failed: {e}")
        return {
            "status": "error",
            "message": f"Health check failed: {str(e)}",
            "service_type": "unknown"
        }
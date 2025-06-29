"""
Progress Analysis Service

This service analyzes task and goal completion to provide
intelligent progress tracking and insights.
"""

import logging
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

async def update_project_progress(db: Session, goal_id: int, user_id: str) -> Dict[str, Any]:
    """
    Update progress metrics when a task is completed.
    
    Args:
        db: Database session
        goal_id: ID of the goal containing the completed task
        user_id: ID of the user
        
    Returns:
        Dict with updated progress information
    """
    try:
        from models import Goal, Task
        
        # Get the goal and its tasks
        goal = db.query(Goal).filter(
            Goal.id == goal_id,
            Goal.user_id == user_id
        ).first()
        
        if not goal:
            logger.warning(f"Goal {goal_id} not found for user {user_id}")
            return {"error": "Goal not found"}
        
        # Get all tasks for this goal
        tasks = db.query(Task).filter(
            Task.goal_id == goal_id,
            Task.user_id == user_id
        ).all()
        
        if not tasks:
            logger.info(f"No tasks found for goal {goal_id}")
            return {"goal_progress": 0, "tasks_completed": 0, "total_tasks": 0}
        
        # Calculate progress
        total_tasks = len(tasks)
        completed_tasks = len([t for t in tasks if t.status == "completed"])
        progress_percentage = (completed_tasks / total_tasks) * 100 if total_tasks > 0 else 0
        
        # Update goal progress
        old_progress = goal.progress
        goal.progress = progress_percentage
        goal.updated_at = datetime.utcnow()
        
        # Check if goal is now complete
        if progress_percentage == 100 and old_progress < 100:
            goal.status = "completed"
            logger.info(f"Goal {goal_id} marked as completed!")
            
            # TODO: Trigger goal completion event
            # await publish_goal_completed(str(goal_id), user_id, {...})
        
        db.commit()
        
        # Calculate velocity and insights
        recent_completions = db.query(Task).filter(
            Task.user_id == user_id,
            Task.status == "completed",
            Task.updated_at >= datetime.utcnow() - timedelta(days=7)
        ).count()
        
        result = {
            "goal_id": goal_id,
            "goal_progress": progress_percentage,
            "tasks_completed": completed_tasks,
            "total_tasks": total_tasks,
            "goal_status": goal.status,
            "recent_velocity": recent_completions,
            "progress_delta": progress_percentage - old_progress
        }
        
        logger.info(f"Updated progress for goal {goal_id}: {progress_percentage}%")
        return result
        
    except Exception as e:
        logger.error(f"Failed to update project progress: {e}")
        return {"error": str(e)}

async def get_user_progress_insights(db: Session, user_id: str) -> Dict[str, Any]:
    """
    Generate progress insights for a user across all their goals.
    
    Args:
        db: Database session
        user_id: ID of the user
        
    Returns:
        Dict with progress insights and recommendations
    """
    try:
        from models import Goal, Task
        
        # Get user's goals and tasks
        goals = db.query(Goal).filter(Goal.user_id == user_id).all()
        total_tasks = db.query(Task).filter(Task.user_id == user_id).count()
        completed_tasks = db.query(Task).filter(
            Task.user_id == user_id,
            Task.status == "completed"
        ).count()
        
        # Calculate completion rates by time period
        now = datetime.utcnow()
        
        # Tasks completed in last 7 days
        weekly_completed = db.query(Task).filter(
            Task.user_id == user_id,
            Task.status == "completed",
            Task.updated_at >= now - timedelta(days=7)
        ).count()
        
        # Tasks completed in last 30 days
        monthly_completed = db.query(Task).filter(
            Task.user_id == user_id,
            Task.status == "completed",
            Task.updated_at >= now - timedelta(days=30)
        ).count()
        
        # Calculate goal completion rate
        completed_goals = len([g for g in goals if g.status == "completed"])
        goal_completion_rate = (completed_goals / len(goals)) * 100 if goals else 0
        
        # Identify most productive life area
        most_productive_area = None
        if goals:
            from collections import Counter
            area_completions = Counter()
            
            for goal in goals:
                if goal.life_area_id and goal.status == "completed":
                    area_completions[goal.life_area_id] += 1
            
            if area_completions:
                most_productive_area_id = area_completions.most_common(1)[0][0]
                from models import LifeArea
                area = db.query(LifeArea).filter(LifeArea.id == most_productive_area_id).first()
                most_productive_area = area.name if area else None
        
        # Generate recommendations
        recommendations = []
        
        if weekly_completed == 0:
            recommendations.append("Consider breaking down your current tasks into smaller, achievable steps")
        elif weekly_completed < 3:
            recommendations.append("Try to complete at least one task per day to maintain momentum")
        
        if goal_completion_rate < 50:
            recommendations.append("Focus on completing existing goals before starting new ones")
        
        return {
            "total_goals": len(goals),
            "completed_goals": completed_goals,
            "goal_completion_rate": goal_completion_rate,
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "task_completion_rate": (completed_tasks / total_tasks) * 100 if total_tasks > 0 else 0,
            "weekly_velocity": weekly_completed,
            "monthly_velocity": monthly_completed,
            "most_productive_area": most_productive_area,
            "recommendations": recommendations,
            "last_updated": now.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to generate progress insights: {e}")
        return {"error": str(e)}

async def predict_completion_date(db: Session, goal_id: int, user_id: str) -> Optional[str]:
    """
    Predict when a goal might be completed based on current velocity.
    
    Args:
        db: Database session
        goal_id: ID of the goal
        user_id: ID of the user
        
    Returns:
        Predicted completion date as ISO string, or None if cannot predict
    """
    try:
        from models import Goal, Task
        
        goal = db.query(Goal).filter(
            Goal.id == goal_id,
            Goal.user_id == user_id
        ).first()
        
        if not goal or goal.status == "completed":
            return None
        
        # Get remaining tasks
        remaining_tasks = db.query(Task).filter(
            Task.goal_id == goal_id,
            Task.user_id == user_id,
            Task.status != "completed"
        ).count()
        
        if remaining_tasks == 0:
            return datetime.utcnow().isoformat()  # Should be completed now
        
        # Calculate recent completion velocity (tasks per day)
        recent_completions = db.query(Task).filter(
            Task.user_id == user_id,
            Task.status == "completed",
            Task.updated_at >= datetime.utcnow() - timedelta(days=14)
        ).count()
        
        velocity_per_day = recent_completions / 14 if recent_completions > 0 else 0.1  # Fallback
        
        # Predict completion date
        days_to_completion = remaining_tasks / velocity_per_day
        predicted_date = datetime.utcnow() + timedelta(days=days_to_completion)
        
        logger.info(f"Predicted completion for goal {goal_id}: {predicted_date.date()}")
        return predicted_date.isoformat()
        
    except Exception as e:
        logger.error(f"Failed to predict completion date: {e}")
        return None
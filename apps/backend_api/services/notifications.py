"""
Notification Service

This service handles sending notifications for task completions
and other important events in the SelfOS platform.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import json

logger = logging.getLogger(__name__)

async def send_completion_notification(user_id: str, task_title: str, task_data: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Send a notification when a task is completed.
    
    Args:
        user_id: ID of the user who completed the task
        task_title: Title of the completed task
        task_data: Additional task information
        
    Returns:
        Dict with notification sending results
    """
    try:
        # Get user preferences for notifications
        notification_prefs = await _get_user_notification_preferences(user_id)
        
        if not notification_prefs.get("enabled", True):
            logger.info(f"Notifications disabled for user {user_id}")
            return {"skipped": True, "reason": "notifications_disabled"}
        
        # Generate notification content
        notification = await _generate_completion_notification(task_title, task_data)
        
        # Send notifications based on user preferences
        results = []
        
        if notification_prefs.get("push_enabled", True):
            push_result = await _send_push_notification(user_id, notification)
            results.append({"type": "push", **push_result})
        
        if notification_prefs.get("email_enabled", False):
            email_result = await _send_email_notification(user_id, notification)
            results.append({"type": "email", **email_result})
        
        # Log notification for user's achievement history
        await _log_achievement_notification(user_id, task_title, notification)
        
        logger.info(f"Sent completion notifications for task '{task_title}' to user {user_id}")
        
        return {
            "success": True,
            "notifications_sent": len(results),
            "results": results,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to send completion notification: {e}")
        return {"success": False, "error": str(e)}

async def _get_user_notification_preferences(user_id: str) -> Dict[str, Any]:
    """
    Get user's notification preferences.
    
    In a full implementation, this would query the user_preferences table.
    For now, returns default preferences.
    """
    # TODO: Query actual user preferences from database
    default_prefs = {
        "enabled": True,
        "push_enabled": True,
        "email_enabled": False,
        "tone": "friendly",
        "celebration_level": "moderate"
    }
    
    return default_prefs

async def _generate_completion_notification(task_title: str, task_data: Dict[str, Any] = None) -> Dict[str, str]:
    """
    Generate notification content for task completion.
    
    Args:
        task_title: Title of the completed task
        task_data: Additional task context
        
    Returns:
        Dict with notification title and body
    """
    task_data = task_data or {}
    
    # Celebration emojis based on task characteristics
    celebration_emojis = ["🎉", "✅", "🌟", "🚀", "💪", "🎯"]
    emoji = celebration_emojis[len(task_title) % len(celebration_emojis)]
    
    # Generate titles
    titles = [
        f"{emoji} Task Completed!",
        f"{emoji} Achievement Unlocked!",
        f"{emoji} Great Progress!",
        f"{emoji} Well Done!"
    ]
    
    title = titles[len(task_title) % len(titles)]
    
    # Generate body text
    bodies = [
        f"You successfully completed '{task_title}'! Keep up the momentum!",
        f"'{task_title}' is now finished. Another step toward your goals!",
        f"Congratulations on completing '{task_title}'. Your consistency pays off!",
        f"Task completed: '{task_title}'. You're making excellent progress!"
    ]
    
    body = bodies[len(task_title) % len(bodies)]
    
    # Add context if available
    if task_data.get("goal_id"):
        body += " This brings you closer to completing your goal."
    
    if task_data.get("media_count", 0) > 0:
        body += f" Your progress has been documented with {task_data['media_count']} attachments."
    
    return {
        "title": title,
        "body": body,
        "emoji": emoji
    }

async def _send_push_notification(user_id: str, notification: Dict[str, str]) -> Dict[str, Any]:
    """
    Send a push notification to the user's device.
    
    In a full implementation, this would integrate with services like
    Firebase Cloud Messaging, Apple Push Notification Service, etc.
    """
    try:
        # Simulate push notification sending
        logger.info(f"[PUSH] To {user_id}: {notification['title']} - {notification['body']}")
        
        # In production, this would:
        # 1. Get user's device tokens from database
        # 2. Send to push notification service
        # 3. Handle delivery confirmations and failures
        
        return {
            "success": True,
            "delivery_method": "push",
            "message_id": f"push_{datetime.utcnow().timestamp()}",
            "delivered_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to send push notification: {e}")
        return {"success": False, "error": str(e)}

async def _send_email_notification(user_id: str, notification: Dict[str, str]) -> Dict[str, Any]:
    """
    Send an email notification to the user.
    
    In a full implementation, this would integrate with email services
    like SendGrid, AWS SES, etc.
    """
    try:
        # Simulate email sending
        logger.info(f"[EMAIL] To {user_id}: {notification['title']} - {notification['body']}")
        
        # In production, this would:
        # 1. Get user's email from database
        # 2. Generate HTML email template
        # 3. Send via email service
        # 4. Handle bounces and unsubscribes
        
        return {
            "success": True,
            "delivery_method": "email",
            "message_id": f"email_{datetime.utcnow().timestamp()}",
            "delivered_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to send email notification: {e}")
        return {"success": False, "error": str(e)}

async def _log_achievement_notification(user_id: str, task_title: str, notification: Dict[str, str]):
    """
    Log the achievement notification for user's history.
    
    This could be stored in a notifications table or used for analytics.
    """
    log_entry = {
        "user_id": user_id,
        "type": "task_completion",
        "task_title": task_title,
        "notification": notification,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # In production, this would be stored in a database
    logger.info(f"Achievement logged: {json.dumps(log_entry)}")

async def send_goal_completion_notification(user_id: str, goal_title: str, completion_stats: Dict[str, Any]) -> Dict[str, Any]:
    """
    Send a notification when a goal is completed.
    
    Args:
        user_id: ID of the user who completed the goal
        goal_title: Title of the completed goal
        completion_stats: Statistics about the goal completion
        
    Returns:
        Dict with notification sending results
    """
    try:
        notification_prefs = await _get_user_notification_preferences(user_id)
        
        if not notification_prefs.get("enabled", True):
            return {"skipped": True, "reason": "notifications_disabled"}
        
        # Generate special goal completion notification
        notification = {
            "title": "🎯 Goal Achieved!",
            "body": f"Congratulations! You've completed your goal: '{goal_title}'. "
                   f"This involved {completion_stats.get('total_tasks', 0)} tasks and represents a significant milestone!",
            "emoji": "🎯"
        }
        
        # Send notifications
        results = []
        
        if notification_prefs.get("push_enabled", True):
            push_result = await _send_push_notification(user_id, notification)
            results.append({"type": "push", **push_result})
        
        if notification_prefs.get("email_enabled", False):
            email_result = await _send_email_notification(user_id, notification)
            results.append({"type": "email", **email_result})
        
        logger.info(f"Sent goal completion notifications for '{goal_title}' to user {user_id}")
        
        return {
            "success": True,
            "notifications_sent": len(results),
            "results": results,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to send goal completion notification: {e}")
        return {"success": False, "error": str(e)}

async def send_weekly_summary_notification(user_id: str, summary_stats: Dict[str, Any]) -> Dict[str, Any]:
    """
    Send a weekly progress summary notification.
    
    Args:
        user_id: ID of the user
        summary_stats: Weekly progress statistics
        
    Returns:
        Dict with notification sending results
    """
    try:
        completed_tasks = summary_stats.get("tasks_completed", 0)
        
        if completed_tasks == 0:
            # Skip notification if no progress
            return {"skipped": True, "reason": "no_progress"}
        
        notification = {
            "title": "📊 Weekly Progress",
            "body": f"This week you completed {completed_tasks} tasks! "
                   f"Your consistency is building momentum toward your goals.",
            "emoji": "📊"
        }
        
        notification_prefs = await _get_user_notification_preferences(user_id)
        
        results = []
        if notification_prefs.get("push_enabled", True):
            push_result = await _send_push_notification(user_id, notification)
            results.append({"type": "push", **push_result})
        
        return {
            "success": True,
            "notifications_sent": len(results),
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Failed to send weekly summary notification: {e}")
        return {"success": False, "error": str(e)}
"""
Story Composition Service

This service generates narrative content from completed tasks,
incorporating media attachments and personal context.
"""

import logging
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from datetime import datetime
import json

logger = logging.getLogger(__name__)

async def enqueue_segment_generation(db: Session, task_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate a story segment when a task is completed.
    
    Args:
        db: Database session
        task_data: Task information from the completion event
        
    Returns:
        Dict with story generation results
    """
    try:
        from models import StorySession, Task, MediaAttachment
        
        task_id = task_data.get("task_id")
        user_id = task_data.get("user_id")
        
        # Get the completed task with media
        task = db.query(Task).filter(
            Task.id == int(task_id),
            Task.user_id == user_id
        ).first()
        
        if not task:
            logger.warning(f"Task {task_id} not found for story generation")
            return {"error": "Task not found"}
        
        # Get associated media
        media_attachments = db.query(MediaAttachment).filter(
            MediaAttachment.task_id == task.id
        ).all()
        
        # Generate story content
        story_content = await _generate_task_story(task, media_attachments)
        
        # Create or update story session
        story_session = StorySession(
            user_id=user_id,
            title=f"Completed: {task.title}",
            generated_text=story_content["text"],
            summary_period="task-based",
            content_type="achievement",
            source_tasks=[task.id],
            source_goals=[task.goal_id] if task.goal_id else [],
            source_life_areas=[task.life_area_id] if task.life_area_id else [],
            word_count=len(story_content["text"].split()),
            estimated_read_time=len(story_content["text"].split()) * 4,  # ~250 WPM
            processing_status="completed",
            generated_at=datetime.utcnow(),
            generation_params={
                "source": "task_completion",
                "task_id": task_id,
                "media_included": len(media_attachments) > 0,
                "auto_generated": True
            }
        )
        
        db.add(story_session)
        db.commit()
        db.refresh(story_session)
        
        logger.info(f"Generated story segment for task {task_id}: {story_session.id}")
        
        return {
            "story_session_id": story_session.id,
            "story_text": story_content["text"],
            "media_count": len(media_attachments),
            "word_count": story_session.word_count,
            "success": True
        }
        
    except Exception as e:
        logger.error(f"Failed to generate story segment: {e}")
        return {"error": str(e), "success": False}

async def _generate_task_story(task, media_attachments: List) -> Dict[str, str]:
    """
    Generate narrative content for a completed task.
    
    This is a simplified version - in production, this would integrate
    with an AI language model for more sophisticated story generation.
    """
    
    # Base story elements
    title = task.title
    description = task.description or ""
    
    # Add context about timing
    duration_text = ""
    if task.duration:
        hours = task.duration // 60
        minutes = task.duration % 60
        if hours > 0:
            duration_text = f" This took {hours} hours and {minutes} minutes to complete."
        else:
            duration_text = f" This took {minutes} minutes to complete."
    
    # Add media context
    media_text = ""
    if media_attachments:
        media_count = len(media_attachments)
        media_types = list(set([m.file_type for m in media_attachments]))
        
        if media_count == 1:
            media_text = f" Along the way, a {media_types[0]} was captured to document the progress."
        else:
            media_text = f" This achievement was documented with {media_count} attachments including {', '.join(media_types)}."
    
    # Generate story variants based on task characteristics
    story_templates = [
        f"Today marks a significant milestone: {title} has been successfully completed! {description} {duration_text}{media_text} This accomplishment represents another step forward in the journey of personal growth and productivity.",
        
        f"Another achievement unlocked! The task '{title}' is now complete. {description} {duration_text}{media_text} Each completed task builds momentum toward larger goals.",
        
        f"Success! '{title}' has been finished with satisfaction. {description} {duration_text}{media_text} This demonstrates continued progress and dedication to personal objectives."
    ]
    
    # Simple selection based on task characteristics
    story_index = len(title) % len(story_templates)
    story_text = story_templates[story_index]
    
    return {
        "text": story_text.strip(),
        "template_used": story_index,
        "elements_included": {
            "title": bool(title),
            "description": bool(description),
            "duration": bool(duration_text),
            "media": bool(media_text)
        }
    }

async def generate_weekly_summary(db: Session, user_id: str) -> Dict[str, Any]:
    """
    Generate a weekly summary story from completed tasks.
    
    Args:
        db: Database session
        user_id: ID of the user
        
    Returns:
        Dict with weekly summary story
    """
    try:
        from models import Task
        from datetime import datetime, timedelta
        
        # Get tasks completed in the last 7 days
        week_ago = datetime.utcnow() - timedelta(days=7)
        completed_tasks = db.query(Task).filter(
            Task.user_id == user_id,
            Task.status == "completed",
            Task.updated_at >= week_ago
        ).all()
        
        if not completed_tasks:
            return {
                "story_text": "This week was a time of reflection and planning. Sometimes the most important progress happens in the quiet moments of preparation.",
                "task_count": 0,
                "success": True
            }
        
        # Group by life area or goal
        from collections import defaultdict
        areas = defaultdict(list)
        
        for task in completed_tasks:
            area_key = f"area_{task.life_area_id}" if task.life_area_id else f"goal_{task.goal_id}"
            areas[area_key].append(task)
        
        # Generate summary
        story_parts = [
            f"This week brought {len(completed_tasks)} accomplishments across different areas of focus."
        ]
        
        for area_key, tasks in areas.items():
            task_titles = [t.title for t in tasks]
            if len(tasks) == 1:
                story_parts.append(f"In one area, '{task_titles[0]}' was completed successfully.")
            else:
                story_parts.append(f"Significant progress was made with tasks including '{task_titles[0]}' and {len(tasks)-1} other achievements.")
        
        story_parts.append("Each completion builds toward larger objectives and represents meaningful progress in the journey of personal development.")
        
        story_text = " ".join(story_parts)
        
        return {
            "story_text": story_text,
            "task_count": len(completed_tasks),
            "areas_involved": len(areas),
            "success": True
        }
        
    except Exception as e:
        logger.error(f"Failed to generate weekly summary: {e}")
        return {"error": str(e), "success": False}

async def suggest_story_prompts(task_data: Dict[str, Any]) -> List[str]:
    """
    Generate AI prompt suggestions for story generation based on task context.
    
    Args:
        task_data: Task information
        
    Returns:
        List of suggested prompts for AI story generation
    """
    title = task_data.get("title", "")
    description = task_data.get("description", "")
    life_area = task_data.get("life_area_id")
    has_media = task_data.get("media_count", 0) > 0
    
    prompts = []
    
    # Basic achievement prompt
    prompts.append(f"Write an inspiring story about completing '{title}'. Focus on the sense of accomplishment and progress.")
    
    # Context-specific prompts
    if description:
        prompts.append(f"Create a narrative about the journey of completing '{title}'. Include details about: {description}")
    
    if has_media:
        prompts.append(f"Tell the story of '{title}' completion, incorporating visual elements and media that documented the process.")
    
    if life_area:
        prompts.append(f"Write about how completing '{title}' contributes to overall growth in this life area.")
    
    # Motivational variants
    prompts.append(f"Describe the personal growth achieved through completing '{title}', emphasizing lessons learned and future potential.")
    
    return prompts
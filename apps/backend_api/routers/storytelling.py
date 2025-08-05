from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from dependencies import get_db, get_current_user
from services.storytelling import generate_weekly_summary, suggest_story_prompts

router = APIRouter()


@router.get("/storytelling/weekly-summary")
async def get_weekly_summary(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Generate a weekly summary story from completed tasks.
    
    Returns:
        A narrative summary of the user's weekly accomplishments
    """
    summary = await generate_weekly_summary(db, current_user["uid"])
    
    if not summary.get("success", True):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate weekly summary: {summary.get('error', 'Unknown error')}"
        )
    
    return {
        "story_text": summary["story_text"],
        "task_count": summary["task_count"],
        "areas_involved": summary.get("areas_involved", 0),
        "week_period": "Last 7 days",
        "generated_at": summary.get("generated_at")
    }


@router.post("/storytelling/prompts")
async def get_story_prompts(
    task_data: dict,
    current_user: dict = Depends(get_current_user)
):
    """
    Generate AI prompt suggestions for story generation based on task context.
    
    Args:
        task_data: Task information including title, description, life_area_id, etc.
        
    Returns:
        List of suggested prompts for AI story generation
    """
    try:
        prompts = await suggest_story_prompts(task_data)
        
        return {
            "task_title": task_data.get("title", ""),
            "prompts": prompts,
            "prompt_count": len(prompts),
            "usage_note": "These prompts can be used with AI language models to generate personalized achievement stories"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate story prompts: {str(e)}"
        )


@router.get("/storytelling/recent-stories")
def get_recent_stories(
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get recent story sessions for the user.
    
    Args:
        limit: Maximum number of stories to return (default: 10)
        
    Returns:
        List of recent story sessions
    """
    try:
        from models import StorySession
        
        stories = db.query(StorySession).filter(
            StorySession.user_id == current_user["uid"]
        ).order_by(
            StorySession.generated_at.desc()
        ).limit(limit).all()
        
        return {
            "stories": [
                {
                    "id": story.id,
                    "title": story.title,
                    "generated_text": story.generated_text[:200] + "..." if len(story.generated_text) > 200 else story.generated_text,
                    "summary_period": story.summary_period,
                    "content_type": story.content_type,
                    "word_count": story.word_count,
                    "estimated_read_time": story.estimated_read_time,
                    "generated_at": story.generated_at.isoformat() if story.generated_at else None,
                    "processing_status": story.processing_status,
                    "source_tasks_count": len(story.source_tasks) if story.source_tasks else 0,
                    "source_goals_count": len(story.source_goals) if story.source_goals else 0
                }
                for story in stories
            ],
            "total_count": len(stories),
            "limit": limit
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve stories: {str(e)}"
        )


@router.get("/storytelling/stories/{story_id}")
def get_story_details(
    story_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get full details of a specific story session.
    
    Args:
        story_id: ID of the story session to retrieve
        
    Returns:
        Complete story session details
    """
    try:
        from models import StorySession
        
        story = db.query(StorySession).filter(
            StorySession.id == story_id,
            StorySession.user_id == current_user["uid"]
        ).first()
        
        if not story:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Story not found"
            )
        
        return {
            "id": story.id,
            "title": story.title,
            "generated_text": story.generated_text,
            "summary_period": story.summary_period,
            "content_type": story.content_type,
            "source_tasks": story.source_tasks,
            "source_goals": story.source_goals,
            "source_life_areas": story.source_life_areas,
            "word_count": story.word_count,
            "estimated_read_time": story.estimated_read_time,
            "processing_status": story.processing_status,
            "generated_at": story.generated_at.isoformat() if story.generated_at else None,
            "generation_params": story.generation_params
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve story details: {str(e)}"
        )


@router.delete("/storytelling/stories/{story_id}")
def delete_story(
    story_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Delete a story session.
    
    Args:
        story_id: ID of the story session to delete
        
    Returns:
        Success confirmation
    """
    try:
        from models import StorySession
        
        story = db.query(StorySession).filter(
            StorySession.id == story_id,
            StorySession.user_id == current_user["uid"]
        ).first()
        
        if not story:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Story not found"
            )
        
        db.delete(story)
        db.commit()
        
        return {"message": "Story deleted successfully", "story_id": story_id}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete story: {str(e)}"
        )

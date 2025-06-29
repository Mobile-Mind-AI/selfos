from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import desc, func, and_
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

from dependencies import get_db, get_current_user
from models import StorySession, Goal, Task, LifeArea
from schemas import (
    StorySessionCreate, StorySessionUpdate, StorySession as StorySessionSchema, 
    StorySessionSummary, GenerationRequest, PublishRequest
)

router = APIRouter(prefix="/story-sessions", tags=["story-sessions"])

@router.get("", response_model=List[StorySessionSchema])
def get_story_sessions(
    content_type: Optional[str] = Query(None, description="Filter by content type"),
    posting_status: Optional[str] = Query(None, description="Filter by posting status"),
    processing_status: Optional[str] = Query(None, description="Filter by processing status"),
    summary_period: Optional[str] = Query(None, description="Filter by summary period"),
    limit: int = Query(50, ge=1, le=1000, description="Maximum number of records to return"),
    offset: int = Query(0, ge=0, description="Number of records to skip"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's story sessions with optional filtering"""
    user_id = current_user["uid"]
    
    query = db.query(StorySession).filter(StorySession.user_id == user_id)
    
    # Apply filters
    if content_type:
        query = query.filter(StorySession.content_type == content_type)
    if posting_status:
        query = query.filter(StorySession.posting_status == posting_status)
    if processing_status:
        query = query.filter(StorySession.processing_status == processing_status)
    if summary_period:
        query = query.filter(StorySession.summary_period == summary_period)
    
    # Order by creation date (newest first) and apply pagination
    story_sessions = query.order_by(desc(StorySession.created_at)).offset(offset).limit(limit).all()
    
    return story_sessions

@router.get("/{session_id}", response_model=StorySessionSchema)
def get_story_session(
    session_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific story session"""
    user_id = current_user["uid"]
    
    story_session = db.query(StorySession).filter(
        StorySession.id == session_id,
        StorySession.user_id == user_id
    ).first()
    
    if not story_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Story session not found"
        )
    
    # Increment view count
    story_session.view_count += 1
    db.commit()
    
    return story_session

@router.post("", response_model=StorySessionSchema, status_code=201)
def create_story_session(
    session_data: StorySessionCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new story session"""
    user_id = current_user["uid"]
    
    # Validate source references if provided
    if session_data.source_goals:
        existing_goals = db.query(Goal.id).filter(
            Goal.id.in_(session_data.source_goals),
            Goal.user_id == user_id
        ).all()
        if len(existing_goals) != len(session_data.source_goals):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Some referenced goals do not exist or don't belong to user"
            )
    
    if session_data.source_tasks:
        existing_tasks = db.query(Task.id).filter(
            Task.id.in_(session_data.source_tasks),
            Task.user_id == user_id
        ).all()
        if len(existing_tasks) != len(session_data.source_tasks):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Some referenced tasks do not exist or don't belong to user"
            )
    
    if session_data.source_life_areas:
        existing_life_areas = db.query(LifeArea.id).filter(
            LifeArea.id.in_(session_data.source_life_areas),
            LifeArea.user_id == user_id
        ).all()
        if len(existing_life_areas) != len(session_data.source_life_areas):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Some referenced life areas do not exist or don't belong to user"
            )
    
    # Create the story session
    story_session = StorySession(
        user_id=user_id,
        **session_data.model_dump(exclude_unset=True)
    )
    
    db.add(story_session)
    db.commit()
    db.refresh(story_session)
    
    return story_session

@router.put("/{session_id}", response_model=StorySessionSchema)
def update_story_session(
    session_id: str,
    session_update: StorySessionUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a story session"""
    user_id = current_user["uid"]
    
    story_session = db.query(StorySession).filter(
        StorySession.id == session_id,
        StorySession.user_id == user_id
    ).first()
    
    if not story_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Story session not found"
        )
    
    # Validate source references if provided in update
    update_data = session_update.model_dump(exclude_unset=True)
    
    if 'source_goals' in update_data and update_data['source_goals']:
        existing_goals = db.query(Goal.id).filter(
            Goal.id.in_(update_data['source_goals']),
            Goal.user_id == user_id
        ).all()
        if len(existing_goals) != len(update_data['source_goals']):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Some referenced goals do not exist or don't belong to user"
            )
    
    if 'source_tasks' in update_data and update_data['source_tasks']:
        existing_tasks = db.query(Task.id).filter(
            Task.id.in_(update_data['source_tasks']),
            Task.user_id == user_id
        ).all()
        if len(existing_tasks) != len(update_data['source_tasks']):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Some referenced tasks do not exist or don't belong to user"
            )
    
    if 'source_life_areas' in update_data and update_data['source_life_areas']:
        existing_life_areas = db.query(LifeArea.id).filter(
            LifeArea.id.in_(update_data['source_life_areas']),
            LifeArea.user_id == user_id
        ).all()
        if len(existing_life_areas) != len(update_data['source_life_areas']):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Some referenced life areas do not exist or don't belong to user"
            )
    
    # Update the story session
    for field, value in update_data.items():
        setattr(story_session, field, value)
    
    story_session.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(story_session)
    
    return story_session

@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_story_session(
    session_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a story session"""
    user_id = current_user["uid"]
    
    story_session = db.query(StorySession).filter(
        StorySession.id == session_id,
        StorySession.user_id == user_id
    ).first()
    
    if not story_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Story session not found"
        )
    
    db.delete(story_session)
    db.commit()

@router.get("/summary/stats", response_model=StorySessionSummary)
def get_story_sessions_summary(
    days: int = Query(30, ge=1, le=365, description="Number of days to include in summary"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get story sessions summary statistics"""
    user_id = current_user["uid"]
    
    # Calculate date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # Base query for the time period
    base_query = db.query(StorySession).filter(
        StorySession.user_id == user_id,
        StorySession.created_at >= start_date
    )
    
    # Get total count
    total_sessions = base_query.count()
    
    # Get breakdown by content type
    content_type_counts = db.query(
        StorySession.content_type,
        func.count(StorySession.id).label('count')
    ).filter(
        StorySession.user_id == user_id,
        StorySession.created_at >= start_date
    ).group_by(StorySession.content_type).all()
    
    by_content_type = {content_type: count for content_type, count in content_type_counts}
    
    # Get breakdown by posting status
    posting_status_counts = db.query(
        StorySession.posting_status,
        func.count(StorySession.id).label('count')
    ).filter(
        StorySession.user_id == user_id,
        StorySession.created_at >= start_date
    ).group_by(StorySession.posting_status).all()
    
    by_posting_status = {posting_status: count for posting_status, count in posting_status_counts}
    
    # Get breakdown by processing status
    processing_status_counts = db.query(
        StorySession.processing_status,
        func.count(StorySession.id).label('count')
    ).filter(
        StorySession.user_id == user_id,
        StorySession.created_at >= start_date
    ).group_by(StorySession.processing_status).all()
    
    by_processing_status = {processing_status: count for processing_status, count in processing_status_counts}
    
    # Calculate total word count
    total_word_count_result = db.query(func.sum(StorySession.word_count)).filter(
        StorySession.user_id == user_id,
        StorySession.created_at >= start_date,
        StorySession.word_count.isnot(None)
    ).scalar()
    
    total_word_count = int(total_word_count_result) if total_word_count_result else 0
    
    # Calculate average rating
    avg_rating_result = db.query(func.avg(StorySession.user_rating)).filter(
        StorySession.user_id == user_id,
        StorySession.created_at >= start_date,
        StorySession.user_rating.isnot(None)
    ).scalar()
    
    average_rating = float(avg_rating_result) if avg_rating_result else None
    
    # Get recent sessions (last 5 entries)
    recent_sessions = base_query.order_by(desc(StorySession.created_at)).limit(5).all()
    
    # Convert SQLAlchemy objects to dict for Pydantic
    recent_sessions_dicts = []
    for session in recent_sessions:
        session_dict = {
            "id": session.id,
            "user_id": session.user_id,
            "title": session.title,
            "generated_text": session.generated_text,
            "video_url": session.video_url,
            "audio_url": session.audio_url,
            "thumbnail_url": session.thumbnail_url,
            "summary_period": session.summary_period,
            "period_start": session.period_start,
            "period_end": session.period_end,
            "content_type": session.content_type,
            "posted_to": session.posted_to,
            "posting_status": session.posting_status,
            "scheduled_post_time": session.scheduled_post_time,
            "generation_prompt": session.generation_prompt,
            "model_version": session.model_version,
            "generation_params": session.generation_params,
            "word_count": session.word_count,
            "estimated_read_time": session.estimated_read_time,
            "source_goals": session.source_goals,
            "source_tasks": session.source_tasks,
            "source_life_areas": session.source_life_areas,
            "view_count": session.view_count,
            "like_count": session.like_count,
            "share_count": session.share_count,
            "engagement_data": session.engagement_data,
            "user_rating": session.user_rating,
            "user_notes": session.user_notes,
            "regeneration_count": session.regeneration_count,
            "processing_status": session.processing_status,
            "error_message": session.error_message,
            "created_at": session.created_at,
            "updated_at": session.updated_at,
            "generated_at": session.generated_at,
            "posted_at": session.posted_at
        }
        recent_sessions_dicts.append(session_dict)
    
    return StorySessionSummary(
        total_sessions=total_sessions,
        by_content_type=by_content_type,
        by_posting_status=by_posting_status,
        by_processing_status=by_processing_status,
        total_word_count=total_word_count,
        average_rating=average_rating,
        recent_sessions=recent_sessions_dicts
    )

@router.post("/generate", response_model=StorySessionSchema)
def generate_story(
    generation_request: GenerationRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate a new story session based on user data"""
    user_id = current_user["uid"]
    
    # Create a new story session in pending state
    story_session = StorySession(
        user_id=user_id,
        title=generation_request.title,
        summary_period=generation_request.summary_period,
        period_start=generation_request.period_start,
        period_end=generation_request.period_end,
        content_type=generation_request.content_type,
        generation_prompt=generation_request.generation_prompt,
        generation_params=generation_request.generation_params,
        processing_status="pending"
    )
    
    # Gather source data based on request parameters
    source_goals = []
    source_tasks = []
    source_life_areas = generation_request.include_life_areas or []
    
    if generation_request.include_goals:
        # Get goals within the specified period
        goals_query = db.query(Goal).filter(Goal.user_id == user_id)
        if generation_request.period_start and generation_request.period_end:
            goals_query = goals_query.filter(
                and_(
                    Goal.created_at >= generation_request.period_start,
                    Goal.created_at <= generation_request.period_end
                )
            )
        if generation_request.include_life_areas:
            goals_query = goals_query.filter(Goal.life_area_id.in_(generation_request.include_life_areas))
        
        goals = goals_query.all()
        source_goals = [goal.id for goal in goals]
    
    if generation_request.include_tasks:
        # Get tasks within the specified period
        tasks_query = db.query(Task).filter(Task.user_id == user_id)
        if generation_request.period_start and generation_request.period_end:
            tasks_query = tasks_query.filter(
                and_(
                    Task.created_at >= generation_request.period_start,
                    Task.created_at <= generation_request.period_end
                )
            )
        if generation_request.include_life_areas:
            tasks_query = tasks_query.filter(Task.life_area_id.in_(generation_request.include_life_areas))
        
        tasks = tasks_query.all()
        source_tasks = [task.id for task in tasks]
    
    story_session.source_goals = source_goals
    story_session.source_tasks = source_tasks
    story_session.source_life_areas = source_life_areas
    
    db.add(story_session)
    db.commit()
    db.refresh(story_session)
    
    # Add background task for actual generation (this would integrate with AI service)
    background_tasks.add_task(process_story_generation, story_session.id, db)
    
    return story_session

def process_story_generation(session_id: str, db: Session):
    """Background task to process story generation"""
    # This is a placeholder for actual AI generation logic
    # In a real implementation, this would:
    # 1. Fetch the story session
    # 2. Gather the source data (goals, tasks, etc.)
    # 3. Call the AI generation service
    # 4. Update the session with generated content
    # 5. Calculate word count and reading time
    # 6. Update processing status to "completed" or "failed"
    
    story_session = db.query(StorySession).filter(StorySession.id == session_id).first()
    if story_session:
        story_session.processing_status = "generating"
        db.commit()
        
        # Simulate generation process
        # In real implementation, replace with actual AI service call
        generated_text = f"This is a generated story for session {session_id}. It would contain a narrative based on the user's goals and tasks during the specified period."
        
        story_session.generated_text = generated_text
        story_session.word_count = len(generated_text.split())
        story_session.estimated_read_time = story_session.word_count * 4  # Assuming 250 WPM reading speed
        story_session.processing_status = "completed"
        story_session.generated_at = datetime.utcnow()
        
        db.commit()

@router.post("/{session_id}/publish", response_model=StorySessionSchema)
def publish_story_session(
    session_id: str,
    publish_request: PublishRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Publish a story session to specified platforms"""
    user_id = current_user["uid"]
    
    story_session = db.query(StorySession).filter(
        StorySession.id == session_id,
        StorySession.user_id == user_id
    ).first()
    
    if not story_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Story session not found"
        )
    
    if story_session.processing_status != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot publish story that hasn't been generated yet"
        )
    
    if not story_session.generated_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot publish story without generated content"
        )
    
    # Update posting information
    story_session.posted_to = publish_request.platforms
    story_session.scheduled_post_time = publish_request.scheduled_time
    
    if publish_request.scheduled_time and publish_request.scheduled_time > datetime.utcnow():
        story_session.posting_status = "scheduled"
    else:
        story_session.posting_status = "posted"
        story_session.posted_at = datetime.utcnow()
    
    story_session.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(story_session)
    
    return story_session

@router.post("/{session_id}/regenerate", response_model=StorySessionSchema)
def regenerate_story_session(
    session_id: str,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Regenerate content for an existing story session"""
    user_id = current_user["uid"]
    
    story_session = db.query(StorySession).filter(
        StorySession.id == session_id,
        StorySession.user_id == user_id
    ).first()
    
    if not story_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Story session not found"
        )
    
    # For regeneration, we just reset the status and increment counter
    # Custom generation parameters could be handled via separate update endpoint
    
    # Increment regeneration count and reset processing status
    story_session.regeneration_count += 1
    story_session.processing_status = "pending"
    story_session.error_message = None
    story_session.updated_at = datetime.utcnow()
    
    db.commit()
    
    # Add background task for regeneration
    background_tasks.add_task(process_story_generation, story_session.id, db)
    
    return story_session

@router.get("/content-types/options")
def get_content_type_options():
    """Get available content type options"""
    return {
        "content_types": [
            {"value": "summary", "label": "Summary", "description": "Factual summary of activities and achievements"},
            {"value": "story", "label": "Story", "description": "Narrative story format with creative elements"},
            {"value": "reflection", "label": "Reflection", "description": "Thoughtful reflection on progress and insights"},
            {"value": "achievement", "label": "Achievement", "description": "Celebration of accomplishments and milestones"}
        ]
    }

@router.get("/periods/options")
def get_period_options():
    """Get available summary period options"""
    return {
        "periods": [
            {"value": "daily", "label": "Daily", "description": "Daily summary"},
            {"value": "weekly", "label": "Weekly", "description": "Weekly summary"},
            {"value": "monthly", "label": "Monthly", "description": "Monthly summary"},
            {"value": "quarterly", "label": "Quarterly", "description": "Quarterly summary"},
            {"value": "project-based", "label": "Project-based", "description": "Based on specific project completion"},
            {"value": "custom", "label": "Custom", "description": "Custom date range"}
        ]
    }

@router.get("/platforms/options")
def get_platform_options():
    """Get available publishing platform options"""
    return {
        "platforms": [
            {"value": "instagram", "label": "Instagram", "description": "Instagram posts and stories"},
            {"value": "youtube", "label": "YouTube", "description": "YouTube videos and shorts"},
            {"value": "twitter", "label": "Twitter/X", "description": "Twitter posts and threads"},
            {"value": "linkedin", "label": "LinkedIn", "description": "LinkedIn posts and articles"},
            {"value": "facebook", "label": "Facebook", "description": "Facebook posts and stories"},
            {"value": "tiktok", "label": "TikTok", "description": "TikTok videos"},
            {"value": "blog", "label": "Personal Blog", "description": "Personal blog or website"}
        ]
    }
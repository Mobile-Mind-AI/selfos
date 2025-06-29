from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

from dependencies import get_db, get_current_user
from models import FeedbackLog
from schemas import FeedbackLogCreate, FeedbackLogUpdate, FeedbackLog as FeedbackLogSchema, FeedbackLogSummary

router = APIRouter(prefix="/feedback-logs", tags=["feedback-logs"])

@router.get("", response_model=List[FeedbackLogSchema])
def get_feedback_logs(
    context_type: Optional[str] = Query(None, description="Filter by context type"),
    feedback_type: Optional[str] = Query(None, description="Filter by feedback type"),
    session_id: Optional[str] = Query(None, description="Filter by session ID"),
    limit: int = Query(50, ge=1, le=1000, description="Maximum number of records to return"),
    offset: int = Query(0, ge=0, description="Number of records to skip"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's feedback logs with optional filtering"""
    user_id = current_user["uid"]
    
    query = db.query(FeedbackLog).filter(FeedbackLog.user_id == user_id)
    
    # Apply filters
    if context_type:
        query = query.filter(FeedbackLog.context_type == context_type)
    if feedback_type:
        query = query.filter(FeedbackLog.feedback_type == feedback_type)
    if session_id:
        query = query.filter(FeedbackLog.session_id == session_id)
    
    # Order by creation date (newest first) and apply pagination
    feedback_logs = query.order_by(desc(FeedbackLog.created_at)).offset(offset).limit(limit).all()
    
    return feedback_logs

@router.get("/{feedback_id}", response_model=FeedbackLogSchema)
def get_feedback_log(
    feedback_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific feedback log"""
    user_id = current_user["uid"]
    
    feedback_log = db.query(FeedbackLog).filter(
        FeedbackLog.id == feedback_id,
        FeedbackLog.user_id == user_id
    ).first()
    
    if not feedback_log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feedback log not found"
        )
    
    return feedback_log

@router.post("", response_model=FeedbackLogSchema)
def create_feedback_log(
    feedback_data: FeedbackLogCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new feedback log entry"""
    user_id = current_user["uid"]
    
    # Create the feedback log
    feedback_log = FeedbackLog(
        user_id=user_id,
        **feedback_data.model_dump(exclude_unset=True)
    )
    
    db.add(feedback_log)
    db.commit()
    db.refresh(feedback_log)
    
    return feedback_log

@router.put("/{feedback_id}", response_model=FeedbackLogSchema)
def update_feedback_log(
    feedback_id: str,
    feedback_update: FeedbackLogUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a feedback log entry"""
    user_id = current_user["uid"]
    
    feedback_log = db.query(FeedbackLog).filter(
        FeedbackLog.id == feedback_id,
        FeedbackLog.user_id == user_id
    ).first()
    
    if not feedback_log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feedback log not found"
        )
    
    # Update the feedback log
    update_data = feedback_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(feedback_log, field, value)
    
    db.commit()
    db.refresh(feedback_log)
    
    return feedback_log

@router.delete("/{feedback_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_feedback_log(
    feedback_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a feedback log entry"""
    user_id = current_user["uid"]
    
    feedback_log = db.query(FeedbackLog).filter(
        FeedbackLog.id == feedback_id,
        FeedbackLog.user_id == user_id
    ).first()
    
    if not feedback_log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feedback log not found"
        )
    
    db.delete(feedback_log)
    db.commit()

@router.get("/summary/stats", response_model=FeedbackLogSummary)
def get_feedback_summary(
    days: int = Query(30, ge=1, le=365, description="Number of days to include in summary"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get feedback summary statistics"""
    user_id = current_user["uid"]
    
    # Calculate date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # Base query for the time period
    base_query = db.query(FeedbackLog).filter(
        FeedbackLog.user_id == user_id,
        FeedbackLog.created_at >= start_date
    )
    
    # Get total counts by feedback type
    feedback_counts = db.query(
        FeedbackLog.feedback_type,
        func.count(FeedbackLog.id).label('count')
    ).filter(
        FeedbackLog.user_id == user_id,
        FeedbackLog.created_at >= start_date
    ).group_by(FeedbackLog.feedback_type).all()
    
    # Initialize counts
    total_feedback = 0
    positive_count = 0
    negative_count = 0
    neutral_count = 0
    
    for feedback_type, count in feedback_counts:
        total_feedback += count
        if feedback_type == "positive":
            positive_count = count
        elif feedback_type == "negative":
            negative_count = count
        elif feedback_type == "neutral":
            neutral_count = count
    
    # Calculate average feedback score (if numeric values exist)
    avg_score_result = db.query(func.avg(FeedbackLog.feedback_value)).filter(
        FeedbackLog.user_id == user_id,
        FeedbackLog.created_at >= start_date,
        FeedbackLog.feedback_value.isnot(None)
    ).scalar()
    
    average_score = float(avg_score_result) if avg_score_result else None
    
    # Get context breakdown
    context_counts = db.query(
        FeedbackLog.context_type,
        func.count(FeedbackLog.id).label('count')
    ).filter(
        FeedbackLog.user_id == user_id,
        FeedbackLog.created_at >= start_date
    ).group_by(FeedbackLog.context_type).all()
    
    context_breakdown = {context_type: count for context_type, count in context_counts}
    
    # Get recent feedback (last 5 entries)
    recent_feedback = base_query.order_by(desc(FeedbackLog.created_at)).limit(5).all()
    
    # Convert SQLAlchemy objects to dict for Pydantic
    recent_feedback_dicts = []
    for feedback in recent_feedback:
        feedback_dict = {
            "id": feedback.id,
            "user_id": feedback.user_id,
            "context_type": feedback.context_type,
            "context_id": feedback.context_id,
            "context_data": feedback.context_data,
            "feedback_type": feedback.feedback_type,
            "feedback_value": feedback.feedback_value,
            "comment": feedback.comment,
            "action_taken": feedback.action_taken,
            "reward_signal": feedback.reward_signal,
            "model_version": feedback.model_version,
            "session_id": feedback.session_id,
            "device_info": feedback.device_info,
            "feature_flags": feedback.feature_flags,
            "created_at": feedback.created_at,
            "processed_at": feedback.processed_at
        }
        recent_feedback_dicts.append(feedback_dict)
    
    return FeedbackLogSummary(
        total_feedback=total_feedback,
        positive_count=positive_count,
        negative_count=negative_count,
        neutral_count=neutral_count,
        average_score=average_score,
        context_breakdown=context_breakdown,
        recent_feedback=recent_feedback_dicts
    )

@router.get("/context-types/options")
def get_context_type_options():
    """Get common context type options for UI"""
    return {
        "context_types": [
            {"value": "task", "label": "Task", "description": "Feedback related to task interactions"},
            {"value": "goal", "label": "Goal", "description": "Feedback related to goal interactions"},
            {"value": "plan", "label": "Plan", "description": "Feedback on planning and suggestions"},
            {"value": "suggestion", "label": "AI Suggestion", "description": "Feedback on AI-generated suggestions"},
            {"value": "ui_interaction", "label": "UI Interaction", "description": "Feedback on user interface elements"},
            {"value": "search", "label": "Search", "description": "Feedback on search functionality"},
            {"value": "notification", "label": "Notification", "description": "Feedback on notifications"},
            {"value": "report", "label": "Report", "description": "Feedback on reports and analytics"},
            {"value": "import", "label": "Data Import", "description": "Feedback on data import processes"},
            {"value": "export", "label": "Data Export", "description": "Feedback on data export processes"},
            {"value": "general", "label": "General", "description": "General application feedback"}
        ]
    }

@router.post("/bulk", response_model=List[FeedbackLogSchema])
def create_bulk_feedback_logs(
    feedback_entries: List[FeedbackLogCreate],
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create multiple feedback log entries in bulk"""
    user_id = current_user["uid"]
    
    if len(feedback_entries) > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot create more than 100 feedback entries at once"
        )
    
    # Create all feedback logs
    feedback_logs = []
    for feedback_data in feedback_entries:
        feedback_log = FeedbackLog(
            user_id=user_id,
            **feedback_data.model_dump(exclude_unset=True)
        )
        feedback_logs.append(feedback_log)
    
    db.add_all(feedback_logs)
    db.commit()
    
    # Refresh all objects
    for feedback_log in feedback_logs:
        db.refresh(feedback_log)
    
    return feedback_logs

from pydantic import BaseModel

class BulkDeleteRequest(BaseModel):
    feedback_ids: List[str]

@router.post("/bulk-delete", status_code=status.HTTP_204_NO_CONTENT)
def delete_bulk_feedback_logs(
    request: BulkDeleteRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete multiple feedback log entries in bulk"""
    user_id = current_user["uid"]
    feedback_ids = request.feedback_ids
    
    if len(feedback_ids) > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete more than 100 feedback entries at once"
        )
    
    # Find all feedback logs belonging to the user
    feedback_logs = db.query(FeedbackLog).filter(
        FeedbackLog.id.in_(feedback_ids),
        FeedbackLog.user_id == user_id
    ).all()
    
    if len(feedback_logs) != len(feedback_ids):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Some feedback logs not found or don't belong to user"
        )
    
    # Delete all feedback logs
    for feedback_log in feedback_logs:
        db.delete(feedback_log)
    
    db.commit()
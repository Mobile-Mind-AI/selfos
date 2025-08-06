"""Analytics router for user behavior insights and preference history."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from dependencies import get_db, get_current_user
from services.preferences_service import get_user_preferences_history, get_preference_change_summary
from schemas import UserPreferencesHistoryItem, UserPreferencesChangeSummary

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/preferences/history", response_model=List[UserPreferencesHistoryItem])
def get_preferences_history(
    limit: Optional[int] = Query(50, ge=1, le=1000, description="Maximum number of records to return"),
    preference_name: Optional[str] = Query(None, description="Filter by specific preference name"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get the history of preference changes for the current user.
    
    This endpoint returns a chronological list of all preference changes,
    which is useful for understanding user behavior patterns and debugging.
    """
    user_id = current_user["uid"]
    
    history = get_user_preferences_history(
        db=db,
        user_id=user_id,
        limit=limit,
        preference_name=preference_name
    )
    
    if not history:
        return []
    
    return history


@router.get("/preferences/summary", response_model=UserPreferencesChangeSummary)
def get_preferences_change_summary(
    days_back: Optional[int] = Query(30, ge=1, le=365, description="Number of days to analyze"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a summary of preference changes over the specified time period.
    
    This provides aggregated analytics about how often and which preferences
    the user has been changing, helping identify usage patterns.
    """
    user_id = current_user["uid"]
    
    summary = get_preference_change_summary(
        db=db,
        user_id=user_id,
        days_back=days_back
    )
    
    return summary


# Admin-only endpoints (would need admin authentication in production)
@router.get("/users/{target_user_id}/preferences/history", response_model=List[UserPreferencesHistoryItem])
def get_user_preferences_history_admin(
    target_user_id: str,
    limit: Optional[int] = Query(50, ge=1, le=1000, description="Maximum number of records to return"),
    preference_name: Optional[str] = Query(None, description="Filter by specific preference name"),
    current_user: dict = Depends(get_current_user),  # In production, this would check for admin role
    db: Session = Depends(get_db)
):
    """
    [ADMIN ONLY] Get preference change history for any user.
    
    This endpoint is intended for administrators to analyze user behavior
    across the platform for product development and user experience improvements.
    
    Note: In production, this should be protected with admin-only authentication.
    """
    # TODO: Add admin role check here
    # if not current_user.get("is_admin"):
    #     raise HTTPException(status_code=403, detail="Admin access required")
    
    history = get_user_preferences_history(
        db=db,
        user_id=target_user_id,
        limit=limit,
        preference_name=preference_name
    )
    
    if not history:
        raise HTTPException(status_code=404, detail="No preference history found for this user")
    
    return history


@router.get("/users/{target_user_id}/preferences/summary", response_model=UserPreferencesChangeSummary)
def get_user_preferences_change_summary_admin(
    target_user_id: str,
    days_back: Optional[int] = Query(30, ge=1, le=365, description="Number of days to analyze"),
    current_user: dict = Depends(get_current_user),  # In production, this would check for admin role
    db: Session = Depends(get_db)
):
    """
    [ADMIN ONLY] Get preference change summary for any user.
    
    This provides administrators with insights into how individual users
    are interacting with preference settings, which can inform UX decisions.
    
    Note: In production, this should be protected with admin-only authentication.
    """
    # TODO: Add admin role check here
    # if not current_user.get("is_admin"):
    #     raise HTTPException(status_code=403, detail="Admin access required")
    
    summary = get_preference_change_summary(
        db=db,
        user_id=target_user_id,
        days_back=days_back
    )
    
    return summary

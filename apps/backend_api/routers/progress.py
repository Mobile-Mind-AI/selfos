from dependencies import get_current_user, get_db
from fastapi import APIRouter, Depends, HTTPException, status
from services.progress import get_user_progress_insights, predict_completion_date
from sqlalchemy.orm import Session

router = APIRouter()


@router.get("/progress/insights")
async def get_progress_insights(
    db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)
):
    """
    Get comprehensive progress insights for the current user.

    Returns analytics including:
    - Goal and task completion rates
    - Weekly and monthly velocity
    - Most productive life area
    - Personalized recommendations
    """
    insights = await get_user_progress_insights(db, current_user["uid"])

    if "error" in insights:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate insights: {insights['error']}",
        )

    return insights


@router.get("/progress/goals/{goal_id}/prediction")
async def get_goal_completion_prediction(
    goal_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Predict when a goal might be completed based on current velocity.

    Args:
        goal_id: ID of the goal to predict completion for

    Returns:
        Predicted completion date or null if cannot predict
    """
    prediction = await predict_completion_date(db, goal_id, current_user["uid"])

    if prediction is None:
        return {
            "goal_id": goal_id,
            "predicted_completion_date": None,
            "reason": "Unable to predict - goal may be completed or insufficient data",
        }

    return {
        "goal_id": goal_id,
        "predicted_completion_date": prediction,
        "reason": "Prediction based on recent task completion velocity",
    }


@router.get("/progress/summary")
async def get_progress_summary(
    db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)
):
    """
    Get a quick progress summary for dashboard display.

    Returns:
        Quick stats suitable for dashboard widgets
    """
    insights = await get_user_progress_insights(db, current_user["uid"])

    if "error" in insights:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate summary: {insights['error']}",
        )

    # Return a condensed version suitable for dashboard
    return {
        "total_goals": insights.get("total_goals", 0),
        "completed_goals": insights.get("completed_goals", 0),
        "goal_completion_rate": insights.get("goal_completion_rate", 0),
        "total_tasks": insights.get("total_tasks", 0),
        "completed_tasks": insights.get("completed_tasks", 0),
        "task_completion_rate": insights.get("task_completion_rate", 0),
        "weekly_velocity": insights.get("weekly_velocity", 0),
        "most_productive_area": insights.get("most_productive_area"),
        "top_recommendation": (
            insights.get("recommendations", [None])[0]
            if insights.get("recommendations")
            else None
        ),
        "last_updated": insights.get("last_updated"),
    }

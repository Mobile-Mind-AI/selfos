"""
Conversation and Intent Classification API Router

Provides endpoints for:
- Natural language intent classification
- Entity extraction
- Conversation flow management
- Intent feedback collection
- Analytics and debugging
"""

import uuid
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import desc, func, and_

from dependencies import get_db, get_current_user
from models import ConversationLog, ConversationSession, IntentFeedback, User, AssistantProfile
from schemas.intent_schemas import (
    ConversationMessageRequest, ConversationMessageResponse,
    IntentClassificationResult, ConversationState, NextAction,
    ConversationLogCreate, ConversationLogOut,
    ConversationSessionCreate, ConversationSessionOut,
    IntentFeedbackCreate, IntentFeedbackOut,
    IntentAnalytics, ConversationAnalytics, EntityExtractionAccuracy
)
from services.intent_service import ConversationFlowManager, IntentClassifier

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/conversation", tags=["conversation"])

# Initialize services
conversation_manager = ConversationFlowManager()
intent_classifier = IntentClassifier()


@router.post("/message", response_model=ConversationMessageResponse)
async def process_message(
    request: ConversationMessageRequest,
    background_tasks: BackgroundTasks,
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Process a user message with intent classification and conversation flow management.
    
    This is the main endpoint for conversational AI interactions.
    """
    try:
        user_id = current_user["uid"]
        
        # Get assistant profile
        assistant_profile = None
        if request.assistant_id:
            assistant_profile = db.query(AssistantProfile).filter(
                and_(
                    AssistantProfile.id == request.assistant_id,
                    AssistantProfile.user_id == user_id
                )
            ).first()
            if not assistant_profile:
                raise HTTPException(status_code=404, detail="Assistant profile not found")
        else:
            # Use default assistant profile
            assistant_profile = db.query(AssistantProfile).filter(
                and_(
                    AssistantProfile.user_id == user_id,
                    AssistantProfile.is_default == True
                )
            ).first()
        
        # Get or create session
        session_id = request.session_id
        if not session_id:
            session_id = str(uuid.uuid4())
            # Create new session in background
            background_tasks.add_task(
                create_conversation_session,
                user_id=user_id,
                session_id=session_id,
                assistant_id=assistant_profile.id if assistant_profile else None,
                db=db
            )
        
        # Process the message with assistant personality
        result = await conversation_manager.process_message(
            user_id=user_id,
            message=request.message,
            conversation_context={
                "session_id": session_id,
                "include_context": request.include_context,
                "assistant_profile": assistant_profile.id if assistant_profile else None
            },
            assistant_profile=assistant_profile
        )
        
        # Store conversation log in background
        background_tasks.add_task(
            store_conversation_log,
            user_id=user_id,
            session_id=session_id,
            message=request.message,
            intent_result=result["intent_result"],
            conversation_state=result["conversation_state"],
            db=db
        )
        
        # Update session in background
        background_tasks.add_task(
            update_conversation_session,
            session_id=session_id,
            conversation_state=result["conversation_state"],
            intent_result=result["intent_result"],
            db=db
        )
        
        return ConversationMessageResponse(
            intent_result=IntentClassificationResult(**result["intent_result"]),
            conversation_state=ConversationState(**result["conversation_state"]),
            next_actions=[NextAction(**action) for action in result["next_actions"]],
            requires_clarification=result["requires_clarification"],
            session_id=session_id
        )
        
    except Exception as e:
        logger.error(f"Error processing message for user {current_user['uid']}: {e}")
        raise HTTPException(status_code=500, detail="Failed to process message")


@router.post("/classify", response_model=IntentClassificationResult)
async def classify_intent_only(
    message: str,
    include_entities: bool = Query(True, description="Include entity extraction"),
    current_user: Dict = Depends(get_current_user)
):
    """
    Classify intent only without conversation flow management.
    
    Useful for testing and debugging intent classification.
    """
    try:
        user_context = None
        if include_entities:
            # Get basic user context for better classification
            user_context = {"user_id": current_user["uid"]}
        
        result = await intent_classifier.classify_intent(message, user_context)
        
        return IntentClassificationResult(
            intent=result.intent,
            confidence=result.confidence,
            entities=result.entities,
            reasoning=result.reasoning,
            fallback_used=result.fallback_used,
            processing_time_ms=0.0  # Not tracked for this endpoint
        )
        
    except Exception as e:
        logger.error(f"Error classifying intent: {e}")
        raise HTTPException(status_code=500, detail="Failed to classify intent")


@router.get("/sessions", response_model=List[ConversationSessionOut])
async def get_user_sessions(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    status: Optional[str] = Query(None, description="Filter by session status"),
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's conversation sessions."""
    try:
        user_id = current_user["uid"]
        
        query = db.query(ConversationSession).filter(
            ConversationSession.user_id == user_id
        )
        
        if status:
            query = query.filter(ConversationSession.status == status)
        
        sessions = query.order_by(
            desc(ConversationSession.last_activity)
        ).offset(offset).limit(limit).all()
        
        return [ConversationSessionOut.from_orm(session) for session in sessions]
        
    except Exception as e:
        logger.error(f"Error fetching sessions: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch sessions")


@router.get("/sessions/{session_id}", response_model=ConversationSessionOut)
async def get_session(
    session_id: str,
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get specific conversation session details."""
    try:
        user_id = current_user["uid"]
        
        session = db.query(ConversationSession).filter(
            and_(
                ConversationSession.id == session_id,
                ConversationSession.user_id == user_id
            )
        ).first()
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return ConversationSessionOut.from_orm(session)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching session: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch session")


@router.get("/sessions/{session_id}/logs", response_model=List[ConversationLogOut])
async def get_session_logs(
    session_id: str,
    limit: int = Query(50, ge=1, le=200),
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get conversation logs for a specific session."""
    try:
        user_id = current_user["uid"]
        
        # Verify session belongs to user
        session = db.query(ConversationSession).filter(
            and_(
                ConversationSession.id == session_id,
                ConversationSession.user_id == user_id
            )
        ).first()
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        logs = db.query(ConversationLog).filter(
            and_(
                ConversationLog.session_id == session_id,
                ConversationLog.user_id == user_id
            )
        ).order_by(ConversationLog.conversation_turn).limit(limit).all()
        
        return [ConversationLogOut.from_orm(log) for log in logs]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching session logs: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch session logs")


@router.post("/feedback", response_model=IntentFeedbackOut)
async def provide_intent_feedback(
    feedback: IntentFeedbackCreate,
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Provide feedback on intent classification accuracy.
    
    This helps improve the intent classification model over time.
    """
    try:
        user_id = current_user["uid"]
        
        # Verify conversation log belongs to user
        conversation_log = db.query(ConversationLog).filter(
            and_(
                ConversationLog.id == feedback.conversation_log_id,
                ConversationLog.user_id == user_id
            )
        ).first()
        
        if not conversation_log:
            raise HTTPException(status_code=404, detail="Conversation log not found")
        
        # Create feedback entry
        feedback_entry = IntentFeedback(
            user_id=user_id,
            conversation_log_id=feedback.conversation_log_id,
            original_intent=feedback.original_intent,
            original_confidence=feedback.original_confidence,
            original_entities=feedback.original_entities,
            corrected_intent=feedback.corrected_intent,
            corrected_entities=feedback.corrected_entities,
            feedback_type=feedback.feedback_type,
            user_comment=feedback.user_comment
        )
        
        db.add(feedback_entry)
        db.commit()
        db.refresh(feedback_entry)
        
        logger.info(f"Intent feedback received from user {user_id}: "
                   f"{feedback.original_intent} -> {feedback.corrected_intent}")
        
        return IntentFeedbackOut.from_orm(feedback_entry)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error storing intent feedback: {e}")
        raise HTTPException(status_code=500, detail="Failed to store feedback")


@router.get("/analytics/intent", response_model=IntentAnalytics)
async def get_intent_analytics(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get intent classification analytics for the user."""
    try:
        user_id = current_user["uid"]
        since_date = datetime.now() - timedelta(days=days)
        
        # Get total messages
        total_messages = db.query(ConversationLog).filter(
            and_(
                ConversationLog.user_id == user_id,
                ConversationLog.created_at >= since_date
            )
        ).count()
        
        if total_messages == 0:
            return IntentAnalytics(
                total_messages=0,
                intent_distribution={},
                avg_confidence=0.0,
                fallback_usage_rate=0.0,
                avg_processing_time_ms=0.0,
                success_rate=0.0,
                common_failure_patterns=[]
            )
        
        # Intent distribution
        intent_distribution = dict(
            db.query(ConversationLog.intent, func.count(ConversationLog.id))
            .filter(
                and_(
                    ConversationLog.user_id == user_id,
                    ConversationLog.created_at >= since_date
                )
            )
            .group_by(ConversationLog.intent)
            .all()
        )
        
        # Average confidence
        avg_confidence = db.query(func.avg(ConversationLog.confidence)).filter(
            and_(
                ConversationLog.user_id == user_id,
                ConversationLog.created_at >= since_date
            )
        ).scalar() or 0.0
        
        # Fallback usage rate
        fallback_count = db.query(ConversationLog).filter(
            and_(
                ConversationLog.user_id == user_id,
                ConversationLog.created_at >= since_date,
                ConversationLog.fallback_used == True
            )
        ).count()
        
        fallback_usage_rate = fallback_count / total_messages if total_messages > 0 else 0.0
        
        # Average processing time
        avg_processing_time = db.query(func.avg(ConversationLog.processing_time_ms)).filter(
            and_(
                ConversationLog.user_id == user_id,
                ConversationLog.created_at >= since_date,
                ConversationLog.processing_time_ms.isnot(None)
            )
        ).scalar() or 0.0
        
        # Success rate (confidence >= 0.85)
        high_confidence_count = db.query(ConversationLog).filter(
            and_(
                ConversationLog.user_id == user_id,
                ConversationLog.created_at >= since_date,
                ConversationLog.confidence >= 0.85
            )
        ).count()
        
        success_rate = high_confidence_count / total_messages if total_messages > 0 else 0.0
        
        # Common failure patterns (low confidence intents)
        failure_patterns = db.query(
            ConversationLog.intent,
            func.count(ConversationLog.id).label('count'),
            func.avg(ConversationLog.confidence).label('avg_confidence')
        ).filter(
            and_(
                ConversationLog.user_id == user_id,
                ConversationLog.created_at >= since_date,
                ConversationLog.confidence < 0.85
            )
        ).group_by(ConversationLog.intent).order_by(desc('count')).limit(5).all()
        
        common_failure_patterns = [
            {
                "intent": pattern.intent,
                "count": pattern.count,
                "avg_confidence": float(pattern.avg_confidence)
            }
            for pattern in failure_patterns
        ]
        
        return IntentAnalytics(
            total_messages=total_messages,
            intent_distribution=intent_distribution,
            avg_confidence=float(avg_confidence),
            fallback_usage_rate=fallback_usage_rate,
            avg_processing_time_ms=float(avg_processing_time),
            success_rate=success_rate,
            common_failure_patterns=common_failure_patterns
        )
        
    except Exception as e:
        logger.error(f"Error generating intent analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate analytics")


@router.get("/analytics/conversation", response_model=ConversationAnalytics)
async def get_conversation_analytics(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get conversation session analytics for the user."""
    try:
        user_id = current_user["uid"]
        since_date = datetime.now() - timedelta(days=days)
        
        # Total sessions
        total_sessions = db.query(ConversationSession).filter(
            and_(
                ConversationSession.user_id == user_id,
                ConversationSession.started_at >= since_date
            )
        ).count()
        
        if total_sessions == 0:
            return ConversationAnalytics(
                total_sessions=0,
                avg_session_length=0.0,
                completion_rate=0.0,
                avg_turns_per_session=0.0,
                intent_success_rate=0.0,
                most_common_intents=[],
                user_satisfaction_score=None
            )
        
        # Completion rate
        completed_sessions = db.query(ConversationSession).filter(
            and_(
                ConversationSession.user_id == user_id,
                ConversationSession.started_at >= since_date,
                ConversationSession.status == 'completed'
            )
        ).count()
        
        completion_rate = completed_sessions / total_sessions if total_sessions > 0 else 0.0
        
        # Average turns per session
        avg_turns = db.query(func.avg(ConversationSession.turn_count)).filter(
            and_(
                ConversationSession.user_id == user_id,
                ConversationSession.started_at >= since_date
            )
        ).scalar() or 0.0
        
        # Intent success rate
        total_successful = db.query(func.sum(ConversationSession.successful_intents)).filter(
            and_(
                ConversationSession.user_id == user_id,
                ConversationSession.started_at >= since_date
            )
        ).scalar() or 0
        
        total_attempts = db.query(
            func.sum(ConversationSession.successful_intents + ConversationSession.failed_intents)
        ).filter(
            and_(
                ConversationSession.user_id == user_id,
                ConversationSession.started_at >= since_date
            )
        ).scalar() or 0
        
        intent_success_rate = total_successful / total_attempts if total_attempts > 0 else 0.0
        
        # Most common intents from logs
        common_intents = db.query(
            ConversationLog.intent,
            func.count(ConversationLog.id).label('count')
        ).join(ConversationSession).filter(
            and_(
                ConversationSession.user_id == user_id,
                ConversationSession.started_at >= since_date
            )
        ).group_by(ConversationLog.intent).order_by(desc('count')).limit(5).all()
        
        most_common_intents = [
            {"intent": intent.intent, "count": intent.count}
            for intent in common_intents
        ]
        
        # Calculate average session length (in minutes)
        session_lengths = db.query(
            func.extract('epoch', ConversationSession.last_activity - ConversationSession.started_at) / 60
        ).filter(
            and_(
                ConversationSession.user_id == user_id,
                ConversationSession.started_at >= since_date,
                ConversationSession.last_activity.isnot(None)
            )
        ).all()
        
        avg_session_length = sum(length[0] for length in session_lengths if length[0]) / len(session_lengths) if session_lengths else 0.0
        
        return ConversationAnalytics(
            total_sessions=total_sessions,
            avg_session_length=float(avg_session_length),
            completion_rate=completion_rate,
            avg_turns_per_session=float(avg_turns),
            intent_success_rate=intent_success_rate,
            most_common_intents=most_common_intents,
            user_satisfaction_score=None  # Could be calculated from feedback
        )
        
    except Exception as e:
        logger.error(f"Error generating conversation analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate analytics")


# Background task functions

async def create_conversation_session(user_id: str, session_id: str, assistant_id: Optional[str], db: Session):
    """Create a new conversation session."""
    try:
        session = ConversationSession(
            id=session_id,
            user_id=user_id,
            session_type="chat",
            status="active"
        )
        # Store assistant_id in context_data if provided
        if assistant_id:
            session.context_data = {"assistant_id": assistant_id}
        
        db.add(session)
        db.commit()
        logger.info(f"Created conversation session {session_id} for user {user_id} with assistant {assistant_id}")
    except Exception as e:
        logger.error(f"Error creating conversation session: {e}")
        db.rollback()


async def store_conversation_log(
    user_id: str,
    session_id: str,
    message: str,
    intent_result: Dict[str, Any],
    conversation_state: Dict[str, Any],
    db: Session
):
    """Store conversation log entry."""
    try:
        log_entry = ConversationLog(
            user_id=user_id,
            session_id=session_id,
            user_message=message,
            intent=intent_result["intent"],
            confidence=intent_result["confidence"],
            entities=intent_result["entities"],
            reasoning=intent_result.get("reasoning"),
            fallback_used=intent_result["fallback_used"],
            processing_time_ms=intent_result["processing_time_ms"],
            conversation_turn=conversation_state["turn_count"],
            previous_intent=conversation_state.get("current_intent")
        )
        db.add(log_entry)
        db.commit()
    except Exception as e:
        logger.error(f"Error storing conversation log: {e}")
        db.rollback()


async def update_conversation_session(
    session_id: str,
    conversation_state: Dict[str, Any],
    intent_result: Dict[str, Any],
    db: Session
):
    """Update conversation session with latest state."""
    try:
        session = db.query(ConversationSession).filter(
            ConversationSession.id == session_id
        ).first()
        
        if session:
            session.current_intent = intent_result["intent"]
            session.turn_count = conversation_state["turn_count"]
            session.last_activity = datetime.now()
            
            # Update success/failure counts
            if intent_result["confidence"] >= 0.85:
                session.successful_intents += 1
            else:
                session.failed_intents += 1
            
            # Update average confidence
            total_intents = session.successful_intents + session.failed_intents
            if total_intents > 0:
                if session.avg_confidence:
                    session.avg_confidence = (
                        (session.avg_confidence * (total_intents - 1) + intent_result["confidence"]) / total_intents
                    )
                else:
                    session.avg_confidence = intent_result["confidence"]
            
            db.commit()
    except Exception as e:
        logger.error(f"Error updating conversation session: {e}")
        db.rollback()
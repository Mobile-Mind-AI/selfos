"""
AI Router

API endpoints for AI-powered goal decomposition, task generation, and chat.
"""

import logging
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field

from dependencies import get_current_user
from schemas import User as UserSchema
from services.enhanced_memory import EnhancedMemoryService, create_memory_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai", tags=["ai"])


class GoalDecompositionRequest(BaseModel):
    """Request for goal decomposition."""
    goal_description: str = Field(..., description="Description of the goal to decompose")
    life_areas: List[Dict[str, Any]] = Field(default_factory=list, description="User's life areas")
    existing_goals: List[Dict[str, Any]] = Field(default_factory=list, description="Existing goals")
    user_preferences: Optional[Dict[str, Any]] = Field(None, description="User preferences")
    additional_context: Optional[str] = Field(None, description="Additional context")


class TaskSuggestion(BaseModel):
    """Individual task suggestion."""
    title: str
    description: str
    estimated_duration: Optional[int] = None
    priority: Optional[str] = None
    timeline: Optional[str] = None
    dependencies: List[str] = Field(default_factory=list)
    resources_needed: List[str] = Field(default_factory=list)


class GoalDecompositionResponse(BaseModel):
    """Response from goal decomposition."""
    request_id: str
    status: str
    content: str
    suggested_tasks: List[TaskSuggestion] = Field(default_factory=list)
    overall_timeline: Optional[str] = None
    potential_challenges: List[str] = Field(default_factory=list)
    success_metrics: List[str] = Field(default_factory=list)
    next_steps: List[str] = Field(default_factory=list)
    confidence_score: Optional[float] = None
    token_usage: Optional[Dict[str, int]] = None
    cost_estimate: Optional[float] = None
    processing_time: Optional[float] = None
    model_used: Optional[str] = None


class ChatRequest(BaseModel):
    """Request for chat/conversation."""
    message: str = Field(..., description="User message")
    conversation_history: List[Dict[str, str]] = Field(default_factory=list, description="Previous conversation")
    user_context: Optional[Dict[str, Any]] = Field(None, description="User context")


class ChatResponse(BaseModel):
    """Response from chat."""
    request_id: str
    status: str
    content: str
    intent_detected: Optional[str] = None
    suggested_actions: List[Dict[str, Any]] = Field(default_factory=list)
    follow_up_questions: List[str] = Field(default_factory=list)
    extracted_goals: List[str] = Field(default_factory=list)
    token_usage: Optional[Dict[str, int]] = None
    processing_time: Optional[float] = None
    model_used: Optional[str] = None


class HealthResponse(BaseModel):
    """AI service health response."""
    status: str
    providers: Dict[str, str]
    cache_size: int
    metrics: Dict[str, Any]


# Initialize services
memory_service = None
ai_orchestrator = None
ai_models_module = None


def get_ai_orchestrator():
    """Get AI orchestrator instance."""
    global ai_orchestrator, ai_models_module
    if ai_orchestrator is None:
        try:
            import sys
            import os
            
            # Find the ai_engine directory - works in both Docker and local environments
            current_dir = os.path.dirname(__file__)
            # Try multiple possible locations
            possible_paths = [
                os.path.join(current_dir, '..', 'ai_engine'),  # Docker path
                os.path.join(current_dir, '..', '..', 'ai_engine'),  # Local tests path
                os.path.join(current_dir, '..', '..', 'apps', 'ai_engine'),  # Repository root path
            ]
            ai_engine_path = None
            for path in possible_paths:
                if os.path.exists(os.path.join(path, 'config.py')):
                    ai_engine_path = path
                    break
            
            if not ai_engine_path:
                raise Exception(f"Could not find ai_engine directory. Tried: {possible_paths}")
            
            # Add libs path first for prompts
            libs_path = os.path.join(os.path.dirname(os.path.dirname(ai_engine_path)), 'libs')
            if libs_path not in sys.path:
                sys.path.insert(0, libs_path)
            
            # Add AI engine path
            if ai_engine_path not in sys.path:
                sys.path.insert(0, ai_engine_path)
            
            # Use dynamic loading with proper module isolation to avoid conflicts
            import importlib.util
            
            # Load config first
            config_path = os.path.join(ai_engine_path, 'config.py')
            config_spec = importlib.util.spec_from_file_location("ai_config", config_path)
            ai_config_module = importlib.util.module_from_spec(config_spec)
            config_spec.loader.exec_module(ai_config_module)
            AIConfig = ai_config_module.AIConfig
            
            # Load models module first (before orchestrator which depends on it)
            models_path = os.path.join(ai_engine_path, 'models.py')
            models_spec = importlib.util.spec_from_file_location("ai_models", models_path)
            ai_models_module = importlib.util.module_from_spec(models_spec)
            models_spec.loader.exec_module(ai_models_module)
            
            # Load orchestrator last
            orchestrator_path = os.path.join(ai_engine_path, 'orchestrator.py')
            orchestrator_spec = importlib.util.spec_from_file_location("ai_orchestrator", orchestrator_path)
            ai_orchestrator_module = importlib.util.module_from_spec(orchestrator_spec)
            orchestrator_spec.loader.exec_module(ai_orchestrator_module)
            AIOrchestrator = ai_orchestrator_module.AIOrchestrator
            
            logger.info("Using dynamic imports for AI modules")
            
            # Create development config for now
            config = AIConfig.create_development_config()
            ai_orchestrator = AIOrchestrator(config)
            logger.info("AI orchestrator initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize AI orchestrator: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AI service not available"
            )
    return ai_orchestrator


def get_memory_service():
    """Get memory service instance."""
    global memory_service
    if memory_service is None:
        try:
            memory_service = create_memory_service(vector_store_type="memory")
            logger.info("Memory service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize memory service: {e}")
            # Continue without memory service for now
            memory_service = None
    return memory_service


@router.post("/decompose-goal", response_model=GoalDecompositionResponse, status_code=200)
async def decompose_goal(
    request: GoalDecompositionRequest,
    current_user: UserSchema = Depends(get_current_user)
):
    """
    Decompose a goal into actionable tasks using AI.
    
    This endpoint takes a goal description and breaks it down into:
    - Specific actionable tasks
    - Timeline estimates
    - Success metrics
    - Potential challenges
    - Next steps
    """
    try:
        # Get AI orchestrator
        orchestrator = get_ai_orchestrator()
        
        # Import request models from AI engine  
        AIGoalRequest = ai_models_module.GoalDecompositionRequest
        
        # Create AI request
        ai_request = AIGoalRequest(
            request_type=ai_models_module.RequestType.GOAL_DECOMPOSITION,  # Required by AIRequest base class
            user_id=str(current_user["uid"]),
            prompt="",  # Will be generated by orchestrator
            goal_description=request.goal_description,
            life_areas=request.life_areas,
            existing_goals=request.existing_goals,
            user_preferences=request.user_preferences,
            additional_context=request.additional_context
        )
        
        # Process request
        ai_response = await orchestrator.decompose_goal(ai_request)
        
        # Convert suggested tasks to response format
        suggested_tasks = []
        for task in ai_response.suggested_tasks:
            suggested_tasks.append(TaskSuggestion(
                title=task.title,
                description=task.description,
                estimated_duration=task.estimated_duration,
                priority=task.priority,
                timeline=task.timeline,
                dependencies=[],  # task.dependencies are integers, convert if needed
                resources_needed=task.resources_needed
            ))
        
        # Store in memory if available
        memory_service = get_memory_service()
        if memory_service:
            try:
                await memory_service.store_memory(
                    user_id=str(current_user["uid"]),
                    content=f"Goal: {request.goal_description}\nAI Response: {ai_response.content}",
                    content_type="goal_decomposition",
                    metadata={
                        "goal_description": request.goal_description,
                        "request_id": ai_response.request_id,
                        "model_used": ai_response.model_used,
                        "confidence_score": ai_response.confidence_score
                    }
                )
                logger.info(f"Stored goal decomposition in memory for user {current_user['uid']}")
            except Exception as e:
                logger.warning(f"Failed to store in memory: {e}")
        
        # Return response
        return GoalDecompositionResponse(
            request_id=ai_response.request_id,
            status=ai_response.status.value,
            content=ai_response.content,
            suggested_tasks=suggested_tasks,
            overall_timeline=ai_response.overall_timeline,
            potential_challenges=ai_response.potential_challenges,
            success_metrics=ai_response.success_metrics,
            next_steps=ai_response.next_steps,
            confidence_score=ai_response.confidence_score,
            token_usage=ai_response.token_usage,
            cost_estimate=ai_response.cost_estimate,
            processing_time=ai_response.processing_time,
            model_used=ai_response.model_used
        )
        
    except Exception as e:
        logger.error(f"Goal decomposition failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Goal decomposition failed: {str(e)}"
        )


@router.post("/chat", response_model=ChatResponse, status_code=200)
async def chat(
    request: ChatRequest,
    current_user: UserSchema = Depends(get_current_user)
):
    """
    Chat with AI assistant for goal and task management.
    
    This endpoint provides conversational AI for:
    - Goal setting assistance
    - Task planning guidance
    - Progress review
    - General life planning advice
    """
    try:
        # Get AI orchestrator
        orchestrator = get_ai_orchestrator()
        
        # Import request models from AI engine
        AIConversationRequest = ai_models_module.ConversationRequest
        
        # Create AI request
        ai_request = AIConversationRequest(
            request_type=ai_models_module.RequestType.CONVERSATION,  # Required by AIRequest base class
            user_id=str(current_user["uid"]),
            prompt="",  # Will be generated by orchestrator
            message=request.message,
            conversation_history=request.conversation_history,
            user_context=request.user_context
        )
        
        # Process request
        ai_response = await orchestrator.chat(ai_request)
        
        # Store conversation in memory if available
        memory_service = get_memory_service()
        if memory_service:
            try:
                await memory_service.store_memory(
                    user_id=str(current_user["uid"]),
                    content=f"User: {request.message}\nAI: {ai_response.content}",
                    content_type="conversation",
                    metadata={
                        "user_message": request.message,
                        "request_id": ai_response.request_id,
                        "intent_detected": ai_response.intent_detected,
                        "model_used": ai_response.model_used
                    }
                )
                logger.info(f"Stored conversation in memory for user {current_user['uid']}")
            except Exception as e:
                logger.warning(f"Failed to store conversation in memory: {e}")
        
        # Return response
        return ChatResponse(
            request_id=ai_response.request_id,
            status=ai_response.status.value,
            content=ai_response.content,
            intent_detected=ai_response.intent_detected,
            suggested_actions=ai_response.suggested_actions,
            follow_up_questions=ai_response.follow_up_questions,
            extracted_goals=ai_response.extracted_goals,
            token_usage=ai_response.token_usage,
            processing_time=ai_response.processing_time,
            model_used=ai_response.model_used
        )
        
    except Exception as e:
        logger.error(f"Chat failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat failed: {str(e)}"
        )


@router.get("/health", response_model=HealthResponse, status_code=200)
async def health_check():
    """
    Check AI service health and status.
    
    Returns information about:
    - AI provider availability
    - Cache statistics
    - Processing metrics
    - Service status
    """
    try:
        # Get AI orchestrator
        orchestrator = get_ai_orchestrator()
        
        # Get health information
        health_info = await orchestrator.health_check()
        
        return HealthResponse(
            status=health_info["status"],
            providers=health_info["providers"],
            cache_size=health_info["cache_size"],
            metrics=health_info["metrics"]
        )
        
    except Exception as e:
        import traceback
        logger.error(f"Health check failed: {e}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return HealthResponse(
            status="error",
            providers={},
            cache_size=0,
            metrics={"error": str(e), "traceback": traceback.format_exc()}
        )


@router.get("/memory/stats", status_code=200)
async def get_memory_stats(
    current_user: UserSchema = Depends(get_current_user)
):
    """
    Get memory statistics for the current user.
    
    Returns information about stored memories, search statistics, and storage health.
    """
    try:
        memory_service = get_memory_service()
        if not memory_service:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Memory service not available"
            )
        
        stats = await memory_service.get_memory_stats(str(current_user["uid"]))
        return stats
        
    except Exception as e:
        logger.error(f"Memory stats failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Memory stats failed: {str(e)}"
        )


@router.post("/memory/search", status_code=200)
async def search_memories(
    query: str,
    content_types: Optional[List[str]] = None,
    limit: int = 10,
    min_similarity: Optional[float] = None,
    current_user: UserSchema = Depends(get_current_user)
):
    """
    Search user's memories using semantic similarity.
    
    This endpoint allows searching through stored conversations, goal decompositions,
    and other AI interactions using natural language queries.
    """
    try:
        memory_service = get_memory_service()
        if not memory_service:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Memory service not available"
            )
        
        results = await memory_service.search_memories(
            user_id=str(current_user["uid"]),
            query=query,
            content_types=content_types,
            limit=limit,
            min_similarity=min_similarity
        )
        
        # Convert results to serializable format
        serialized_results = []
        for result in results:
            serialized_results.append({
                "id": result.entry.id,
                "content": result.entry.content,
                "content_type": result.entry.content_type,
                "metadata": result.entry.metadata,
                "similarity_score": result.similarity_score,
                "context_relevance": result.context_relevance,
                "combined_score": result.combined_score,
                "created_at": result.entry.created_at.isoformat()
            })
        
        return {
            "query": query,
            "results": serialized_results,
            "total_results": len(serialized_results)
        }
        
    except Exception as e:
        logger.error(f"Memory search failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Memory search failed: {str(e)}"
        )
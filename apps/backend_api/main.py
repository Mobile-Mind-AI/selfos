from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import db  # ensure database engine & Base
from db import engine, Base

# Import ORM models so they are registered
import models

# Import dependencies to initialize Firebase
import dependencies

# Import middleware
from middleware import ErrorHandlingMiddleware, RequestLoggingMiddleware, RateLimitingMiddleware

# Include API routers
from routers.auth import router as auth_router
from routers.goals import router as goals_router
from routers.projects import router as projects_router
from routers.tasks import router as tasks_router
from routers.life_areas import router as life_areas_router
from routers.media_attachments import router as media_attachments_router
from routers.user_preferences import router as user_preferences_router
from routers.feedback_logs import router as feedback_logs_router
from routers.story_sessions import router as story_sessions_router
from routers.health import router as health_router
from routers.ai import router as ai_router
from routers.conversation import router as conversation_router
from routers.assistant_profiles import router as assistant_profiles_router
from routers.onboarding import router as onboarding_router
from routers.avatars import router as avatars_router
from routers.assistant import router as assistant_router
from routers.personal_config import router as personal_config_router

# Import event system
import event_consumers

app = FastAPI(
    title="SelfOS Backend API",
    description="Backend API for SelfOS - Personal Life Management System",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add middleware (order matters - first added is executed last)
app.add_middleware(ErrorHandlingMiddleware)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(RateLimitingMiddleware, requests_per_minute=60, requests_per_hour=1000, burst_limit=10)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "SelfOS Backend API"}

@app.on_event("startup")
async def on_startup():
    # Create database tables
    Base.metadata.create_all(bind=engine)
    
    # Initialize event consumers
    await event_consumers.initialize_consumers()

@app.on_event("shutdown")
async def on_shutdown():
    # Cleanup event consumers
    await event_consumers.shutdown_consumers()

# Register routers
app.include_router(health_router)
app.include_router(auth_router, prefix="/auth", tags=["authentication"])
app.include_router(goals_router, prefix="/api", tags=["goals"])
app.include_router(projects_router, prefix="/api", tags=["projects"])
app.include_router(tasks_router, prefix="/api", tags=["tasks"])
app.include_router(life_areas_router, prefix="/api", tags=["life_areas"])
app.include_router(media_attachments_router, prefix="/api", tags=["media"])
app.include_router(user_preferences_router, prefix="/api", tags=["preferences"])
app.include_router(feedback_logs_router, prefix="/api", tags=["feedback"])
app.include_router(story_sessions_router, prefix="/api", tags=["stories"])
app.include_router(ai_router, prefix="/api", tags=["ai"])
app.include_router(conversation_router, tags=["conversation"])
app.include_router(assistant_profiles_router, prefix="/api", tags=["assistant_profiles"])
app.include_router(onboarding_router, prefix="/api", tags=["onboarding"])
app.include_router(avatars_router, tags=["avatars"])
app.include_router(assistant_router, tags=["assistant"])
app.include_router(personal_config_router, prefix="/api/personal-config", tags=["personal-config"])
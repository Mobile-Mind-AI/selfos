import db  # ensure database engine & Base

# Import dependencies to initialize Firebase
import dependencies

# Import event system
import event_consumers

# Import ORM models so they are registered
import models

# Import centralized configuration
from config import settings
from db import Base, engine
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import middleware
from middleware import (
    ErrorHandlingMiddleware,
    RateLimitingMiddleware,
    RequestLoggingMiddleware,
)
from routers.ai import router as ai_router
from routers.analytics import router as analytics_router
from routers.assistant import router as assistant_router
from routers.assistant_profiles import router as assistant_profiles_router
from routers.assistants import router as assistants_router

# Include API routers
from routers.auth import router as auth_router
from routers.avatars import router as avatars_router
from routers.conversation import router as conversation_router
from routers.feedback_logs import router as feedback_logs_router
from routers.goals import router as goals_router
from routers.habits import router as habits_router
from routers.health import router as health_router
from routers.journal import router as journal_router
from routers.life_areas import router as life_areas_router
from routers.media_attachments import router as media_attachments_router
from routers.projects import router as projects_router
from routers.story_sessions import router as story_sessions_router
from routers.tags import router as tags_router
from routers.tasks import router as tasks_router
from routers.user_preferences import router as user_preferences_router

# from routers.entities import router as entities_router  # TODO: Create entities router


app = FastAPI(
    title=settings.app.app_name,
    description=settings.app.app_description,
    version=settings.app.app_version,
    docs_url=settings.app.docs_url,
    redoc_url=settings.app.redoc_url,
    openapi_url=settings.app.openapi_url,
)

# Get rate limiting configuration from settings
rate_limit_config = settings.get_rate_limit_config()

# Add middleware (order matters - first added is executed last)
app.add_middleware(ErrorHandlingMiddleware)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(
    RateLimitingMiddleware,
    requests_per_minute=rate_limit_config["requests_per_minute"],
    requests_per_hour=rate_limit_config["requests_per_hour"],
    burst_limit=rate_limit_config["burst_limit"],
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_credentials=settings.security.cors_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "SelfOS Backend API"}


@app.on_event("startup")
async def on_startup():
    # Note: Database tables are created via Alembic migrations in startup.sh
    # Do not call Base.metadata.create_all() here as it conflicts with migrations

    # Initialize event consumers - disabled for testing
    # await event_consumers.initialize_consumers()
    pass


@app.on_event("shutdown")
async def on_shutdown():
    # Cleanup event consumers - disabled for testing
    # await event_consumers.shutdown_consumers()
    pass


# Register routers
app.include_router(health_router)
app.include_router(auth_router, prefix="/auth", tags=["authentication"])
app.include_router(goals_router, prefix="/api")
app.include_router(projects_router, prefix="/api")
app.include_router(tasks_router, prefix="/api", tags=["tasks"])
app.include_router(habits_router, prefix="/api", tags=["habits"])
app.include_router(journal_router, prefix="/api/journal", tags=["journal"])
app.include_router(tags_router, prefix="/api", tags=["tags"])
app.include_router(analytics_router, prefix="/api", tags=["analytics"])
app.include_router(life_areas_router, prefix="/api", tags=["life_areas"])
app.include_router(media_attachments_router, prefix="/api", tags=["media"])
app.include_router(user_preferences_router, prefix="/api", tags=["preferences"])
app.include_router(feedback_logs_router, prefix="/api", tags=["feedback"])
app.include_router(story_sessions_router, prefix="/api", tags=["stories"])
app.include_router(ai_router, prefix="/api", tags=["ai"])
app.include_router(conversation_router, tags=["conversation"])
app.include_router(
    assistant_profiles_router, prefix="/api", tags=["assistant_profiles"]
)
app.include_router(avatars_router, tags=["avatars"])
app.include_router(assistant_router, tags=["assistant"])
app.include_router(assistants_router, prefix="/api", tags=["assistants"])
# app.include_router(entities_router, prefix="/api", tags=["entities"])  # TODO: Enable when entities router is ready

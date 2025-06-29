from fastapi import FastAPI
import db  # ensure database engine & Base
from db import engine, Base

# Import ORM models so they are registered
import models

# Include API routers
from routers.auth import router as auth_router
from routers.goals import router as goals_router
from routers.tasks import router as tasks_router
from routers.life_areas import router as life_areas_router
from routers.media_attachments import router as media_attachments_router
from routers.user_preferences import router as user_preferences_router
from routers.feedback_logs import router as feedback_logs_router
from routers.story_sessions import router as story_sessions_router
from routers.health import router as health_router

# Import event system
import event_consumers

app = FastAPI()

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
app.include_router(tasks_router, prefix="/api", tags=["tasks"])
app.include_router(life_areas_router, prefix="/api", tags=["life_areas"])
app.include_router(media_attachments_router, prefix="/api", tags=["media"])
app.include_router(user_preferences_router, prefix="/api", tags=["preferences"])
app.include_router(feedback_logs_router, prefix="/api", tags=["feedback"])
app.include_router(story_sessions_router, prefix="/api", tags=["stories"])
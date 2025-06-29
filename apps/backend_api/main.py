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

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "SelfOS Backend API"}

@app.on_event("startup")
def on_startup():
    # Create database tables
    Base.metadata.create_all(bind=engine)

# Register routers
app.include_router(auth_router)
app.include_router(goals_router)
app.include_router(tasks_router)
app.include_router(life_areas_router)
app.include_router(media_attachments_router)
app.include_router(user_preferences_router)
app.include_router(feedback_logs_router)
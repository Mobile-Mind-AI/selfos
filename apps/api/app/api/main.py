from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .settings import get_api_settings
from .errors import install_error_handlers
from .routers import health, life_areas, dreams, goals, projects, habits, tasks, attachments


def create_app() -> FastAPI:
    settings = get_api_settings()
    app = FastAPI(title=settings.app_name, version="0.2")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    install_error_handlers(app)

    app.include_router(health.router)
    app.include_router(life_areas.router, prefix="/v1", tags=["life_areas"])
    app.include_router(dreams.router, prefix="/v1", tags=["dreams"])
    app.include_router(goals.router, prefix="/v1", tags=["goals"])
    app.include_router(projects.router, prefix="/v1", tags=["projects"])
    app.include_router(habits.router, prefix="/v1", tags=["habits"])
    app.include_router(tasks.router, prefix="/v1", tags=["tasks"])
    app.include_router(attachments.router, prefix="/v1", tags=["attachments"])

    return app


app = create_app()


"""
FastAPI Application Entry Point for Autonomous AI Organization Platform.
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.api.routes.agents import router as agents_router
from src.api.routes.communication import router as communication_router
from src.api.routes.decisions import router as decisions_router
from src.api.routes.employees import router as employees_router
from src.api.routes.meetings import router as meetings_router
from src.api.routes.objectives import router as objectives_router
from src.api.routes.runs import router as runs_router
from src.api.routes.tasks import router as tasks_router
from src.application.provider_registry import default_provider_registry
from src.infrastructure.config import settings
from src.infrastructure.logging_config import configure_logging
from src.infrastructure.models.fake_provider import FakeModelProvider
from src.infrastructure.providers.groq_provider import GroqModelProvider


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    configure_logging(level=settings.LOG_LEVEL)
    default_provider_registry.register(GroqModelProvider())
    default_provider_registry.register(FakeModelProvider())
    yield


app = FastAPI(
    title=settings.APP_NAME,
    description=(
        "Autonomous AI Organization Platform - "
        "Agent Runtime, Employee Framework, Manager Orchestration, Task Engine, Communication & Meetings/Decisions "
        "(Phase 1 - Phase 6)"
    ),
    version="0.6.0",
    lifespan=lifespan,
)

# Include Routers
app.include_router(agents_router)
app.include_router(employees_router)
app.include_router(objectives_router)
app.include_router(runs_router)
app.include_router(tasks_router)
app.include_router(communication_router)
app.include_router(meetings_router)
app.include_router(decisions_router)


@app.get("/health", tags=["System"])
async def health_check() -> dict[str, str]:
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "environment": settings.APP_ENV,
    }

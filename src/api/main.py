"""
FastAPI Application Entry Point for Agent Runtime Foundation (Phase 1).
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.api.routes.agents import router as agents_router
from src.api.routes.runs import router as runs_router
from src.application.provider_registry import default_provider_registry
from src.infrastructure.config import settings
from src.infrastructure.logging_config import configure_logging
from src.infrastructure.models.fake_provider import FakeModelProvider
from src.infrastructure.providers.groq_provider import GroqModelProvider


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Configure logging
    configure_logging(level=settings.LOG_LEVEL)

    # Register Model Providers
    default_provider_registry.register(GroqModelProvider())
    default_provider_registry.register(FakeModelProvider())

    yield


app = FastAPI(
    title=settings.APP_NAME,
    description="Agent Runtime Foundation - Autonomous AI Organization Platform (Phase 1)",
    version="0.1.0",
    lifespan=lifespan,
)

# Include Routers
app.include_router(agents_router)
app.include_router(runs_router)


@app.get("/health", tags=["System"])
async def health_check() -> dict[str, str]:
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "environment": settings.APP_ENV,
    }

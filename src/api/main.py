"""
FastAPI Application Entry Point for Autonomous AI Organization Platform.
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.api.routes.agents import router as agents_router
from src.api.routes.artifacts import router as artifacts_router
from src.api.routes.communication import router as communication_router
from src.api.routes.company import router as company_router
from src.api.routes.decisions import router as decisions_router
from src.api.routes.department_requests import router as department_requests_router
from src.api.routes.departments import router as departments_router
from src.api.routes.employees import router as employees_router
from src.api.routes.experiments import router as experiments_router
from src.api.routes.governance import router as governance_router
from src.api.routes.knowledge import router as knowledge_router
from src.api.routes.meetings import router as meetings_router
from src.api.routes.memories import router as memories_router
from src.api.routes.model_routing import router as model_routing_router
from src.api.routes.objectives import router as objectives_router
from src.api.routes.office import router as office_router
from src.api.routes.runs import router as runs_router
from src.api.routes.software_projects import router as software_projects_router
from src.api.routes.tasks import router as tasks_router
from src.api.routes.teams import router as teams_router
from src.api.routes.tools import router as tools_router
from src.api.routes.verifications import router as verifications_router
from src.api.routes.workforce import router as workforce_router
from src.api.routes.workspaces import router as workspaces_router
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
        "Agent Runtime, Employee Framework, Manager Orchestration, Task Engine, Communication, Meetings, Memory/Workspace, Tools, AI Software Company, Verification/Recovery, Governance, Model Routing, Pixel Office, Enterprise Departments, Dynamic Workforce, Autonomous Company OS & Institutional Learning "
        "(Phase 1 - Phase 18)"
    ),
    version="0.18.0",
    lifespan=lifespan,
)

# Include Routers
app.include_router(agents_router)
app.include_router(employees_router)
app.include_router(departments_router)
app.include_router(department_requests_router)
app.include_router(objectives_router)
app.include_router(runs_router)
app.include_router(tasks_router)
app.include_router(communication_router)
app.include_router(meetings_router)
app.include_router(decisions_router)
app.include_router(memories_router)
app.include_router(workspaces_router)
app.include_router(artifacts_router)
app.include_router(tools_router)
app.include_router(software_projects_router)
app.include_router(verifications_router)
app.include_router(governance_router)
app.include_router(model_routing_router)
app.include_router(office_router)
app.include_router(workforce_router)
app.include_router(teams_router)
app.include_router(company_router)
app.include_router(knowledge_router)
app.include_router(experiments_router)


@app.get("/health", tags=["System"])
async def health_check() -> dict[str, str]:
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "environment": settings.APP_ENV,
    }

"""FastAPI Application Entry Point for Autonomous AI Organization Platform."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.middleware.security import (
    CorrelationIdMiddleware,
    ProductionSecurityHeadersMiddleware,
    RequestSizeLimitMiddleware,
)
from src.api.routes.agents import router as agents_router
from src.api.routes.artifacts import router as artifacts_router
from src.api.routes.business import router as business_router
from src.api.routes.communication import router as communication_router
from src.api.routes.company import router as company_router
from src.api.routes.decisions import router as decisions_router
from src.api.routes.department_requests import router as department_requests_router
from src.api.routes.departments import router as departments_router
from src.api.routes.employees import router as employees_router
from src.api.routes.experiments import router as experiments_router
from src.api.routes.governance import router as governance_router
from src.api.routes.gtm import router as gtm_router
from src.api.routes.health import router as health_router
from src.api.routes.innovation import router as innovation_router
from src.api.routes.knowledge import router as knowledge_router
from src.api.routes.meetings import router as meetings_router
from src.api.routes.memories import router as memories_router
from src.api.routes.model_routing import router as model_routing_router
from src.api.routes.objectives import router as objectives_router
from src.api.routes.office import router as office_router
from src.api.routes.research import router as research_router
from src.api.routes.runs import router as runs_router
from src.api.routes.simulation import router as simulation_router
from src.api.routes.software_projects import router as software_projects_router
from src.api.routes.swarms import router as swarms_router
from src.api.routes.tasks import router as tasks_router
from src.api.routes.teams import router as teams_router
from src.api.routes.tools import router as tools_router
from src.api.routes.verifications import router as verifications_router
from src.api.routes.company_intelligence import router as company_intelligence_router
from src.api.routes.venture import router as venture_router
from src.api.routes.enterprise import router as enterprise_router
from src.api.routes.workforce import router as workforce_router
from src.api.routes.resilience import router as resilience_router
from src.api.routes.platform import router as platform_router
from src.api.middleware.resilience import ResilienceSecurityMiddleware


from src.api.routes.workspaces import router as workspaces_router
from src.application.provider_registry import default_provider_registry
from src.infrastructure.config import settings
from src.infrastructure.env_validation import validate_production_env
from src.infrastructure.logging_config import configure_logging
from src.infrastructure.models.fake_provider import FakeModelProvider
from src.infrastructure.observability import configure_opentelemetry
from src.infrastructure.providers.groq_provider import GroqModelProvider
from src.infrastructure.redis_client import close_redis


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    configure_logging(level=settings.LOG_LEVEL)
    validate_production_env(settings)
    configure_opentelemetry()
    default_provider_registry.register(GroqModelProvider())
    default_provider_registry.register(FakeModelProvider())
    yield
    await close_redis()


app = FastAPI(
    title=settings.APP_NAME,
    description=(
        "Autonomous AI Organization Platform 1.0 - "
        "Agent Runtime, Employee Framework, Manager Orchestration, Task Engine, Communication, Meetings, Memory/Workspace, Tools, AI Software Company, Verification/Recovery, Governance, Model Routing, Pixel Office, Enterprise Departments, Dynamic Workforce, Autonomous Company OS, Institutional Learning, Research Engine, Production Infrastructure, Swarms, Enterprise OS, Production Hardening & Unified Control Plane "
        "(Phases 1 - 31)"
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# Register Production Security & Correlation Middlewares
app.add_middleware(CorrelationIdMiddleware)
app.add_middleware(ProductionSecurityHeadersMiddleware)
app.add_middleware(RequestSizeLimitMiddleware)
app.add_middleware(ResilienceSecurityMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from src.api.routes.simulation import router as simulation_router
from src.api.routes.company_intelligence import router as company_intelligence_router
from src.api.routes.learning import router as learning_router

# Include Routers
app.include_router(health_router)
app.include_router(agents_router)
app.include_router(employees_router)
app.include_router(departments_router)
app.include_router(teams_router)
app.include_router(objectives_router)
app.include_router(tasks_router)
app.include_router(runs_router)
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
app.include_router(department_requests_router)
app.include_router(workforce_router)
app.include_router(company_router)
app.include_router(knowledge_router)
app.include_router(experiments_router)
app.include_router(research_router, prefix="/api/v1")
app.include_router(innovation_router, prefix="/api/v1")
app.include_router(swarms_router)
app.include_router(business_router)
app.include_router(gtm_router)
app.include_router(simulation_router)
app.include_router(company_intelligence_router)
app.include_router(learning_router)

app.include_router(venture_router)
app.include_router(enterprise_router)
app.include_router(resilience_router)
app.include_router(platform_router)








"""Production Health and Readiness Endpoints.

Provides /health/live and /health/ready endpoints for orchestrators, load balancers, and monitoring.
"""

from datetime import UTC, datetime
from typing import Any
from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.config import settings
from src.infrastructure.database import check_database_health, get_db_session
from src.infrastructure.observability import metrics_collector
from src.infrastructure.redis_client import check_redis_health
from src.infrastructure.repositories.outbox_repository import SQLAlchemyOutboxRepository

router = APIRouter(prefix="/health", tags=["Health & Readiness"])


@router.get("/live", status_code=status.HTTP_200_OK)
async def liveness_check() -> dict[str, Any]:
    """Liveness probe: verifies process is alive."""
    return {
        "status": "alive",
        "app_name": settings.APP_NAME,
        "environment": settings.APP_ENV,
        "timestamp": datetime.now(UTC).isoformat(),
    }


@router.get("/ready")
async def readiness_check(
    response: Response,
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    """Readiness probe: checks Database, Redis, Storage, and Outbox health."""
    db_ok, db_msg = await check_database_health()
    redis_ok, redis_msg = await check_redis_health()

    # Outbox backlog check
    outbox_backlog = 0
    try:
        repo = SQLAlchemyOutboxRepository(db)
        pending = await repo.get_pending_messages(limit=100)
        outbox_backlog = len(pending)
        metrics_collector.outbox_backlog_depth = outbox_backlog
    except Exception:
        pass

    dependencies = {
        "database": {"status": "healthy" if db_ok else "unhealthy", "detail": db_msg},
        "redis": {"status": "healthy" if redis_ok else "unhealthy", "detail": redis_msg},
        "outbox_backlog_depth": outbox_backlog,
    }

    # System is ready if database is healthy (Redis is graceful optional in non-production)
    is_ready = db_ok

    if not is_ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return {
        "status": "ready" if is_ready else "degraded",
        "environment": settings.APP_ENV,
        "dependencies": dependencies,
        "metrics_summary": metrics_collector.get_summary(),
        "timestamp": datetime.now(UTC).isoformat(),
    }

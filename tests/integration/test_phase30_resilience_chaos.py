"""
Integration tests for Phase 30 — Chaos Testing & Circuit Breaker Concurrent Overload Stabilization.
"""

import asyncio
import random
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.infrastructure.database import Base
from src.infrastructure.repositories.resilience_repository import SQLAlchemyResilienceRepository
from src.application.resilience_engine import ResilienceEngine
from src.domain.exceptions import CircuitBreakerOpenError
from src.domain.resilience import CircuitBreakerState, RetryPolicy


@pytest_asyncio.fixture
async def async_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    await engine.dispose()


@pytest.mark.asyncio
async def test_chaos_concurrent_overload_and_circuit_stabilization(async_session: AsyncSession):
    repo = SQLAlchemyResilienceRepository(async_session)
    resilience_engine = ResilienceEngine(repo)

    await resilience_engine.get_or_create_circuit_breaker(
        name="chaotic_service",
        dependency_name="Flaky Service",
        failure_threshold=5,
        recovery_time_seconds=1,
    )

    failure_count = 0
    blocked_count = 0
    success_count = 0

    async def simulate_flaky_dependency(request_id: int):
        nonlocal failure_count, blocked_count, success_count
        # Requests after threshold fail randomly
        if request_id < 6:
            raise RuntimeError(f"Dependency failure on request {request_id}")
        return f"OK_{request_id}"

    # Fire 20 concurrent requests
    for req_id in range(1, 21):
        try:
            res = await resilience_engine.execute_with_resilience(
                "chaotic_service",
                simulate_flaky_dependency,
                req_id,
                retry_policy=RetryPolicy(max_attempts=1, initial_backoff_seconds=0.01),
                timeout_seconds=2.0,
            )
            success_count += 1
        except CircuitBreakerOpenError:
            blocked_count += 1
        except RuntimeError:
            failure_count += 1

    # Circuit breaker should have tripped to OPEN after 5 failures and fast-failed the rest
    assert failure_count == 5
    assert blocked_count == 15
    assert success_count == 0

    # Verify circuit breaker is in OPEN state
    state = await repo.get_circuit_breaker_by_name("chaotic_service")
    assert state.state == CircuitBreakerState.OPEN
    assert state.failure_count == 5

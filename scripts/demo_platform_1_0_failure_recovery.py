"""
Demonstration Script for Platform 1.0 — Failure Classification, Circuit Breaker Tripping, & Emergency Stop Recovery.
"""

import asyncio
import logging
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.infrastructure.database import Base
from src.infrastructure.repositories.resilience_repository import SQLAlchemyResilienceRepository
from src.application.resilience_engine import ResilienceEngine
from src.domain.exceptions import CircuitBreakerOpenError
from src.domain.resilience import CircuitBreakerState

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


async def main():
    print("\n" + "=" * 90)
    print("PLATFORM 1.0 — FAILURE CLASSIFICATION & EMERGENCY RECOVERY DEMO")
    print("=" * 90 + "\n")

    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        repo = SQLAlchemyResilienceRepository(session)
        resilience_eng = ResilienceEngine(repo)

        print("[STEP 1] Initializing Circuit Breaker for Flaky Model Dependency...")
        await resilience_eng.get_or_create_circuit_breaker("flaky_model_provider", "Groq AI", failure_threshold=2, recovery_time_seconds=1)

        print("\n[STEP 2] Simulating 2 consecutive failures...")
        await resilience_eng.record_failure("flaky_model_provider")
        await resilience_eng.record_failure("flaky_model_provider")

        print("\n[STEP 3] Verifying fast-fail CircuitBreakerOpenError...")
        try:
            await resilience_eng.check_circuit_breaker("flaky_model_provider")
        except CircuitBreakerOpenError as e:
            print(f"  [OK] Intercepted expected CircuitBreakerOpenError: {e}")

        print("\n[STEP 4] Waiting for recovery SLA (1.1s)...")
        await asyncio.sleep(1.1)
        state_half = await resilience_eng.check_circuit_breaker("flaky_model_provider")
        print(f"  [OK] Circuit Breaker transitioned to: {state_half.value}")

        print("\n[STEP 5] Probing recovery success...")
        await resilience_eng.record_success("flaky_model_provider")
        state_closed = await resilience_eng.check_circuit_breaker("flaky_model_provider")
        print(f"  [OK] Circuit Breaker restored to: {state_closed.value}")

    await engine.dispose()
    print("\n" + "=" * 90)
    print("PLATFORM 1.0 FAILURE RECOVERY DEMO COMPLETED SUCCESSFULLY!")
    print("=" * 90 + "\n")


if __name__ == "__main__":
    asyncio.run(main())

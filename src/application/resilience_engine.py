"""
Application engine for Circuit Breakers, Retry Policies, Timeouts, and System Degradation (Phase 30).
"""

import asyncio
from datetime import datetime, timezone, UTC
import logging
import random
import time
from typing import Any, Callable, Dict, List, Optional, TypeVar

from src.domain.exceptions import CircuitBreakerOpenError, RateLimitExceededError, ResilienceTimeoutError
from src.domain.repository import ResilienceRepositoryInterface
from src.domain.resilience import (
    CircuitBreaker,
    CircuitBreakerState,
    DegradationState,
    DependencyHealthSnapshot,
    ResiliencePolicy,
    RetryPolicy,
    TimeoutPolicy,
)

logger = logging.getLogger(__name__)

T = TypeVar("T")


class ResilienceEngine:
    """Engine executing resilience policies, circuit breaking, backoff retries, and degradation matrix."""

    def __init__(self, repository: ResilienceRepositoryInterface) -> None:
        self.repository = repository

    async def get_or_create_circuit_breaker(self, name: str, dependency_name: str, failure_threshold: int = 5, recovery_time_seconds: int = 60) -> CircuitBreaker:
        cb = await self.repository.get_circuit_breaker_by_name(name)
        if not cb:
            cb = CircuitBreaker(
                name=name,
                dependency_name=dependency_name,
                failure_threshold=failure_threshold,
                recovery_time_seconds=recovery_time_seconds,
            )
            cb = await self.repository.save_circuit_breaker(cb)
        return cb

    async def check_circuit_breaker(self, name: str) -> CircuitBreakerState:
        cb = await self.repository.get_circuit_breaker_by_name(name)
        if not cb:
            return CircuitBreakerState.CLOSED

        if cb.state == CircuitBreakerState.OPEN:
            last_change = cb.last_state_change_at
            if last_change.tzinfo is None:
                last_change = last_change.replace(tzinfo=UTC)

            elapsed = (datetime.now(UTC) - last_change).total_seconds()
            if elapsed >= cb.recovery_time_seconds:
                cb.state = CircuitBreakerState.HALF_OPEN
                cb.last_state_change_at = datetime.now(UTC)
                await self.repository.save_circuit_breaker(cb)
                logger.info(f"Circuit breaker {name} transitioned from OPEN to HALF_OPEN after {elapsed:.1f}s")
                return CircuitBreakerState.HALF_OPEN
            else:
                raise CircuitBreakerOpenError(dependency_name=name, recovery_time_seconds=int(cb.recovery_time_seconds - elapsed))

        return cb.state

    async def record_success(self, name: str) -> CircuitBreaker:
        cb = await self.repository.get_circuit_breaker_by_name(name)
        if not cb:
            return CircuitBreaker(name=name)

        cb.success_count += 1
        if cb.state == CircuitBreakerState.HALF_OPEN:
            cb.state = CircuitBreakerState.CLOSED
            cb.failure_count = 0
            cb.last_state_change_at = datetime.now(UTC)
            logger.info(f"Circuit breaker {name} recovered to CLOSED state.")
        cb = await self.repository.save_circuit_breaker(cb)
        return cb

    async def record_failure(self, name: str) -> CircuitBreaker:
        cb = await self.repository.get_circuit_breaker_by_name(name)
        if not cb:
            return CircuitBreaker(name=name)

        cb.failure_count += 1
        cb.last_failure_at = datetime.now(UTC)
        if cb.failure_count >= cb.failure_threshold or cb.state == CircuitBreakerState.HALF_OPEN:
            cb.state = CircuitBreakerState.OPEN
            cb.last_state_change_at = datetime.now(UTC)
            logger.warning(f"Circuit breaker {name} tripped to OPEN state after {cb.failure_count} failures.")

        cb = await self.repository.save_circuit_breaker(cb)
        return cb

    def calculate_backoff_delay(self, attempt: int, initial_backoff: float = 1.0, max_backoff: float = 30.0, multiplier: float = 2.0, jitter: bool = True) -> float:
        delay = min(max_backoff, initial_backoff * (multiplier ** (attempt - 1)))
        if jitter:
            delay = random.uniform(0.5 * delay, 1.5 * delay)
        return round(delay, 3)

    async def execute_with_resilience(
        self,
        target_name: str,
        func: Callable[..., Any],
        *args: Any,
        retry_policy: Optional[RetryPolicy] = None,
        timeout_seconds: Optional[float] = None,
        fallback_func: Optional[Callable[..., Any]] = None,
        **kwargs: Any,
    ) -> Any:
        policy = retry_policy or RetryPolicy()
        timeout = timeout_seconds or 30.0

        await self.check_circuit_breaker(target_name)

        attempt = 1
        last_exception: Exception | None = None

        while attempt <= policy.max_attempts:
            try:
                if timeout > 0:
                    result = await asyncio.wait_for(func(*args, **kwargs), timeout=timeout)
                else:
                    result = await func(*args, **kwargs)

                await self.record_success(target_name)
                return result
            except asyncio.TimeoutError:
                last_exception = ResilienceTimeoutError(target_name=target_name, timeout_seconds=timeout)
                await self.record_failure(target_name)
                logger.warning(f"Timeout on target '{target_name}' (Attempt {attempt}/{policy.max_attempts})")
            except CircuitBreakerOpenError:
                raise
            except Exception as e:
                last_exception = e
                await self.record_failure(target_name)
                logger.warning(f"Execution failed on target '{target_name}' (Attempt {attempt}/{policy.max_attempts}): {e}")

            if attempt < policy.max_attempts:
                delay = self.calculate_backoff_delay(
                    attempt=attempt,
                    initial_backoff=policy.initial_backoff_seconds,
                    max_backoff=policy.max_backoff_seconds,
                    multiplier=policy.backoff_multiplier,
                    jitter=policy.jitter,
                )
                await asyncio.sleep(delay)

            attempt += 1

        if fallback_func is not None:
            logger.info(f"Invoking fallback function for target '{target_name}'")
            return await fallback_func(*args, **kwargs)

        raise last_exception or RuntimeError(f"Resilience execution failed for target '{target_name}'")

    async def evaluate_system_degradation(self) -> DegradationState:
        snapshots = await self.repository.list_latest_dependency_snapshots()
        if not snapshots:
            return DegradationState.NORMAL

        total = len(snapshots)
        unhealthy_count = sum(1 for s in snapshots if not s.is_available or s.error_rate_pct > 0.5)

        if unhealthy_count == 0:
            return DegradationState.NORMAL
        elif unhealthy_count < total:
            return DegradationState.DEGRADED
        else:
            return DegradationState.UNAVAILABLE

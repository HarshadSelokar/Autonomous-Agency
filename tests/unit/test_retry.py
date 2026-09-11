"""
Unit tests for RetryPolicy.
"""

import pytest

from src.application.retry import RetryPolicy
from src.domain.exceptions import (
    AuthenticationError,
    RateLimitError,
    TimeoutError,
)


@pytest.mark.asyncio
async def test_retry_policy_succeeds_without_retries() -> None:
    policy = RetryPolicy(max_retries=3, backoff_factor=0.01)
    call_count = 0

    async def successful_func() -> str:
        nonlocal call_count
        call_count += 1
        return "success"

    result = await policy.execute(successful_func)
    assert result == "success"
    assert call_count == 1


@pytest.mark.asyncio
async def test_retry_policy_retries_transient_failures_and_recovers() -> None:
    policy = RetryPolicy(max_retries=3, backoff_factor=0.01)
    call_count = 0

    async def transient_failing_func() -> str:
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise TimeoutError(f"Transient failure {call_count}")
        return "recovered"

    result = await policy.execute(transient_failing_func)
    assert result == "recovered"
    assert call_count == 3


@pytest.mark.asyncio
async def test_retry_policy_exhausts_retries() -> None:
    policy = RetryPolicy(max_retries=2, backoff_factor=0.01)
    call_count = 0

    async def always_failing_func() -> str:
        nonlocal call_count
        call_count += 1
        raise RateLimitError("Rate limit exceeded")

    with pytest.raises(RateLimitError):
        await policy.execute(always_failing_func)

    assert call_count == 3  # Initial attempt + 2 retries = 3 total attempts


@pytest.mark.asyncio
async def test_retry_policy_does_not_retry_non_retryable_errors() -> None:
    policy = RetryPolicy(max_retries=3, backoff_factor=0.01)
    call_count = 0

    async def non_retryable_func() -> str:
        nonlocal call_count
        call_count += 1
        raise AuthenticationError("Invalid API key")

    with pytest.raises(AuthenticationError):
        await policy.execute(non_retryable_func)

    assert call_count == 1  # Fails immediately without retrying

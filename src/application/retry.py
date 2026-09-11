"""
Bounded Exponential Backoff Retry Policy Subsystem.
Only retries transient retryable errors (Timeout, RateLimit, ProviderUnavailable).
Rejects non-retryable errors (Authentication, Validation, Configuration, Cancellation).
"""

import asyncio
import logging
from collections.abc import Awaitable, Callable
from typing import TypeVar

from src.domain.exceptions import (
    AuthenticationError,
    CancellationError,
    ConfigurationError,
    InvalidResponseError,
    ProviderUnavailableError,
    RateLimitError,
    StructuredOutputValidationError,
    TimeoutError,
)
from src.infrastructure.config import settings

logger = logging.getLogger(__name__)

T = TypeVar("T")

RETRYABLE_EXCEPTIONS: tuple[type[Exception], ...] = (
    TimeoutError,
    RateLimitError,
    ProviderUnavailableError,
)

NON_RETRYABLE_EXCEPTIONS: tuple[type[Exception], ...] = (
    AuthenticationError,
    CancellationError,
    ConfigurationError,
    StructuredOutputValidationError,
    InvalidResponseError,
)


class RetryPolicy:
    def __init__(
        self,
        max_retries: int | None = None,
        backoff_factor: float | None = None,
    ) -> None:
        self.max_retries = max_retries if max_retries is not None else settings.MAX_RETRIES
        self.backoff_factor = (
            backoff_factor if backoff_factor is not None else settings.RETRY_BACKOFF_FACTOR
        )

    def is_retryable(self, exception: Exception) -> bool:
        """Check if an exception is classified as transient and retryable."""
        if isinstance(exception, NON_RETRYABLE_EXCEPTIONS):
            return False
        return isinstance(exception, RETRYABLE_EXCEPTIONS)

    async def execute(self, func: Callable[[], Awaitable[T]]) -> T:
        """
        Execute an async callable with bounded exponential backoff retries.
        """
        attempt = 0
        while True:
            try:
                return await func()
            except Exception as exc:
                attempt += 1
                if not self.is_retryable(exc) or attempt > self.max_retries:
                    logger.warning(
                        f"Retry exhausted or non-retryable exception caught: {exc} "
                        f"(Attempt {attempt}/{self.max_retries})"
                    )
                    raise exc

                delay = self.backoff_factor ** (attempt - 1)
                logger.info(
                    f"Retryable error caught ({exc}). Retrying in {delay:.2f}s "
                    f"(Attempt {attempt}/{self.max_retries})..."
                )
                await asyncio.sleep(delay)

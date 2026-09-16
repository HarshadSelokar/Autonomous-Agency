"""Redis Connection Pool & Resilience Client Manager."""

import logging
from typing import Any

logger = logging.getLogger(__name__)

try:
    import redis.asyncio as aioredis
    from redis.asyncio.client import Redis
    from redis.asyncio.connection import ConnectionPool
    HAS_REDIS = True
except ImportError:
    HAS_REDIS = False
    aioredis = None  # type: ignore
    Redis = None  # type: ignore
    ConnectionPool = None  # type: ignore

from src.infrastructure.config import settings


class RedisClientManager:
    """Manages async Redis connection pool, health pings, and reconnect resilience."""

    def __init__(self, url: str | None = None) -> None:
        self.url = url or settings.REDIS_URL
        self._pool: Any | None = None
        self._client: Any | None = None

    def get_pool(self) -> Any:
        if not HAS_REDIS:
            raise RuntimeError("The 'redis' package is not installed.")
        if self._pool is None:
            self._pool = ConnectionPool.from_url(
                self.url,
                max_connections=settings.REDIS_MAX_CONNECTIONS,
                socket_timeout=settings.REDIS_SOCKET_TIMEOUT,
                retry_on_timeout=settings.REDIS_RETRY_ON_TIMEOUT,
                decode_responses=True,
            )
        return self._pool

    def get_client(self) -> Any:
        if not HAS_REDIS:
            raise RuntimeError("The 'redis' package is not installed.")
        if self._client is None:
            pool = self.get_pool()
            self._client = Redis(connection_pool=pool)
        return self._client

    async def check_health(self) -> tuple[bool, str]:
        """Ping Redis server to check connection health."""
        if not HAS_REDIS:
            return False, "Redis package is not installed"
        try:
            client = self.get_client()
            pong = await client.ping()
            if pong:
                return True, "Redis connection healthy"
            return False, "Redis ping returned unexpected response"
        except Exception as err:
            logger.warning(f"Redis health check failed: {err}")
            return False, f"Redis unavailable: {str(err)}"

    async def close(self) -> None:
        """Safely close Redis connection pool on application shutdown."""
        if self._client:
            logger.info("Closing Redis client...")
            try:
                await self._client.close()
            except Exception as e:
                logger.warning(f"Error closing Redis client: {e}")
            self._client = None
        if self._pool:
            logger.info("Disconnecting Redis connection pool...")
            try:
                await self._pool.disconnect()
            except Exception as e:
                logger.warning(f"Error disconnecting Redis pool: {e}")
            self._pool = None


# Singleton instance
redis_manager = RedisClientManager()


async def get_redis() -> Any:
    return redis_manager.get_client()


async def check_redis_health() -> tuple[bool, str]:
    return await redis_manager.check_health()


async def close_redis() -> None:
    await redis_manager.close()

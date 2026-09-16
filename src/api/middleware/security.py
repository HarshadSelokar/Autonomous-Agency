"""FastAPI Production Security & Correlation Middlewares."""

import uuid
from collections.abc import Awaitable, Callable
from fastapi import HTTPException, Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware

from src.infrastructure.config import settings
from src.infrastructure.observability import metrics_collector


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """Propagates and injects X-Correlation-ID and X-Request-ID headers across HTTP requests."""

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        req_id = request.headers.get("X-Request-ID") or f"req-{uuid.uuid4().hex[:12]}"
        corr_id = request.headers.get("X-Correlation-ID") or f"corr-{uuid.uuid4().hex[:12]}"

        # Attach to request state for access in endpoints/services
        request.state.request_id = req_id
        request.state.correlation_id = corr_id

        response = await call_next(request)

        response.headers["X-Request-ID"] = req_id
        response.headers["X-Correlation-ID"] = corr_id

        # Record API metrics
        metrics_collector.record_api_request(request.url.path, response.status_code)
        return response


class ProductionSecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Sets standard production security headers on HTTP responses."""

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        response = await call_next(request)

        if settings.APP_ENV == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
            response.headers["X-XSS-Protection"] = "1; mode=block"

        return response


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """Rejects incoming HTTP requests whose Content-Length exceeds MAX_CONTENT_LENGTH_BYTES."""

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        content_length = request.headers.get("Content-Length")
        if content_length:
            try:
                length_int = int(content_length)
                if length_int > settings.MAX_CONTENT_LENGTH_BYTES:
                    return Response(
                        content=f'{{"detail": "Request payload size {length_int} bytes exceeds maximum allowed limit of {settings.MAX_CONTENT_LENGTH_BYTES} bytes."}}',
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        media_type="application/json",
                    )
            except ValueError:
                pass

        return await call_next(request)

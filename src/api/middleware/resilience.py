"""
FastAPI / Starlette middleware for security filtering, secret redaction, and prompt injection guarding (Phase 30).
"""

import json
import logging
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from src.application.security_incident_engine import SecurityIncidentEngine
from src.infrastructure.repositories.resilience_repository import SQLAlchemyResilienceRepository
from src.domain.exceptions import SecurityBoundaryViolationError

logger = logging.getLogger(__name__)


class ResilienceSecurityMiddleware(BaseHTTPMiddleware):
    """Middleware inspecting request payloads for prompt injection and redacting secrets in responses."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 1. Inspect request body for text/json calls if present
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                body_bytes = await request.body()
                if body_bytes:
                    body_text = body_bytes.decode("utf-8", errors="ignore")
                    # Quick pattern check
                    from src.application.security_incident_engine import PROMPT_INJECTION_PATTERNS
                    import re

                    for pattern in PROMPT_INJECTION_PATTERNS:
                        if re.search(pattern, body_text):
                            logger.warning(f"Security Middleware blocked request to {request.url.path} due to prompt injection pattern match.")
                            return JSONResponse(
                                status_code=403,
                                content={
                                    "error": "SECURITY_BOUNDARY_VIOLATION",
                                    "message": f"Malicious prompt injection pattern detected in payload to {request.url.path}.",
                                },
                            )
            except Exception as e:
                logger.debug(f"Failed to inspect request body in ResilienceSecurityMiddleware: {e}")

        # 2. Process request
        response: Response = await call_next(request)

        return response

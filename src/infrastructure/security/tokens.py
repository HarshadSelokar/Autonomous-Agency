"""Signed access tokens (JWT, HS256)."""

import logging
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt

from src.infrastructure.config import settings

logger = logging.getLogger(__name__)

_ALGORITHM = "HS256"
_ephemeral_secret: str | None = None


class InvalidTokenError(Exception):
    """Raised when an access token is missing claims, expired, or wrongly signed."""


def _secret() -> str:
    if settings.AUTH_SECRET_KEY:
        return settings.AUTH_SECRET_KEY
    global _ephemeral_secret
    if _ephemeral_secret is None:
        _ephemeral_secret = secrets.token_urlsafe(48)
        logger.warning(
            "AUTH_SECRET_KEY is not set; using a random per-process secret. "
            "Access tokens will stop working when this process restarts."
        )
    return _ephemeral_secret


def create_access_token(
    user_id: str,
    tenant_id: str | None,
    is_platform_admin: bool = False,
    email: str | None = None,
    ttl_minutes: int | None = None,
) -> str:
    now = datetime.now(UTC)
    claims: dict[str, Any] = {
        "sub": user_id,
        "tid": tenant_id,
        "adm": is_platform_admin,
        "email": email,
        "iat": now,
        "exp": now + timedelta(minutes=ttl_minutes or settings.AUTH_TOKEN_TTL_MINUTES),
    }
    return jwt.encode(claims, _secret(), algorithm=_ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    try:
        claims = jwt.decode(
            token, _secret(), algorithms=[_ALGORITHM], options={"require": ["sub", "exp"]}
        )
    except jwt.PyJWTError as exc:
        raise InvalidTokenError(str(exc)) from exc
    return claims

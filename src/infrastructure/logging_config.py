"""Structured JSON Logging Module for Autonomous AI Organization Platform.

Ensures trace context (request_id, correlation_id, agent_id, run_id, task_id)
is formatted into JSON lines while redacting sensitive tokens and credentials.
"""

import json
import logging
from datetime import UTC, datetime
from typing import Any

SENSITIVE_KEYS = {"password", "api_key", "secret", "token", "authorization", "groq_api_key", "s3_secret_access_key"}


class StructuredJsonFormatter(logging.Formatter):
    """Formats Python log records into structured JSON lines with secret redaction."""

    def _redact(self, data: Any) -> Any:
        if isinstance(data, dict):
            return {
                k: ("[REDACTED]" if k.lower() in SENSITIVE_KEYS else self._redact(v))
                for k, v in data.items()
            }
        if isinstance(data, list):
            return [self._redact(i) for i in data]
        return data

    def format(self, record: logging.LogRecord) -> str:
        log_data: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "event": record.getMessage(),
        }

        # Context correlation fields
        for key in (
            "request_id",
            "correlation_id",
            "trace_id",
            "worker_id",
            "agent_id",
            "run_id",
            "task_id",
            "provider",
            "model",
            "environment",
        ):
            if hasattr(record, key):
                log_data[key] = getattr(record, key)

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(self._redact(log_data))


def configure_logging(level: str = "INFO") -> None:
    """Configure system-wide structured JSON logging."""
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    handler = logging.StreamHandler()
    handler.setFormatter(StructuredJsonFormatter())
    root_logger.addHandler(handler)

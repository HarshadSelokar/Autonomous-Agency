"""
SecretsBroker Application Layer for Phase 8.
Manages credential isolation and execution-time secret injection.
CRITICAL INVARIANT: Raw secrets MUST NEVER enter model context.
All tool results, logs, and evidence are automatically redacted.
"""

from typing import Any


class SecretsBroker:
    def __init__(self) -> None:
        self._secrets: dict[str, str] = {}

    def register_secret(self, secret_ref: str, secret_value: str) -> None:
        """Register a scoped credential reference and its raw value."""
        if not secret_ref or not secret_ref.strip():
            raise ValueError("Secret reference cannot be empty.")
        if not secret_value or not secret_value.strip():
            raise ValueError("Secret value cannot be empty.")
        self._secrets[secret_ref] = secret_value

    def get_secret(self, secret_ref: str) -> str | None:
        """Retrieve raw secret at execution time for authorized tool adapters."""
        return self._secrets.get(secret_ref)

    def redact(self, value: Any) -> Any:
        """
        Recursively redact raw secret values from text, dictionaries, or lists
        before sending to LLM context, logs, tool results, or evidence traces.
        """
        if not self._secrets:
            return value

        if isinstance(value, str):
            redacted_str = value
            for secret_val in self._secrets.values():
                if secret_val and secret_val in redacted_str:
                    redacted_str = redacted_str.replace(secret_val, "[REDACTED_SECRET]")
            return redacted_str

        elif isinstance(value, dict):
            return {k: self.redact(v) for k, v in value.items()}

        elif isinstance(value, list):
            return [self.redact(item) for item in value]

        return value

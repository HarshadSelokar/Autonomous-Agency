"""
HTTP Tool Executor Adapter for Phase 8.
Handles HTTP_REQUEST with SSRF defenses (blocking loopback, private subnets, cloud metadata IPs)
and SecretsBroker execution-time credential injection and redaction.
"""

import time
from typing import Any
import httpx

from src.application.secrets_broker import SecretsBroker
from src.domain.tool import (
    ToolCapability,
    ToolDefinition,
    ToolExecutionStatus,
    ToolRequest,
    ToolResult,
)
from src.infrastructure.tools.executors.base import ToolExecutorInterface
from src.infrastructure.tools.sandboxing import SandboxExecutionBoundary


class HTTPToolExecutor(ToolExecutorInterface):
    def __init__(self, sandbox: SandboxExecutionBoundary | None = None) -> None:
        self.sandbox = sandbox or SandboxExecutionBoundary()

    async def execute(
        self,
        request: ToolRequest,
        tool: ToolDefinition,
        secrets_broker: SecretsBroker | None = None,
    ) -> ToolResult:
        start_time = time.time()
        args = request.arguments

        try:
            url = args.get("url")
            method = (args.get("method") or "GET").upper()
            headers = args.get("headers") or {}
            body = args.get("body")
            secret_ref = args.get("secret_ref")

            if not url:
                raise ValueError("Argument 'url' is required for HTTP_REQUEST capability.")

            # 1. SSRF Defense Validation
            self.sandbox.validate_http_url(url)

            # 2. Execution-Time Credential Injection from SecretsBroker
            if secret_ref and secrets_broker:
                secret_val = secrets_broker.get_secret(secret_ref)
                if secret_val:
                    headers["Authorization"] = f"Bearer {secret_val}"

            # 3. Controlled Async HTTP Request Execution
            timeout_sec = min(tool.timeout_seconds, 15.0)
            async with httpx.AsyncClient(timeout=timeout_sec, follow_redirects=False) as client:
                resp = await client.request(method=method, url=url, headers=headers, content=body)

            output_text = resp.text
            truncated_output = self.sandbox.truncate_output(output_text)

            raw_result_data = {
                "url": url,
                "status_code": resp.status_code,
                "headers": dict(resp.headers),
                "body": truncated_output,
            }

            # 4. Redact Any Secret Values before returning
            if secrets_broker:
                raw_result_data = secrets_broker.redact(raw_result_data)

            elapsed = (time.time() - start_time) * 1000
            return ToolResult(
                execution_id=request.id,
                status=ToolExecutionStatus.SUCCEEDED,
                output=raw_result_data,
                execution_time_ms=elapsed,
            )

        except Exception as exc:
            elapsed = (time.time() - start_time) * 1000
            err_msg = str(exc)
            if secrets_broker:
                err_msg = secrets_broker.redact(err_msg)

            return ToolResult(
                execution_id=request.id,
                status=ToolExecutionStatus.FAILED,
                error_message=err_msg,
                execution_time_ms=elapsed,
            )

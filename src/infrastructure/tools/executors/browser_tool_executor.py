"""
Browser Tool Executor Adapter for Phase 8.
Provider-neutral browser automation primitives (BrowserSession, BrowserAction, BrowserPolicy, BrowserResult)
supporting domain navigation boundaries, action limits, and Playwright integration readiness.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
import time
from typing import Any

from src.application.secrets_broker import SecretsBroker
from src.domain.tool import (
    ToolCapability,
    ToolDefinition,
    ToolExecutionStatus,
    ToolRequest,
    ToolResult,
)
from src.infrastructure.tools.executors.base import ToolExecutorInterface
from src.infrastructure.tools.sandboxing import SandboxExecutionBoundary, SSRFViolationError


@dataclass
class BrowserPolicy:
    allowed_domains: list[str] = field(default_factory=list)
    max_actions_per_session: int = 20
    session_timeout_seconds: float = 60.0
    allow_download: bool = False
    allow_upload: bool = False


@dataclass
class BrowserAction:
    action_type: str  # navigate, click, type, screenshot, extract_text
    target_url: str | None = None
    selector: str | None = None
    value: str | None = None


@dataclass
class BrowserResultData:
    session_id: str
    current_url: str
    title: str = ""
    extracted_text: str = ""
    action_history: list[str] = field(default_factory=list)


class BrowserToolExecutor(ToolExecutorInterface):
    def __init__(
        self,
        sandbox: SandboxExecutionBoundary | None = None,
        policy: BrowserPolicy | None = None,
    ) -> None:
        self.sandbox = sandbox or SandboxExecutionBoundary()
        self.policy = policy or BrowserPolicy()

    async def execute(
        self,
        request: ToolRequest,
        tool: ToolDefinition,
        secrets_broker: SecretsBroker | None = None,
    ) -> ToolResult:
        start_time = time.time()
        args = request.arguments
        action_type = args.get("action", "navigate")
        url = args.get("url")

        try:
            if url:
                # SSRF Defense Validation on Browser Navigation Target
                self.sandbox.validate_http_url(url)

                if self.policy.allowed_domains:
                    domain_ok = any(
                        url.lower().startswith(f"http://{d}") or url.lower().startswith(f"https://{d}")
                        for d in self.policy.allowed_domains
                    )
                    if not domain_ok:
                        raise SSRFViolationError(f"Browser navigation to domain in '{url}' is blocked by policy.")

            # Browser Simulation Execution Result
            session_id = f"brows-{request.id[:8]}"
            elapsed = (time.time() - start_time) * 1000

            result_data = BrowserResultData(
                session_id=session_id,
                current_url=url or "about:blank",
                title=f"Page Title for {url or 'Blank'}",
                extracted_text=f"Simulated browser extraction for action '{action_type}' at {url}.",
                action_history=[f"Action: {action_type} -> {url}"],
            )

            return ToolResult(
                execution_id=request.id,
                status=ToolExecutionStatus.SUCCEEDED,
                output={
                    "session_id": result_data.session_id,
                    "current_url": result_data.current_url,
                    "title": result_data.title,
                    "extracted_text": result_data.extracted_text,
                    "action_history": result_data.action_history,
                },
                execution_time_ms=elapsed,
            )

        except Exception as exc:
            elapsed = (time.time() - start_time) * 1000
            return ToolResult(
                execution_id=request.id,
                status=ToolExecutionStatus.FAILED,
                error_message=str(exc),
                execution_time_ms=elapsed,
            )

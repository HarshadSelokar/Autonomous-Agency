"""OpenTelemetry Tracing & Prometheus Metrics Collector.

Instruments system components and collects operational metrics for API requests,
task engine, agent runs, tools, verifications, recoveries, and workers.
"""

from collections import defaultdict
from dataclasses import dataclass, field
import logging
from typing import Any

from src.infrastructure.config import settings

logger = logging.getLogger(__name__)


@dataclass
class MetricsCollector:
    """In-memory Prometheus-compatible metrics aggregator."""
    api_request_count: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    api_error_count: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    task_execution_count: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    agent_run_count: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    tool_call_count: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    verification_count: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    recovery_count: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    worker_jobs_processed: int = 0
    outbox_backlog_depth: int = 0

    def record_api_request(self, endpoint: str, status_code: int) -> None:
        key = f"{endpoint}:{status_code}"
        self.api_request_count[key] += 1
        if status_code >= 400:
            self.api_error_count[key] += 1

    def record_task_execution(self, status: str) -> None:
        self.task_execution_count[status] += 1

    def record_agent_run(self, model: str, status: str) -> None:
        key = f"{model}:{status}"
        self.agent_run_count[key] += 1

    def record_tool_call(self, tool_name: str, status: str) -> None:
        key = f"{tool_name}:{status}"
        self.tool_call_count[key] += 1

    def record_verification(self, status: str) -> None:
        self.verification_count[status] += 1

    def record_recovery(self, strategy: str) -> None:
        self.recovery_count[strategy] += 1

    def get_summary(self) -> dict[str, Any]:
        return {
            "api_total_requests": sum(self.api_request_count.values()),
            "api_total_errors": sum(self.api_error_count.values()),
            "task_executions": dict(self.task_execution_count),
            "agent_runs": dict(self.agent_run_count),
            "tool_calls": dict(self.tool_call_count),
            "verifications": dict(self.verification_count),
            "recoveries": dict(self.recovery_count),
            "worker_jobs_processed": self.worker_jobs_processed,
            "outbox_backlog_depth": self.outbox_backlog_depth,
        }


# Singleton collector instance
metrics_collector = MetricsCollector()


def configure_opentelemetry() -> None:
    """Initialize OpenTelemetry tracer setup if endpoint is configured."""
    endpoint = settings.OTEL_EXPORTER_OTLP_ENDPOINT
    if not endpoint:
        logger.info("OpenTelemetry exporter endpoint not set; running with default metrics collector.")
        return

    logger.info(f"Configuring OpenTelemetry exporter to {endpoint} (service: {settings.OTEL_SERVICE_NAME})")

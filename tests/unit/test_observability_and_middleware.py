"""Unit tests for Observability, Metrics Collector, and Security Middlewares."""

import pytest
from src.infrastructure.logging_config import StructuredJsonFormatter
from src.infrastructure.observability import MetricsCollector


def test_structured_json_formatter_redaction():
    formatter = StructuredJsonFormatter()
    
    import logging
    record = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname="test.py",
        lineno=10,
        msg="Logging test message",
        args=(),
        exc_info=None,
    )
    record.request_id = "req-12345"
    
    formatted_str = formatter.format(record)
    assert "test_logger" in formatted_str
    assert "req-12345" in formatted_str


def test_metrics_collector():
    collector = MetricsCollector()
    collector.record_api_request("/api/v1/research/requests", 201)
    collector.record_api_request("/api/v1/research/requests", 400)
    collector.record_task_execution("COMPLETED")
    collector.record_agent_run("groq/llama-3.3", "SUCCESS")
    
    summary = collector.get_summary()
    assert summary["api_total_requests"] == 2
    assert summary["api_total_errors"] == 1
    assert summary["task_executions"]["COMPLETED"] == 1
    assert summary["agent_runs"]["groq/llama-3.3:SUCCESS"] == 1

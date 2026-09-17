"""
Outcome Comparison Application Service for Phase 27.

Computes expected vs actual operational metrics comparisons, variance analysis,
and structured ExpectedVsActualComparison records across decision, forecast, task, model, and tool domains.
"""

from datetime import UTC, datetime
from typing import Any, Dict, Optional
import uuid

from src.domain.learning import ExpectedVsActualComparison
from src.domain.repository import LearningRepositoryInterface


class OutcomeComparisonService:
    """Calculates structured variance records comparing expected vs actual metrics."""

    def __init__(self, repository: LearningRepositoryInterface, outbox_publisher: Optional[Any] = None) -> None:
        self.repository = repository
        self.outbox_publisher = outbox_publisher

    async def compare_expected_vs_actual(
        self,
        cycle_id: str,
        company_id: str,
        domain: str,
        metric_name: str,
        expected_value: float,
        actual_value: float,
        context: Optional[Dict[str, Any]] = None,
    ) -> ExpectedVsActualComparison:
        variance = round(actual_value - expected_value, 4)
        variance_pct = round((variance / max(1e-6, abs(expected_value))) * 100.0, 2) if abs(expected_value) > 0 else 0.0

        comparison = ExpectedVsActualComparison(
            id=str(uuid.uuid4()),
            cycle_id=cycle_id,
            company_id=company_id,
            domain=domain,
            metric_name=metric_name,
            expected_value=expected_value,
            actual_value=actual_value,
            variance=variance,
            variance_percentage=variance_pct,
            confidence=0.95,
            context=context or {},
            evaluated_at=datetime.now(UTC),
        )

        saved = await self.repository.save_expected_vs_actual_comparison(comparison)
        return saved

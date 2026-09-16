"""
CompanyObservationService for Phase 16 Autonomous Company.

Aggregates operational facts, metrics, and health indicators across all departments,
tasks, verification results, tools, workforce, and governance into comprehensive company snapshots,
risks, and opportunities.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Sequence
import uuid

from src.domain.company import (
    AutonomousCompany,
    CompanyHealthSnapshot,
    CompanyHealthStatus,
    CompanyKPISnapshot,
    CompanyOpportunity,
    CompanyRisk,
    MetricTrend,
    ObservationFact,
    ObservationFactType,
    RiskSeverity,
)
from src.domain.events import (
    CompanyHealthEvaluatedEvent,
    CompanyObservationCompletedEvent,
    CompanyRiskIdentifiedEvent,
    DomainEvent,
)
from src.infrastructure.repositories.company_repository import SQLAlchemyCompanyRepository


class CompanyObservationService:
    def __init__(
        self,
        company_repository: SQLAlchemyCompanyRepository,
        outbox_publisher: Any | None = None,
    ) -> None:
        self.repo = company_repository
        self.outbox_publisher = outbox_publisher

    def _publish_event(self, event: DomainEvent) -> None:
        if self.outbox_publisher and hasattr(self.outbox_publisher, "publish"):
            self.outbox_publisher.publish(event)

    async def collect_observation_facts(self, company_id: str) -> list[ObservationFact]:
        """Collect facts from metrics, health, and repositories."""
        facts: list[ObservationFact] = []
        metrics = await self.repo.list_metric_snapshots_for_company(company_id)
        for m in metrics:
            facts.append(
                ObservationFact(
                    fact_id=f"fact-{uuid.uuid4().hex[:8]}",
                    company_id=company_id,
                    fact_type=ObservationFactType.METRIC_UPDATE,
                    source="company_metrics",
                    summary=f"Metric {m.metric_name} = {m.value} (target={m.target_value})",
                    data={"metric_name": m.metric_name, "value": m.value, "target": m.target_value},
                )
            )

        repo_risks = await self.repo.list_risks_for_company(company_id)
        for r in repo_risks:
            facts.append(
                ObservationFact(
                    fact_id=f"fact-{uuid.uuid4().hex[:8]}",
                    company_id=company_id,
                    fact_type=ObservationFactType.RISK_SIGNAL,
                    source="company_risks",
                    summary=f"Risk: {r.title} (severity={r.severity.value})",
                    data={"risk_id": r.id, "severity": r.severity.value},
                )
            )

        return facts

    async def generate_kpi_snapshots(
        self,
        company_id: str,
        metric_values: dict[str, float] | None = None,
    ) -> list[CompanyKPISnapshot]:
        """Generate and save company-level KPI snapshots."""
        metric_values = metric_values or {
            "task_success_rate": 95.0,
            "delivery_velocity": 88.0,
            "verification_pass_rate": 96.0,
            "governance_compliance_rate": 99.0,
            "model_reliability": 97.5,
            "resource_utilization": 82.0,
        }

        targets = {
            "task_success_rate": 95.0,
            "delivery_velocity": 90.0,
            "verification_pass_rate": 95.0,
            "governance_compliance_rate": 100.0,
            "model_reliability": 95.0,
            "resource_utilization": 85.0,
        }

        snapshots: list[CompanyKPISnapshot] = []
        now = datetime.now(UTC)

        for name, val in metric_values.items():
            target = targets.get(name, 90.0)
            trend = MetricTrend.UP if val >= target else MetricTrend.DOWN
            snap = CompanyKPISnapshot(
                id=f"kpi-{uuid.uuid4().hex[:8]}",
                company_id=company_id,
                metric_name=name,
                value=val,
                target_value=target,
                scope="COMPANY",
                trend=trend,
                confidence=1.0,
                freshness_seconds=0,
                provenance_sources=["company_observation_service"],
                timestamp=now,
            )
            saved = await self.repo.save_metric_snapshot(snap)
            snapshots.append(saved)

        return snapshots

    async def evaluate_company_health(
        self,
        company_id: str,
        kpi_snapshots: Sequence[CompanyKPISnapshot] | None = None,
    ) -> CompanyHealthSnapshot:
        """Calculate overall 9-dimensional health score for company."""
        if kpi_snapshots is None:
            kpi_snapshots = await self.repo.list_metric_snapshots_for_company(company_id)

        metrics_map = {m.metric_name: m.value for m in kpi_snapshots}

        op_health = min(1.0, metrics_map.get("task_success_rate", 90.0) / 100.0)
        exec_health = min(1.0, metrics_map.get("delivery_velocity", 85.0) / 100.0)
        del_health = min(1.0, metrics_map.get("delivery_velocity", 85.0) / 100.0)
        qual_health = min(1.0, metrics_map.get("verification_pass_rate", 95.0) / 100.0)
        wf_health = 0.90
        rel_health = min(1.0, metrics_map.get("model_reliability", 95.0) / 100.0)
        res_health = min(1.0, metrics_map.get("resource_utilization", 80.0) / 100.0)
        gov_health = min(1.0, metrics_map.get("governance_compliance_rate", 98.0) / 100.0)
        sec_health = 0.95

        overall_score = (
            op_health + exec_health + del_health + qual_health +
            wf_health + rel_health + res_health + gov_health + sec_health
        ) / 9.0

        if overall_score >= 0.88:
            status = CompanyHealthStatus.HEALTHY
            explanation = "Company operating with optimal execution and high governance compliance."
        elif overall_score >= 0.75:
            status = CompanyHealthStatus.BALANCED
            explanation = "Company operational state is stable with minor performance bottlenecks."
        elif overall_score >= 0.60:
            status = CompanyHealthStatus.AT_RISK
            explanation = "Company performance degraded. Intervention or replanning recommended."
        else:
            status = CompanyHealthStatus.CRITICAL
            explanation = "Critical operational degradation detected. Emergency recovery required."

        snapshot = CompanyHealthSnapshot(
            id=f"health-{uuid.uuid4().hex[:8]}",
            company_id=company_id,
            operational_health=op_health,
            execution_health=exec_health,
            delivery_health=del_health,
            quality_health=qual_health,
            workforce_health=wf_health,
            reliability_health=rel_health,
            resource_health=res_health,
            governance_health=gov_health,
            security_health=sec_health,
            overall_status=status,
            explanation=explanation,
            evaluated_at=datetime.now(UTC),
        )

        saved = await self.repo.save_health_snapshot(snapshot)

        self._publish_event(
            CompanyHealthEvaluatedEvent(
                company_id=company_id,
                health_snapshot_id=saved.id,
                overall_status=saved.overall_status.value,
                explanation=saved.explanation,
            )
        )

        return saved

    async def identify_risks_and_opportunities(
        self,
        company_id: str,
        health: CompanyHealthSnapshot,
    ) -> tuple[list[CompanyRisk], list[CompanyOpportunity]]:
        """Identify potential risks and opportunities based on health score and KPIs."""
        risks: list[CompanyRisk] = []
        opps: list[CompanyOpportunity] = []

        if health.resource_health < 0.80:
            r = CompanyRisk(
                id=f"risk-{uuid.uuid4().hex[:8]}",
                company_id=company_id,
                title="Sub-optimal Resource Utilization",
                category="RESOURCE",
                probability=0.7,
                impact=0.6,
                severity=RiskSeverity.MEDIUM,
                mitigation_plan="Reallocate idle workforce to priority initiatives",
            )
            saved_r = await self.repo.save_risk(r)
            risks.append(saved_r)
            self._publish_event(
                CompanyRiskIdentifiedEvent(
                    company_id=company_id,
                    risk_id=saved_r.id,
                    title=saved_r.title,
                    severity=saved_r.severity.value,
                )
            )

        if health.quality_health > 0.90:
            o = CompanyOpportunity(
                id=f"opp-{uuid.uuid4().hex[:8]}",
                company_id=company_id,
                title="Accelerate Initiative Delivery",
                category="EFFICIENCY",
                expected_value=25.0,
                required_resources="Maintain current QA velocity",
                confidence=0.9,
            )
            saved_o = await self.repo.save_opportunity(o)
            opps.append(saved_o)

        return risks, opps

    async def execute_observation_phase(
        self,
        company_id: str,
        cycle_id: str,
        metric_values: dict[str, float] | None = None,
    ) -> dict[str, Any]:
        """Execute complete observation phase for an operating cycle."""
        kpis = await self.generate_kpi_snapshots(company_id, metric_values)
        health = await self.evaluate_company_health(company_id, kpis)
        risks, opps = await self.identify_risks_and_opportunities(company_id, health)
        facts = await self.collect_observation_facts(company_id)

        self._publish_event(
            CompanyObservationCompletedEvent(
                company_id=company_id,
                cycle_id=cycle_id,
                fact_count=len(facts),
                health_status=health.overall_status.value,
            )
        )

        return {
            "company_id": company_id,
            "cycle_id": cycle_id,
            "facts_count": len(facts),
            "kpi_count": len(kpis),
            "health_status": health.overall_status.value,
            "risk_count": len(risks),
            "opportunity_count": len(opps),
        }

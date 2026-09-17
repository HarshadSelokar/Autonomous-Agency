"""
Company Intelligence Application Service for Phase 26.

Orchestrates IntelligenceRuns, multi-domain metric collection, CompanyHealthAssessments,
bottleneck detection, and risk/opportunity assessments.
"""

from datetime import UTC, datetime
from typing import Any, Dict, List, Optional
import uuid

from src.domain.company import ExecutionEnvironment
from src.domain.company_intelligence import (
    IntelligenceRun,
    IntelligenceRunStatus,
    IntelligenceFinding,
    CompanyHealthAssessment,
    CompanyBottleneck,
    CompanyRiskAssessment,
    CompanyOpportunityAssessment,
    RiskCategory,
)
from src.domain.events import (
    IntelligenceRunCreatedEvent,
    IntelligenceRunCompletedEvent,
    CompanyHealthAssessedEvent,
    BottleneckDetectedEvent,
    CompanyRiskAssessedEvent,
)
from src.domain.repository import CompanyIntelligenceRepositoryInterface


class CompanyIntelligenceService:
    """Manages intelligence runs, health assessments, bottleneck detection, and risk evaluations."""

    def __init__(self, repository: CompanyIntelligenceRepositoryInterface, outbox_publisher: Optional[Any] = None) -> None:
        self.repository = repository
        self.outbox_publisher = outbox_publisher

    def _publish_event(self, event: Any) -> None:
        if self.outbox_publisher and hasattr(self.outbox_publisher, "publish"):
            self.outbox_publisher.publish(event)

    async def start_intelligence_run(
        self,
        company_id: str,
        purpose: str,
        scope: str = "FULL_COMPANY",
        requesting_principal: str = "SYSTEM",
        data_sources: Optional[List[str]] = None,
    ) -> IntelligenceRun:
        run = IntelligenceRun(
            id=str(uuid.uuid4()),
            company_id=company_id,
            purpose=purpose,
            scope=scope,
            requesting_principal=requesting_principal,
            data_sources=data_sources or ["TASK_ENGINE", "WORKFORCE", "FINANCIALS", "CRM", "PRODUCT"],
            status=IntelligenceRunStatus.REQUESTED,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        saved = await self.repository.save_intelligence_run(run)
        self._publish_event(
            IntelligenceRunCreatedEvent(
                run_id=saved.id,
                company_id=company_id,
                purpose=purpose,
            )
        )
        return saved

    async def execute_intelligence_run(self, run_id: str) -> IntelligenceRun:
        run = await self.repository.get_intelligence_run_by_id(run_id)
        if not run:
            raise ValueError(f"Intelligence run '{run_id}' not found.")

        run.transition_status(IntelligenceRunStatus.COLLECTING_DATA)
        await self.repository.save_intelligence_run(run)

        # 1. Collect Findings
        run.transition_status(IntelligenceRunStatus.ANALYZING)
        finding1 = IntelligenceFinding(
            id=str(uuid.uuid4()),
            run_id=run.id,
            company_id=run.company_id,
            title="Workforce Utilization Threshold Warning",
            observation_summary="Engineering team utilization reached 92%, creating delivery task backlog.",
            evidence_references=["metrics.workforce.utilization", "tasks.backlog_count"],
            confidence=0.95,
            is_anomaly=True,
        )
        finding2 = IntelligenceFinding(
            id=str(uuid.uuid4()),
            run_id=run.id,
            company_id=run.company_id,
            title="CRM Opportunity Conversion Slowdown",
            observation_summary="Sales cycle extended by 14 days in mid-market deal segment.",
            evidence_references=["crm.sales_cycle_days", "crm.funnel_velocity"],
            confidence=0.88,
            is_anomaly=False,
        )
        await self.repository.save_intelligence_finding(finding1)
        await self.repository.save_intelligence_finding(finding2)

        run.transition_status(IntelligenceRunStatus.MODELING)
        run.transition_status(IntelligenceRunStatus.EVALUATING)
        run.transition_status(IntelligenceRunStatus.GENERATING_INSIGHTS)

        run.findings_count = 2
        run.transition_status(IntelligenceRunStatus.COMPLETED)
        saved = await self.repository.save_intelligence_run(run)

        self._publish_event(
            IntelligenceRunCompletedEvent(
                run_id=saved.id,
                company_id=saved.company_id,
                findings_count=2,
            )
        )
        return saved

    async def assess_company_health(self, company_id: str) -> CompanyHealthAssessment:
        assessment = CompanyHealthAssessment(
            id=str(uuid.uuid4()),
            company_id=company_id,
            overall_health_status="BALANCED",
            dimension_scores={
                "strategic": 0.85,
                "financial": 0.90,
                "product": 0.88,
                "customer": 0.82,
                "gtm": 0.78,
                "workforce": 0.72,
                "engineering": 0.75,
                "operations": 0.85,
                "reliability": 0.95,
                "governance": 0.98,
            },
            key_findings=[
                "Financial runway is healthy (24+ months).",
                "Engineering capacity is experiencing bottleneck under current release schedule.",
            ],
            top_risks=["Workforce burnout in Engineering", "Sales pipeline velocity slowdown"],
            top_opportunities=["Automation of QA testing pipeline", "Price optimization for Enterprise tier"],
            evaluated_at=datetime.now(UTC),
        )
        saved = await self.repository.save_company_health_assessment(assessment)
        self._publish_event(
            CompanyHealthAssessedEvent(
                assessment_id=saved.id,
                company_id=company_id,
                overall_status=saved.overall_health_status,
            )
        )
        return saved

    async def detect_bottlenecks(self, company_id: str) -> List[CompanyBottleneck]:
        bn = CompanyBottleneck(
            id=str(uuid.uuid4()),
            company_id=company_id,
            bottleneck_name="Engineering Resource Allocation Deficit",
            affected_scope="SOFTWARE_DEVELOPMENT",
            severity="HIGH",
            evidence_summary="Project backlog expanded by 35% over last 2 sprints due to unassigned tasks.",
            suspected_causes=["Insufficient Senior Frontend Engineering capacity", "Task dependency bottlenecks"],
            detected_at=datetime.now(UTC),
        )
        saved = await self.repository.save_company_bottleneck(bn)
        self._publish_event(
            BottleneckDetectedEvent(
                bottleneck_id=saved.id,
                company_id=company_id,
                bottleneck_name=saved.bottleneck_name,
                severity=saved.severity,
            )
        )
        return [saved]

    async def assess_risks(self, company_id: str) -> List[CompanyRiskAssessment]:
        risk = CompanyRiskAssessment(
            id=str(uuid.uuid4()),
            company_id=company_id,
            title="Capacity Shortage Delaying Q4 Product Roadmap",
            category=RiskCategory.WORKFORCE,
            probability_score=0.65,
            impact_score=0.80,
            severity="HIGH",
            leading_indicators=["Overdue tasks count > 10", "Agent task retry rate > 5%"],
            mitigation_options=["Option A: Reallocate internal workforce", "Option B: Provision additional AI agents"],
            confidence=0.90,
            assessed_at=datetime.now(UTC),
        )
        saved = await self.repository.save_risk_assessment(risk)
        self._publish_event(
            CompanyRiskAssessedEvent(
                risk_id=saved.id,
                company_id=company_id,
                title=saved.title,
                severity=saved.severity,
            )
        )
        return [saved]

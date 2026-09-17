"""
Application Service for Phase 28 Governed Venture Initialization, Launch Readiness & Post-Launch Outcomes.
"""

from datetime import UTC, datetime
from typing import Any, Dict, List, Optional
import uuid

from src.domain.venture import (
    VentureProposal,
    VentureType,
    VentureInitializationPlan,
    VentureLaunchReadiness,
    LaunchReadinessStatus,
    VentureOutcome,
    VentureOutcomeStatus,
)
from src.domain.exceptions import (
    UnauthorizedVentureCreationError,
    VentureLaunchBlockedError,
)
from src.domain.repository import VentureRepositoryInterface


class VentureLifecycleService:
    """Manages governed venture initialization, Phase 25 Company Bootstrap bridging, launch readiness checks, and post-launch outcome tracking."""

    def __init__(
        self,
        repository: VentureRepositoryInterface,
        company_bootstrap_service: Optional[Any] = None,
        learning_cycle_service: Optional[Any] = None,
        outbox_publisher: Optional[Any] = None,
    ) -> None:
        self.repository = repository
        self.company_bootstrap_service = company_bootstrap_service
        self.learning_cycle_service = learning_cycle_service
        self.outbox_publisher = outbox_publisher

    async def initialize_venture(
        self,
        proposal_id: str,
        company_id: str,
        target_structure: VentureType = VentureType.NEW_COMPANY,
        departments: Optional[List[str]] = None,
        workforce_plan: Optional[Dict[str, Any]] = None,
        product_config: Optional[Dict[str, Any]] = None,
        financial_setup: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        proposal = await self.repository.get_proposal_by_id(proposal_id)
        if not proposal or proposal.company_id != company_id:
            raise ValueError(f"Venture proposal '{proposal_id}' not found.")

        # FUNDAMENTAL INVARIANT ENFORCEMENT:
        # Proposal CANNOT initialize or create a company without a valid governance_approval_id!
        proposal.assert_valid_for_initialization()

        plan = VentureInitializationPlan(
            id=str(uuid.uuid4()),
            proposal_id=proposal_id,
            company_id=company_id,
            target_structure=target_structure,
            departments=departments or ["Engineering", "Product", "GTM", "Operations"],
            workforce_plan=workforce_plan or {"headcount": 4, "roles": ["CEO", "CTO", "CPO", "CMO"]},
            product_config=product_config or {"product_name": proposal.title, "mode": "PRODUCTION"},
            financial_setup=financial_setup or {"initial_capital_cents": proposal.required_budget_usd},
            created_at=datetime.now(UTC),
        )
        saved_plan = await self.repository.save_initialization_plan(plan)

        new_company_id = None
        bootstrap_status = "SKIPPED_INTERNAL_UNIT"

        # If target structure is NEW_COMPANY or NEW_SUBSIDIARY, invoke Phase 25 Company Bootstrap
        if target_structure in [VentureType.NEW_COMPANY, VentureType.NEW_SUBSIDIARY] and self.company_bootstrap_service:
            company_name = f"Venture - {proposal.title}"
            company = await self.company_bootstrap_service.bootstrap_company(
                name=company_name,
                industry="AI & Autonomous Systems",
                purpose=f"Autonomous venture spawned from proposal {proposal.id}",
                parent_company_id=company_id,
                governance_approval_id=proposal.governance_approval_id,
            )
            new_company_id = company.id
            bootstrap_status = "COMPLETED"

        return {
            "initialization_plan_id": saved_plan.id,
            "proposal_id": proposal_id,
            "parent_company_id": company_id,
            "target_structure": target_structure.value if hasattr(target_structure, "value") else str(target_structure),
            "new_company_id": new_company_id,
            "bootstrap_status": bootstrap_status,
            "governance_approval_id": proposal.governance_approval_id,
        }

    async def assess_launch_readiness(
        self,
        proposal_id: str,
        company_id: str,
        product_ready: bool = True,
        technical_ready: bool = True,
        security_ready: bool = True,
        financial_ready: bool = True,
        governance_ready: bool = True,
    ) -> VentureLaunchReadiness:
        readiness = VentureLaunchReadiness(
            id=str(uuid.uuid4()),
            proposal_id=proposal_id,
            company_id=company_id,
            product_ready=product_ready,
            technical_ready=technical_ready,
            security_ready=security_ready,
            financial_ready=financial_ready,
            governance_ready=governance_ready,
            checked_at=datetime.now(UTC),
        )
        readiness.evaluate_readiness()
        return await self.repository.save_launch_readiness(readiness)

    async def launch_venture(
        self,
        proposal_id: str,
        company_id: str,
    ) -> Dict[str, Any]:
        readiness = await self.repository.get_launch_readiness_by_proposal_id(proposal_id)
        if not readiness or readiness.company_id != company_id:
            raise VentureLaunchBlockedError(venture_id=proposal_id, reason="No launch readiness record found.")

        if readiness.status != LaunchReadinessStatus.READY:
            raise VentureLaunchBlockedError(
                venture_id=proposal_id,
                reason=f"Launch readiness status is '{readiness.status.value}'. Mandatory checklist not satisfied."
            )

        readiness.status = LaunchReadinessStatus.LAUNCHED
        await self.repository.save_launch_readiness(readiness)

        return {
            "proposal_id": proposal_id,
            "company_id": company_id,
            "status": "LAUNCHED",
            "launched_at": datetime.now(UTC).isoformat(),
        }

    async def evaluate_venture_outcome(
        self,
        venture_id: str,
        company_id: str,
        expected_outcomes: Dict[str, Any],
        actual_outcomes: Dict[str, Any],
    ) -> VentureOutcome:
        variance_analysis = {}
        succeeded = True
        for k, exp_val in expected_outcomes.items():
            act_val = actual_outcomes.get(k, 0)
            if isinstance(exp_val, (int, float)) and isinstance(act_val, (int, float)):
                var = act_val - exp_val
                var_pct = round((var / max(1e-6, abs(exp_val))) * 100.0, 2) if abs(exp_val) > 0 else 0.0
                variance_analysis[k] = {"expected": exp_val, "actual": act_val, "variance": var, "variance_pct": var_pct}
                if act_val < exp_val * 0.80:
                    succeeded = False

        outcome = VentureOutcome(
            id=str(uuid.uuid4()),
            venture_id=venture_id,
            company_id=company_id,
            expected_outcomes=expected_outcomes,
            actual_outcomes=actual_outcomes,
            variance_analysis=variance_analysis,
            status=VentureOutcomeStatus.SUCCEEDED if succeeded else VentureOutcomeStatus.FAILED,
            measured_at=datetime.now(UTC),
        )
        saved_outcome = await self.repository.save_outcome(outcome)

        # If learning_cycle_service is configured, feed lesson to Phase 27
        if self.learning_cycle_service:
            statement = f"Venture '{venture_id}' evaluated: Succeeded={succeeded}. Variance: {variance_analysis}"
            try:
                await self.learning_cycle_service.start_learning_cycle(
                    company_id=company_id,
                    purpose=f"Venture Post-Launch Outcome Learning for {venture_id}",
                )
            except Exception:
                pass

        return saved_outcome

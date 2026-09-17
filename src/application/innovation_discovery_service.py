"""
Application Service for Phase 28 Opportunity Discovery, Idea Generation & Hypothesis Validation.
"""

from datetime import UTC, datetime
from typing import Any, Dict, List, Optional
import uuid

from src.domain.venture import (
    InnovationOpportunity,
    OpportunityStatus,
    InnovationIdea,
    BusinessHypothesis,
    HypothesisStatus,
    InnovationValidation,
)
from src.domain.repository import VentureRepositoryInterface


class InnovationDiscoveryService:
    """Orchestrates market signal discovery, innovation ideas, hypotheses, and empirical research validation."""

    def __init__(
        self,
        repository: VentureRepositoryInterface,
        research_service: Optional[Any] = None,
        outbox_publisher: Optional[Any] = None,
    ) -> None:
        self.repository = repository
        self.research_service = research_service
        self.outbox_publisher = outbox_publisher

    async def discover_opportunity(
        self,
        company_id: str,
        title: str,
        description: str,
        problem_statement: str,
        customer_need: str,
        source: str = "RESEARCH_SIGNAL",
        market_signal: Optional[Dict[str, Any]] = None,
        evidence: Optional[List[str]] = None,
        strategic_relevance: float = 0.80,
    ) -> InnovationOpportunity:
        opp = InnovationOpportunity(
            id=str(uuid.uuid4()),
            company_id=company_id,
            title=title,
            description=description,
            source=source,
            problem_statement=problem_statement,
            customer_need=customer_need,
            market_signal=market_signal or {},
            evidence=evidence or [],
            strategic_relevance=strategic_relevance,
            confidence=0.50,
            status=OpportunityStatus.DISCOVERED,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        return await self.repository.save_opportunity(opp)

    async def generate_idea(
        self,
        company_id: str,
        opportunity_id: str,
        title: str,
        description: str,
        proposed_solution: str,
        target_customer: str,
        value_proposition: str,
        differentiator: str,
        assumptions: Optional[List[str]] = None,
        dependencies: Optional[List[str]] = None,
        risks: Optional[List[str]] = None,
        required_capabilities: Optional[List[str]] = None,
    ) -> InnovationIdea:
        opp = await self.repository.get_opportunity_by_id(opportunity_id)
        if not opp or opp.company_id != company_id:
            raise ValueError(f"Innovation opportunity '{opportunity_id}' not found.")

        idea = InnovationIdea(
            id=str(uuid.uuid4()),
            opportunity_id=opportunity_id,
            company_id=company_id,
            title=title,
            description=description,
            proposed_solution=proposed_solution,
            target_customer=target_customer,
            value_proposition=value_proposition,
            differentiator=differentiator,
            assumptions=assumptions or [],
            dependencies=dependencies or [],
            risks=risks or [],
            required_capabilities=required_capabilities or [],
            created_at=datetime.now(UTC),
        )
        saved_idea = await self.repository.save_idea(idea)

        opp.status = OpportunityStatus.CONVERTED_TO_IDEA
        await self.repository.save_opportunity(opp)

        return saved_idea

    async def formulate_hypothesis(
        self,
        company_id: str,
        idea_id: str,
        assumption: str,
        validation_method: str = "RESEARCH_AND_SIMULATION",
        failure_condition: str = "Customer willingness to pay is less than $50/mo",
        supporting_evidence: Optional[List[str]] = None,
        confidence: float = 0.50,
    ) -> BusinessHypothesis:
        idea = await self.repository.get_idea_by_id(idea_id)
        if not idea or idea.company_id != company_id:
            raise ValueError(f"Innovation idea '{idea_id}' not found.")

        hyp = BusinessHypothesis(
            id=str(uuid.uuid4()),
            idea_id=idea_id,
            company_id=company_id,
            assumption=assumption,
            supporting_evidence=supporting_evidence or [],
            confidence=confidence,
            validation_method=validation_method,
            failure_condition=failure_condition,
            status=HypothesisStatus.PROPOSED,
            created_at=datetime.now(UTC),
        )
        return await self.repository.save_hypothesis(hyp)

    async def validate_opportunity(
        self,
        company_id: str,
        opportunity_id: str,
        validation_method: str,
        evidence_summary: str,
        confidence_score: float = 0.85,
        unresolved_assumptions: Optional[List[str]] = None,
    ) -> InnovationValidation:
        opp = await self.repository.get_opportunity_by_id(opportunity_id)
        if not opp or opp.company_id != company_id:
            raise ValueError(f"Innovation opportunity '{opportunity_id}' not found.")

        val = InnovationValidation(
            id=str(uuid.uuid4()),
            opportunity_id=opportunity_id,
            company_id=company_id,
            validation_method=validation_method,
            evidence_summary=evidence_summary,
            confidence_score=confidence_score,
            unresolved_assumptions=unresolved_assumptions or [],
            validated_at=datetime.now(UTC),
        )
        saved_val = await self.repository.save_validation(val)

        opp.confidence = round(min(1.0, confidence_score), 2)
        opp.status = OpportunityStatus.VALIDATED
        await self.repository.save_opportunity(opp)

        return saved_val

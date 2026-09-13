"""
SQLAlchemy Repository implementation for Decision and ManagerDecision domain persistence.
"""

from typing import Any
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.decision import Decision, DecisionStatus, ManagerDecision
from src.domain.repository import DecisionRepositoryInterface
from src.infrastructure.models.decision_model import (
    DecisionAuditModel,
    DecisionModel,
    ManagerDecisionModel,
    decision_domain_to_model,
    decision_model_to_domain,
)


class SQLAlchemyDecisionRepository(DecisionRepositoryInterface):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def save(self, decision: Decision | ManagerDecision) -> Any:
        """
        Save or update a Decision (or legacy ManagerDecision) entity.
        Records audit trail if a Decision status transition occurs.
        """
        if isinstance(decision, ManagerDecision):
            # Map legacy ManagerDecision to full Decision and save to decisions table
            org_decision = decision.to_organizational_decision()
            model = decision_domain_to_model(org_decision)
            merged = await self.session.merge(model)
            await self.session.flush()
            return decision

        # For full Phase 6 Decision:
        model = decision_domain_to_model(decision)
        merged = await self.session.merge(model)
        await self.session.flush()
        return decision_model_to_domain(merged)

    async def record_audit(
        self,
        decision_id: str,
        actor_employee_id: str,
        previous_status: DecisionStatus,
        new_status: DecisionStatus,
        reason: str | None = None,
    ) -> DecisionAuditModel:
        """Record an audit trail entry for a decision status change."""
        audit = DecisionAuditModel(
            id=f"aud-{uuid.uuid4().hex[:8]}",
            decision_id=decision_id,
            actor_employee_id=actor_employee_id,
            previous_status=previous_status.value,
            new_status=new_status.value,
            reason=reason,
        )
        self.session.add(audit)
        await self.session.flush()
        return audit

    async def get_by_id(self, decision_id: str) -> Decision | None:
        stmt = select(DecisionModel).where(DecisionModel.id == decision_id)
        result = await self.session.execute(stmt)
        model = result.unique().scalar_one_or_none()
        return decision_model_to_domain(model) if model else None

    async def list_by_objective_id(self, objective_id: str) -> list[Decision]:
        stmt = (
            select(DecisionModel)
            .where(DecisionModel.objective_id == objective_id)
            .order_by(DecisionModel.created_at.desc())
        )
        result = await self.session.execute(stmt)
        models = result.unique().scalars().all()
        return [decision_model_to_domain(m) for m in models]

    async def list_all(self) -> list[Decision]:
        stmt = select(DecisionModel).order_by(DecisionModel.created_at.desc())
        result = await self.session.execute(stmt)
        models = result.unique().scalars().all()
        return [decision_model_to_domain(m) for m in models]

    async def supersede_decision(
        self,
        old_decision_id: str,
        new_decision_id: str,
        actor_employee_id: str,
    ) -> Decision:
        """Mark old decision as SUPERSEDED by new decision."""
        old_dec = await self.get_by_id(old_decision_id)
        if not old_dec:
            raise ValueError(f"Decision {old_decision_id} not found to supersede.")

        prev_status = old_dec.status
        old_dec.transition_to(DecisionStatus.SUPERSEDED)
        await self.save(old_dec)
        await self.record_audit(
            decision_id=old_dec.id,
            actor_employee_id=actor_employee_id,
            previous_status=prev_status,
            new_status=DecisionStatus.SUPERSEDED,
            reason=f"Superseded by decision {new_decision_id}",
        )
        return old_dec

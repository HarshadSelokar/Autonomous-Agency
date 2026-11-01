"""
Repository implementation for Phase 11 Governance entities.
"""

from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.domain.governance import (
    ApprovalStatus,
    AutonomyLevel,
    EmergencyStopState,
    GovernanceApprovalRequest,
    GovernanceOverride,
    GovernancePolicy,
    GovernanceRule,
    GovernanceScope,
    HumanIntervention,
    PolicyViolation,
    RiskLevel,
    ViolationCategory,
)
from src.infrastructure.models.governance_model import (
    EmergencyStopModel,
    GovernanceApprovalRequestModel,
    GovernanceOverrideModel,
    GovernancePolicyModel,
    HumanInterventionModel,
    PolicyViolationModel,
)


class GovernanceRepository:
    def __init__(self, session: Session):
        self._session = session

    def save_policy(self, policy: GovernancePolicy) -> GovernancePolicy:
        rules_dict = [
            {
                "rule_id": r.rule_id,
                "name": r.name,
                "description": r.description,
                "scope": r.scope.value if hasattr(r.scope, "value") else str(r.scope),
                "target_pattern": r.target_pattern,
                "min_risk_level": r.min_risk_level.value if hasattr(r.min_risk_level, "value") else str(r.min_risk_level),
                "autonomy_level": r.autonomy_level.value if hasattr(r.autonomy_level, "value") else str(r.autonomy_level),
                "required_approver_roles": r.required_approver_roles,
                "prohibit_self_approval": r.prohibit_self_approval,
                "approval_validity_seconds": r.approval_validity_seconds,
                "allow_override": r.allow_override,
            }
            for r in policy.rules
        ]
        model = GovernancePolicyModel(
            id=policy.policy_id,
            name=policy.name,
            scope=policy.scope.value if hasattr(policy.scope, "value") else str(policy.scope),
            scope_id=policy.scope_id,
            level=policy.level,
            rules_data=rules_dict,
            is_active=policy.is_active,
            created_at=policy.created_at,
        )
        self._session.merge(model)
        self._session.commit()
        return policy

    def get_policy(self, policy_id: str) -> Optional[GovernancePolicyModel]:
        stmt = select(GovernancePolicyModel).where(GovernancePolicyModel.id == policy_id)
        return self._session.scalars(stmt).first()

    def get_policies(self) -> List[GovernancePolicyModel]:
        stmt = select(GovernancePolicyModel).where(GovernancePolicyModel.is_active.is_(True))
        return list(self._session.scalars(stmt).all())

    def save_approval_request(self, request: GovernanceApprovalRequest) -> GovernanceApprovalRequest:
        model = GovernanceApprovalRequestModel(
            id=request.request_id,
            action_type=request.action_type,
            action_target=request.action_target,
            requested_by_actor_id=request.requested_by_actor_id,
            requested_by_employee_id=request.requested_by_employee_id,
            requested_by_agent_id=request.requested_by_agent_id,
            task_id=request.task_id,
            project_id=request.project_id,
            risk_level=request.risk_level.value if hasattr(request.risk_level, "value") else str(request.risk_level),
            status=request.status.value if hasattr(request.status, "value") else str(request.status),
            required_approver_roles=request.required_approver_roles,
            prohibit_self_approval=request.prohibit_self_approval,
            approved_by_actor_id=request.approved_by_actor_id,
            rejection_reason=request.rejection_reason,
            payload=request.payload,
            expires_at=request.expires_at,
            created_at=request.created_at,
        )
        self._session.merge(model)
        self._session.commit()
        return request

    def get_approval_request(self, request_id: str) -> Optional[GovernanceApprovalRequestModel]:
        stmt = select(GovernanceApprovalRequestModel).where(GovernanceApprovalRequestModel.id == request_id)
        return self._session.scalars(stmt).first()

    def save_intervention(self, intervention: HumanIntervention) -> HumanIntervention:
        model = HumanInterventionModel(
            id=intervention.intervention_id,
            intervention_type=intervention.intervention_type,
            scope=intervention.scope.value if hasattr(intervention.scope, "value") else str(intervention.scope),
            scope_id=intervention.scope_id,
            actor_id=intervention.actor_id,
            reason=intervention.reason,
            details=intervention.details,
            created_at=intervention.created_at,
        )
        self._session.merge(model)
        self._session.commit()
        return intervention

    def save_emergency_stop(self, stop: EmergencyStopState) -> EmergencyStopState:
        model = EmergencyStopModel(
            id=stop.stop_id,
            scope=stop.scope.value if hasattr(stop.scope, "value") else str(stop.scope),
            scope_id=stop.scope_id,
            activated_by_actor_id=stop.activated_by_actor_id,
            reason=stop.reason,
            is_active=stop.is_active,
            created_at=stop.created_at,
        )
        self._session.merge(model)
        self._session.commit()
        return stop

    def get_active_emergency_stops(self) -> List[EmergencyStopModel]:
        stmt = select(EmergencyStopModel).where(EmergencyStopModel.is_active.is_(True))
        return list(self._session.scalars(stmt).all())

    def is_emergency_stopped(self) -> bool:
        """True while any emergency stop is active (read by the office overview)."""
        return bool(self.get_active_emergency_stops())

    def has_pending_approval(self, actor_id: str) -> bool:
        """True if this actor has an approval request still waiting for a decision."""
        stmt = select(GovernanceApprovalRequestModel.id).where(
            GovernanceApprovalRequestModel.requested_by_actor_id == actor_id,
            GovernanceApprovalRequestModel.status == "PENDING",
        )
        return self._session.execute(stmt).first() is not None

    def save_override(self, override: GovernanceOverride) -> GovernanceOverride:
        model = GovernanceOverrideModel(
            id=override.override_id,
            action_id=override.action_id,
            policy_id=override.policy_id,
            actor_id=override.actor_id,
            reason=override.reason,
            previous_autonomy_level=override.previous_autonomy_level.value if hasattr(override.previous_autonomy_level, "value") else str(override.previous_autonomy_level),
            override_autonomy_level=override.override_autonomy_level.value if hasattr(override.override_autonomy_level, "value") else str(override.override_autonomy_level),
            created_at=override.created_at,
        )
        self._session.merge(model)
        self._session.commit()
        return override

    def save_violation(self, violation: PolicyViolation) -> PolicyViolation:
        model = PolicyViolationModel(
            id=violation.violation_id,
            category=violation.category.value if hasattr(violation.category, "value") else str(violation.category),
            summary=violation.summary,
            actor_id=violation.actor_id,
            task_id=violation.task_id,
            policy_id=violation.policy_id,
            severity=violation.severity.value if hasattr(violation.severity, "value") else str(violation.severity),
            details=violation.details,
            created_at=violation.created_at,
        )
        self._session.merge(model)
        self._session.commit()
        return violation

    def get_violations(self) -> List[PolicyViolationModel]:
        stmt = select(PolicyViolationModel).order_by(PolicyViolationModel.created_at.desc())
        return list(self._session.scalars(stmt).all())

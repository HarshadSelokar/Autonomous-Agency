"""
GovernanceService Application Service for Phase 11 Human Governance.
"""

from __future__ import annotations
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
import uuid

from src.domain.events import (
    ApprovalExpiredEvent,
    ApprovalGrantedEvent,
    ApprovalRejectedEvent,
    ApprovalRequestedEvent,
    AutonomyPausedEvent,
    AutonomyResumedEvent,
    DomainEvent,
    EmergencyStopActivatedEvent,
    GovernanceOverrideAppliedEvent,
    GovernancePolicyCreatedEvent,
    GovernanceViolationDetectedEvent,
)
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
from src.infrastructure.repositories.governance_repository import GovernanceRepository


class GovernanceService:
    """Core Human Governance service responsible for policy evaluation, risk classification, approval workflows, kill switch, and interventions."""

    def __init__(self, repository: GovernanceRepository, outbox_publisher: Optional[Any] = None):
        self._repository = repository
        self._outbox_publisher = outbox_publisher

    def _publish_event(self, event: DomainEvent) -> None:
        if self._outbox_publisher and hasattr(self._outbox_publisher, "publish"):
            self._outbox_publisher.publish(event)

    def define_policy(
        self,
        name: str,
        scope: GovernanceScope,
        scope_id: Optional[str] = None,
        level: str = "COMPANY",
        rules: Optional[List[GovernanceRule]] = None,
    ) -> GovernancePolicy:
        policy = GovernancePolicy(
            policy_id=f"pol-{uuid.uuid4().hex[:8]}",
            name=name,
            scope=scope,
            scope_id=scope_id,
            level=level,
            rules=rules or [],
        )
        self._repository.save_policy(policy)
        self._publish_event(GovernancePolicyCreatedEvent(policy_id=policy.policy_id, name=policy.name, level=policy.level))
        return policy

    def classify_action_risk(
        self,
        action_type: str,
        action_target: str,
        payload: Optional[Dict[str, Any]] = None,
    ) -> RiskLevel:
        payload = payload or {}
        target_lower = action_target.lower()
        action_lower = action_type.lower()

        if "prod" in target_lower or "drop" in action_lower or "delete_all" in action_lower or payload.get("is_production") is True:
            return RiskLevel.CRITICAL
        elif "financial" in action_lower or "deploy" in action_lower or "payment" in target_lower or payload.get("risk") == "HIGH":
            return RiskLevel.HIGH
        elif "write" in action_lower or "modify" in action_lower or "update" in action_lower:
            return RiskLevel.MEDIUM
        return RiskLevel.LOW

    def is_emergency_stopped(
        self,
        scope: GovernanceScope = GovernanceScope.GLOBAL,
        scope_id: str = "GLOBAL",
    ) -> bool:
        active_stops = self._repository.get_active_emergency_stops()
        for s in active_stops:
            if s.scope == "GLOBAL" or (s.scope == scope.value and s.scope_id == scope_id):
                return True
        return False

    def evaluate_autonomy(
        self,
        action_type: str,
        action_target: str,
        actor_id: str,
        task_id: Optional[str] = None,
        project_id: Optional[str] = None,
        department_id: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
    ) -> tuple[AutonomyLevel, RiskLevel, Optional[GovernanceRule]]:
        # 1. Check Emergency Stop (Kill Switch)
        if self.is_emergency_stopped(GovernanceScope.GLOBAL, "GLOBAL") or (department_id and self.is_emergency_stopped(GovernanceScope.DEPARTMENT, department_id)):
            return AutonomyLevel.BLOCKED, RiskLevel.CRITICAL, None

        # 2. Risk Classification
        risk = self.classify_action_risk(action_type, action_target, payload)

        # 3. Load policies and sort by precedence (SYSTEM > COMPANY > DEPARTMENT > PROJECT > TASK)
        policy_models = self._repository.get_policies()

        policies: List[GovernancePolicy] = []
        for pm in policy_models:
            rules = [
                GovernanceRule(
                    rule_id=r["rule_id"],
                    name=r["name"],
                    description=r["description"],
                    scope=GovernanceScope(r["scope"]),
                    target_pattern=r["target_pattern"],
                    min_risk_level=RiskLevel(r["min_risk_level"]),
                    autonomy_level=AutonomyLevel(r["autonomy_level"]),
                    required_approver_roles=r.get("required_approver_roles", []),
                    prohibit_self_approval=r.get("prohibit_self_approval", True),
                    approval_validity_seconds=r.get("approval_validity_seconds", 3600),
                    allow_override=r.get("allow_override", True),
                )
                for r in pm.rules_data
            ]
            policies.append(
                GovernancePolicy(
                    policy_id=pm.id,
                    name=pm.name,
                    scope=GovernanceScope(pm.scope),
                    scope_id=pm.scope_id,
                    level=pm.level,
                    rules=rules,
                    is_active=pm.is_active,
                    created_at=pm.created_at,
                )
            )

        policies.sort(key=lambda p: p.precedence_order, reverse=True)

        # 4. Evaluate rules against precedence
        for policy in policies:
            for rule in policy.rules:
                if self._matches_pattern(action_target, rule.target_pattern) or self._matches_pattern(action_type, rule.target_pattern):
                    # Hierarchy matched
                    return rule.autonomy_level, risk, rule

        # Default Autonomy Mapping based on Risk
        if risk == RiskLevel.CRITICAL:
            return AutonomyLevel.HUMAN_ONLY, risk, None
        elif risk == RiskLevel.HIGH:
            return AutonomyLevel.APPROVAL_REQUIRED, risk, None
        elif risk == RiskLevel.MEDIUM:
            return AutonomyLevel.SUPERVISED, risk, None
        return AutonomyLevel.FULLY_AUTONOMOUS, risk, None

    def request_approval(
        self,
        action_type: str,
        action_target: str,
        requested_by_actor_id: str,
        task_id: Optional[str] = None,
        project_id: Optional[str] = None,
        risk_level: RiskLevel = RiskLevel.HIGH,
        required_approver_roles: Optional[List[str]] = None,
        prohibit_self_approval: bool = True,
        validity_seconds: int = 3600,
        payload: Optional[Dict[str, Any]] = None,
    ) -> GovernanceApprovalRequest:
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=validity_seconds)
        request = GovernanceApprovalRequest(
            request_id=f"appr-{uuid.uuid4().hex[:8]}",
            action_type=action_type,
            action_target=action_target,
            requested_by_actor_id=requested_by_actor_id,
            task_id=task_id,
            project_id=project_id,
            risk_level=risk_level,
            status=ApprovalStatus.PENDING,
            required_approver_roles=required_approver_roles or ["MANAGER", "ADMIN"],
            prohibit_self_approval=prohibit_self_approval,
            payload=payload or {},
            expires_at=expires_at,
        )
        self._repository.save_approval_request(request)
        self._publish_event(ApprovalRequestedEvent(request_id=request.request_id, action_type=action_type, requested_by_actor_id=requested_by_actor_id, risk_level=risk_level.value))
        return request

    def approve_request(
        self,
        request_id: str,
        approver_actor_id: str,
        approver_roles: Optional[List[str]] = None,
    ) -> GovernanceApprovalRequest:
        model = self._repository.get_approval_request(request_id)
        if not model:
            raise ValueError(f"Approval request {request_id} not found")

        req = self._model_to_approval_request(model)

        if req.status != ApprovalStatus.PENDING:
            raise ValueError(f"Approval request {request_id} is in state {req.status}, expected PENDING")

        if req.is_expired():
            req.status = ApprovalStatus.EXPIRED
            self._repository.save_approval_request(req)
            self._publish_event(ApprovalExpiredEvent(request_id=request_id))
            raise ValueError(f"Approval request {request_id} has expired")

        # Enforce Separation of Duties (Self-approval prevention)
        if req.prohibit_self_approval and req.requested_by_actor_id == approver_actor_id:
            self.record_violation(
                category=ViolationCategory.SEPARATION_OF_DUTIES_VIOLATION,
                summary=f"Actor {approver_actor_id} attempted to self-approve request {request_id}",
                actor_id=approver_actor_id,
                task_id=req.task_id,
            )
            raise ValueError(f"Self-approval prohibited: Actor {approver_actor_id} requested this action")

        req.status = ApprovalStatus.APPROVED
        req.approved_by_actor_id = approver_actor_id
        self._repository.save_approval_request(req)
        self._publish_event(ApprovalGrantedEvent(request_id=request_id, approved_by_actor_id=approver_actor_id))
        return req

    def reject_request(
        self,
        request_id: str,
        rejector_actor_id: str,
        reason: str,
    ) -> GovernanceApprovalRequest:
        model = self._repository.get_approval_request(request_id)
        if not model:
            raise ValueError(f"Approval request {request_id} not found")

        req = self._model_to_approval_request(model)
        req.status = ApprovalStatus.REJECTED
        req.rejection_reason = reason
        self._repository.save_approval_request(req)
        self._publish_event(ApprovalRejectedEvent(request_id=request_id, rejected_by_actor_id=rejector_actor_id, reason=reason))
        return req

    def activate_emergency_stop(
        self,
        activated_by_actor_id: str,
        reason: str,
        scope: GovernanceScope = GovernanceScope.GLOBAL,
        scope_id: str = "GLOBAL",
    ) -> EmergencyStopState:
        stop = EmergencyStopState(
            stop_id=f"stop-{uuid.uuid4().hex[:8]}",
            scope=scope,
            scope_id=scope_id,
            activated_by_actor_id=activated_by_actor_id,
            reason=reason,
            is_active=True,
        )
        self._repository.save_emergency_stop(stop)
        self._publish_event(EmergencyStopActivatedEvent(stop_id=stop.stop_id, scope=scope.value, scope_id=scope_id, activated_by_actor_id=activated_by_actor_id, reason=reason))
        return stop

    def deactivate_emergency_stop(
        self,
        stop_id: str,
        deactivated_by_actor_id: str,
    ) -> None:
        model = self._repository._session.get(
            __import__("src.infrastructure.models.governance_model", fromlist=["EmergencyStopModel"]).EmergencyStopModel,
            stop_id,
        )
        if model:
            model.is_active = False
            self._repository._session.commit()
            self._publish_event(AutonomyResumedEvent(scope=model.scope, scope_id=model.scope_id, resumed_by_actor_id=deactivated_by_actor_id))

    def record_human_intervention(
        self,
        intervention_type: str,
        scope: GovernanceScope,
        scope_id: str,
        actor_id: str,
        reason: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> HumanIntervention:
        intervention = HumanIntervention(
            intervention_id=f"intv-{uuid.uuid4().hex[:8]}",
            intervention_type=intervention_type,
            scope=scope,
            scope_id=scope_id,
            actor_id=actor_id,
            reason=reason,
            details=details or {},
        )
        self._repository.save_intervention(intervention)
        if intervention_type == "PAUSE":
            self._publish_event(AutonomyPausedEvent(scope=scope.value, scope_id=scope_id, paused_by_actor_id=actor_id, reason=reason))
        elif intervention_type == "RESUME":
            self._publish_event(AutonomyResumedEvent(scope=scope.value, scope_id=scope_id, resumed_by_actor_id=actor_id))
        return intervention

    def apply_override(
        self,
        action_id: str,
        policy_id: str,
        actor_id: str,
        reason: str,
        previous_autonomy: AutonomyLevel,
        override_autonomy: AutonomyLevel,
    ) -> GovernanceOverride:
        override = GovernanceOverride(
            override_id=f"ovr-{uuid.uuid4().hex[:8]}",
            action_id=action_id,
            policy_id=policy_id,
            actor_id=actor_id,
            reason=reason,
            previous_autonomy_level=previous_autonomy,
            override_autonomy_level=override_autonomy,
        )
        self._repository.save_override(override)
        self._publish_event(GovernanceOverrideAppliedEvent(override_id=override.override_id, action_id=action_id, actor_id=actor_id, reason=reason))
        return override

    def record_violation(
        self,
        category: ViolationCategory,
        summary: str,
        actor_id: str,
        task_id: Optional[str] = None,
        policy_id: Optional[str] = None,
        severity: RiskLevel = RiskLevel.HIGH,
        details: Optional[Dict[str, Any]] = None,
    ) -> PolicyViolation:
        violation = PolicyViolation(
            violation_id=f"viol-{uuid.uuid4().hex[:8]}",
            category=category,
            summary=summary,
            actor_id=actor_id,
            task_id=task_id,
            policy_id=policy_id,
            severity=severity,
            details=details or {},
        )
        self._repository.save_violation(violation)
        self._publish_event(GovernanceViolationDetectedEvent(violation_id=violation.violation_id, category=category.value, actor_id=actor_id, severity=severity.value))
        return violation

    def _matches_pattern(self, text: str, pattern: str) -> bool:
        if pattern == "*" or pattern == text:
            return True
        if pattern.endswith("*"):
            prefix = pattern[:-1]
            return text.startswith(prefix)
        return False

    def _model_to_approval_request(self, m: Any) -> GovernanceApprovalRequest:
        return GovernanceApprovalRequest(
            request_id=m.id,
            action_type=m.action_type,
            action_target=m.action_target,
            requested_by_actor_id=m.requested_by_actor_id,
            requested_by_employee_id=m.requested_by_employee_id,
            requested_by_agent_id=m.requested_by_agent_id,
            task_id=m.task_id,
            project_id=m.project_id,
            risk_level=RiskLevel(m.risk_level),
            status=ApprovalStatus(m.status),
            required_approver_roles=m.required_approver_roles if isinstance(m.required_approver_roles, list) else [],
            prohibit_self_approval=m.prohibit_self_approval,
            approved_by_actor_id=m.approved_by_actor_id,
            rejection_reason=m.rejection_reason,
            payload=m.payload if isinstance(m.payload, dict) else {},
            expires_at=m.expires_at,
            created_at=m.created_at,
        )

"""
SQLAlchemy repository implementation for Phase 30 Resilience, Security, Audit & DR.
"""

from datetime import datetime, timezone, UTC
import json
from typing import Any, List, Optional

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.resilience import (
    CircuitBreaker,
    CircuitBreakerState,
    DegradationState,
    DependencyHealthSnapshot,
    ProductionReadinessItem,
    ResiliencePolicy,
    RetryPolicy,
    TimeoutPolicy,
    SecurityIncident,
    SecurityIncidentStatus,
    SecuritySeverity,
    SecuritySignal,
    AuditTrailLog,
)
from src.domain.repository import ResilienceRepositoryInterface
from src.infrastructure.models.resilience_model import (
    CircuitBreakerModel,
    ResiliencePolicyModel,
    SecurityIncidentModel,
    SecuritySignalModel,
    AuditTrailLogModel,
    DependencyHealthSnapshotModel,
    ProductionReadinessItemModel,
)


class SQLAlchemyResilienceRepository(ResilienceRepositoryInterface):

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # 1. Circuit Breakers
    async def save_circuit_breaker(self, cb: CircuitBreaker) -> CircuitBreaker:
        stmt = select(CircuitBreakerModel).where(CircuitBreakerModel.name == cb.name)
        res = await self.session.execute(stmt)
        model = res.scalar_one_or_none()

        if not model:
            model = CircuitBreakerModel(
                id=cb.id,
                name=cb.name,
                dependency_name=cb.dependency_name,
                state=cb.state.value if isinstance(cb.state, CircuitBreakerState) else str(cb.state),
                failure_threshold=cb.failure_threshold,
                recovery_time_seconds=cb.recovery_time_seconds,
                failure_count=cb.failure_count,
                success_count=cb.success_count,
                last_failure_at=cb.last_failure_at,
                last_state_change_at=cb.last_state_change_at or datetime.now(UTC),
                metadata_json=json.dumps(cb.metadata),
            )
            self.session.add(model)
        else:
            model.dependency_name = cb.dependency_name
            model.state = cb.state.value if isinstance(cb.state, CircuitBreakerState) else str(cb.state)
            model.failure_threshold = cb.failure_threshold
            model.recovery_time_seconds = cb.recovery_time_seconds
            model.failure_count = cb.failure_count
            model.success_count = cb.success_count
            model.last_failure_at = cb.last_failure_at
            model.last_state_change_at = cb.last_state_change_at or datetime.now(UTC)
            model.metadata_json = json.dumps(cb.metadata)

        await self.session.flush()
        return self._to_domain_circuit_breaker(model)

    async def get_circuit_breaker_by_name(self, name: str) -> CircuitBreaker | None:
        stmt = select(CircuitBreakerModel).where(CircuitBreakerModel.name == name)
        res = await self.session.execute(stmt)
        model = res.scalar_one_or_none()
        if not model:
            return None
        return self._to_domain_circuit_breaker(model)

    async def list_circuit_breakers(self) -> list[CircuitBreaker]:
        stmt = select(CircuitBreakerModel)
        res = await self.session.execute(stmt)
        return [self._to_domain_circuit_breaker(m) for m in res.scalars().all()]

    def _to_domain_circuit_breaker(self, model: CircuitBreakerModel) -> CircuitBreaker:
        return CircuitBreaker(
            id=model.id,
            name=model.name,
            dependency_name=model.dependency_name,
            state=CircuitBreakerState(model.state),
            failure_threshold=model.failure_threshold,
            recovery_time_seconds=model.recovery_time_seconds,
            failure_count=model.failure_count,
            success_count=model.success_count,
            last_failure_at=model.last_failure_at,
            last_state_change_at=model.last_state_change_at,
            metadata=json.loads(model.metadata_json) if model.metadata_json else {},
        )

    # 2. Resilience Policies
    async def save_resilience_policy(self, policy: ResiliencePolicy) -> ResiliencePolicy:
        stmt = select(ResiliencePolicyModel).where(ResiliencePolicyModel.target_name == policy.target_name)
        res = await self.session.execute(stmt)
        model = res.scalar_one_or_none()

        retry_dict = {
            "max_attempts": policy.retry_policy.max_attempts,
            "initial_backoff_seconds": policy.retry_policy.initial_backoff_seconds,
            "max_backoff_seconds": policy.retry_policy.max_backoff_seconds,
            "backoff_multiplier": policy.retry_policy.backoff_multiplier,
            "jitter": policy.retry_policy.jitter,
            "retryable_categories": policy.retry_policy.retryable_categories,
        }
        timeout_dict = {
            "timeout_seconds": policy.timeout_policy.timeout_seconds,
            "action_on_timeout": policy.timeout_policy.action_on_timeout,
        }

        if not model:
            model = ResiliencePolicyModel(
                id=policy.id,
                target_name=policy.target_name,
                retry_policy_json=json.dumps(retry_dict),
                timeout_policy_json=json.dumps(timeout_dict),
                circuit_breaker_enabled=policy.circuit_breaker_enabled,
                fallback_enabled=policy.fallback_enabled,
                degradation_behavior=policy.degradation_behavior.value if isinstance(policy.degradation_behavior, DegradationState) else str(policy.degradation_behavior),
                created_at=policy.created_at or datetime.now(UTC),
            )
            self.session.add(model)
        else:
            model.retry_policy_json = json.dumps(retry_dict)
            model.timeout_policy_json = json.dumps(timeout_dict)
            model.circuit_breaker_enabled = policy.circuit_breaker_enabled
            model.fallback_enabled = policy.fallback_enabled
            model.degradation_behavior = policy.degradation_behavior.value if isinstance(policy.degradation_behavior, DegradationState) else str(policy.degradation_behavior)

        await self.session.flush()
        return self._to_domain_resilience_policy(model)

    async def get_resilience_policy_by_name(self, policy_name: str) -> ResiliencePolicy | None:
        stmt = select(ResiliencePolicyModel).where(ResiliencePolicyModel.target_name == policy_name)
        res = await self.session.execute(stmt)
        model = res.scalar_one_or_none()
        if not model:
            return None
        return self._to_domain_resilience_policy(model)

    async def list_resilience_policies(self) -> list[ResiliencePolicy]:
        stmt = select(ResiliencePolicyModel)
        res = await self.session.execute(stmt)
        return [self._to_domain_resilience_policy(m) for m in res.scalars().all()]

    def _to_domain_resilience_policy(self, model: ResiliencePolicyModel) -> ResiliencePolicy:
        rp_data = json.loads(model.retry_policy_json) if model.retry_policy_json else {}
        tp_data = json.loads(model.timeout_policy_json) if model.timeout_policy_json else {}

        retry_policy = RetryPolicy(
            max_attempts=rp_data.get("max_attempts", 3),
            initial_backoff_seconds=rp_data.get("initial_backoff_seconds", 1.0),
            max_backoff_seconds=rp_data.get("max_backoff_seconds", 30.0),
            backoff_multiplier=rp_data.get("backoff_multiplier", 2.0),
            jitter=rp_data.get("jitter", True),
            retryable_categories=rp_data.get("retryable_categories", ["TIMEOUT", "NETWORK_FAILURE"]),
        )
        timeout_policy = TimeoutPolicy(
            timeout_seconds=tp_data.get("timeout_seconds", 30.0),
            action_on_timeout=tp_data.get("action_on_timeout", "CANCEL_AND_FALLBACK"),
        )

        return ResiliencePolicy(
            id=model.id,
            target_name=model.target_name,
            retry_policy=retry_policy,
            timeout_policy=timeout_policy,
            circuit_breaker_enabled=model.circuit_breaker_enabled,
            fallback_enabled=model.fallback_enabled,
            degradation_behavior=DegradationState(model.degradation_behavior),
            created_at=model.created_at,
        )

    # 3. Security Incidents & Signals
    async def save_security_incident(self, incident: SecurityIncident) -> SecurityIncident:
        stmt = select(SecurityIncidentModel).where(SecurityIncidentModel.id == incident.id)
        res = await self.session.execute(stmt)
        model = res.scalar_one_or_none()

        if not model:
            model = SecurityIncidentModel(
                id=incident.id,
                title=incident.title,
                description=incident.description,
                severity=incident.severity.value if isinstance(incident.severity, SecuritySeverity) else str(incident.severity),
                status=incident.status.value if isinstance(incident.status, SecurityIncidentStatus) else str(incident.status),
                affected_components_json=json.dumps(incident.affected_components),
                governance_approval_id=incident.governance_approval_id,
                detected_at=incident.detected_at or datetime.now(UTC),
                resolved_at=incident.resolved_at,
            )
            self.session.add(model)
        else:
            model.title = incident.title
            model.description = incident.description
            model.severity = incident.severity.value if isinstance(incident.severity, SecuritySeverity) else str(incident.severity)
            model.status = incident.status.value if isinstance(incident.status, SecurityIncidentStatus) else str(incident.status)
            model.affected_components_json = json.dumps(incident.affected_components)
            model.governance_approval_id = incident.governance_approval_id
            model.resolved_at = incident.resolved_at

        await self.session.flush()
        return self._to_domain_security_incident(model)

    async def get_security_incident_by_code(self, incident_code: str) -> SecurityIncident | None:
        stmt = select(SecurityIncidentModel).where(SecurityIncidentModel.id == incident_code)
        res = await self.session.execute(stmt)
        model = res.scalar_one_or_none()
        if not model:
            return None
        return self._to_domain_security_incident(model)

    async def list_security_incidents(self, status: str | None = None) -> list[SecurityIncident]:
        stmt = select(SecurityIncidentModel)
        if status:
            stmt = stmt.where(SecurityIncidentModel.status == status)
        res = await self.session.execute(stmt)
        return [self._to_domain_security_incident(m) for m in res.scalars().all()]

    def _to_domain_security_incident(self, model: SecurityIncidentModel) -> SecurityIncident:
        return SecurityIncident(
            id=model.id,
            title=model.title,
            description=model.description,
            severity=SecuritySeverity(model.severity),
            status=SecurityIncidentStatus(model.status),
            affected_components=json.loads(model.affected_components_json) if model.affected_components_json else [],
            governance_approval_id=model.governance_approval_id,
            detected_at=model.detected_at,
            resolved_at=model.resolved_at,
        )

    async def save_security_signal(self, signal: SecuritySignal) -> SecuritySignal:
        stmt = select(SecuritySignalModel).where(SecuritySignalModel.id == signal.id)
        res = await self.session.execute(stmt)
        model = res.scalar_one_or_none()

        if not model:
            model = SecuritySignalModel(
                id=signal.id,
                source=signal.source,
                signal_type=signal.signal_type,
                severity=signal.severity.value if isinstance(signal.severity, SecuritySeverity) else str(signal.severity),
                raw_content=signal.raw_content,
                sanitized_content=signal.sanitized_content,
                is_blocked=signal.is_blocked,
                metadata_json=json.dumps(signal.metadata),
                detected_at=signal.detected_at or datetime.now(UTC),
            )
            self.session.add(model)
        else:
            model.source = signal.source
            model.signal_type = signal.signal_type
            model.severity = signal.severity.value if isinstance(signal.severity, SecuritySeverity) else str(signal.severity)
            model.raw_content = signal.raw_content
            model.sanitized_content = signal.sanitized_content
            model.is_blocked = signal.is_blocked
            model.metadata_json = json.dumps(signal.metadata)

        await self.session.flush()
        return self._to_domain_security_signal(model)

    async def list_security_signals_for_incident(self, incident_id: str) -> list[SecuritySignal]:
        stmt = select(SecuritySignalModel)
        res = await self.session.execute(stmt)
        return [self._to_domain_security_signal(m) for m in res.scalars().all()]

    def _to_domain_security_signal(self, model: SecuritySignalModel) -> SecuritySignal:
        return SecuritySignal(
            id=model.id,
            source=model.source,
            signal_type=model.signal_type,
            severity=SecuritySeverity(model.severity),
            raw_content=model.raw_content,
            sanitized_content=model.sanitized_content,
            is_blocked=model.is_blocked,
            metadata=json.loads(model.metadata_json) if model.metadata_json else {},
            detected_at=model.detected_at,
        )

    # 4. Audit Trail Logs
    async def save_audit_log(self, audit_log: AuditTrailLog) -> AuditTrailLog:
        stmt = select(AuditTrailLogModel).where(AuditTrailLogModel.id == audit_log.id)
        res = await self.session.execute(stmt)
        model = res.scalar_one_or_none()

        if not model:
            model = AuditTrailLogModel(
                id=audit_log.id,
                timestamp=audit_log.timestamp or datetime.now(UTC),
                actor_id=audit_log.actor_id,
                actor_type=audit_log.actor_type,
                enterprise_id=audit_log.enterprise_id,
                company_id=audit_log.company_id,
                action=audit_log.action,
                resource=audit_log.resource,
                previous_state=audit_log.previous_state,
                new_state=audit_log.new_state,
                checksum=audit_log.checksum,
                correlation_id=audit_log.correlation_id,
            )
            self.session.add(model)

        await self.session.flush()
        return self._to_domain_audit_log(model)

    async def get_latest_audit_log(self) -> AuditTrailLog | None:
        stmt = select(AuditTrailLogModel).order_by(desc(AuditTrailLogModel.timestamp)).limit(1)
        res = await self.session.execute(stmt)
        model = res.scalar_one_or_none()
        if not model:
            return None
        return self._to_domain_audit_log(model)

    async def list_audit_logs(self, actor_id: str | None = None, limit: int = 100) -> list[AuditTrailLog]:
        stmt = select(AuditTrailLogModel).order_by(desc(AuditTrailLogModel.timestamp)).limit(limit)
        if actor_id:
            stmt = stmt.where(AuditTrailLogModel.actor_id == actor_id)
        res = await self.session.execute(stmt)
        return [self._to_domain_audit_log(m) for m in res.scalars().all()]

    def _to_domain_audit_log(self, model: AuditTrailLogModel) -> AuditTrailLog:
        return AuditTrailLog(
            id=model.id,
            timestamp=model.timestamp,
            actor_id=model.actor_id,
            actor_type=model.actor_type,
            enterprise_id=model.enterprise_id,
            company_id=model.company_id,
            action=model.action,
            resource=model.resource,
            previous_state=model.previous_state,
            new_state=model.new_state,
            checksum=model.checksum,
            correlation_id=model.correlation_id,
        )

    # 5. Dependency Health Snapshots
    async def save_dependency_health_snapshot(self, snapshot: DependencyHealthSnapshot) -> DependencyHealthSnapshot:
        stmt = select(DependencyHealthSnapshotModel).where(DependencyHealthSnapshotModel.id == snapshot.id)
        res = await self.session.execute(stmt)
        model = res.scalar_one_or_none()

        if not model:
            model = DependencyHealthSnapshotModel(
                id=snapshot.id,
                dependency_name=snapshot.dependency_name,
                is_available=snapshot.is_available,
                latency_ms=snapshot.latency_ms,
                error_rate_pct=snapshot.error_rate_pct,
                circuit_state=snapshot.circuit_state.value if isinstance(snapshot.circuit_state, CircuitBreakerState) else str(snapshot.circuit_state),
                last_checked_at=snapshot.last_checked_at or datetime.now(UTC),
            )
            self.session.add(model)

        await self.session.flush()
        return self._to_domain_dependency_snapshot(model)

    async def list_latest_dependency_snapshots(self) -> list[DependencyHealthSnapshot]:
        stmt = select(DependencyHealthSnapshotModel).order_by(desc(DependencyHealthSnapshotModel.last_checked_at))
        res = await self.session.execute(stmt)
        seen = set()
        unique_snapshots = []
        for model in res.scalars().all():
            if model.dependency_name not in seen:
                seen.add(model.dependency_name)
                unique_snapshots.append(self._to_domain_dependency_snapshot(model))
        return unique_snapshots

    def _to_domain_dependency_snapshot(self, model: DependencyHealthSnapshotModel) -> DependencyHealthSnapshot:
        return DependencyHealthSnapshot(
            id=model.id,
            dependency_name=model.dependency_name,
            is_available=model.is_available,
            latency_ms=model.latency_ms,
            error_rate_pct=model.error_rate_pct,
            circuit_state=CircuitBreakerState(model.circuit_state),
            last_checked_at=model.last_checked_at,
        )

    # 6. Production Readiness Items
    async def save_readiness_item(self, item: ProductionReadinessItem) -> ProductionReadinessItem:
        stmt = select(ProductionReadinessItemModel).where(ProductionReadinessItemModel.id == item.id)
        res = await self.session.execute(stmt)
        model = res.scalar_one_or_none()

        if not model:
            model = ProductionReadinessItemModel(
                id=item.id,
                domain=item.domain,
                requirement=item.requirement,
                status=item.status,
                evidence_reference=item.evidence_reference,
                tested_at=item.tested_at or datetime.now(UTC),
            )
            self.session.add(model)
        else:
            model.domain = item.domain
            model.requirement = item.requirement
            model.status = item.status
            model.evidence_reference = item.evidence_reference
            model.tested_at = item.tested_at or datetime.now(UTC)

        await self.session.flush()
        return self._to_domain_readiness_item(model)

    async def list_readiness_items(self) -> list[ProductionReadinessItem]:
        stmt = select(ProductionReadinessItemModel)
        res = await self.session.execute(stmt)
        return [self._to_domain_readiness_item(m) for m in res.scalars().all()]

    def _to_domain_readiness_item(self, model: ProductionReadinessItemModel) -> ProductionReadinessItem:
        return ProductionReadinessItem(
            id=model.id,
            domain=model.domain,
            requirement=model.requirement,
            status=model.status,
            evidence_reference=model.evidence_reference,
            tested_at=model.tested_at,
        )

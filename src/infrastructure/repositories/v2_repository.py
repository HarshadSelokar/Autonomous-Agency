"""
Persistence for the control-plane services (workflow engine, audit trail, resilience,
event outbox). Written against the synchronous Session API, like the services that use it;
on an AsyncSession run it through run_with_sync_session.
"""

import dataclasses
import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.domain.audit_v2 import AuditActionType, AuditRecordV2
from src.domain.event_v2 import OutboxMessage
from src.domain.resilience_v2 import ResilienceV2Policy, SelfHealingAction
from src.domain.workflow_v2 import (
    WorkflowDefinition,
    WorkflowInstance,
    WorkflowNode,
    WorkflowNodeType,
    WorkflowStatus,
)
from src.infrastructure.models.audit_v2_model import AuditRecordV2Model
from src.infrastructure.models.outbox_model import OutboxMessageModel
from src.infrastructure.models.resilience_v2_model import ResilienceV2PolicyModel, SelfHealingLogModel
from src.infrastructure.models.workflow_v2_model import WorkflowDefinitionModel, WorkflowInstanceModel


class V2Repository:
    def __init__(self, session: Session) -> None:
        self.session = session

    # -------------------------------------------------------------- workflows
    def save_definition(self, definition: WorkflowDefinition) -> None:
        self.session.merge(
            WorkflowDefinitionModel(
                id=definition.id,
                tenant_id=definition.tenant_id,
                name=definition.name,
                version=definition.version,
                nodes_json=[
                    {**dataclasses.asdict(node), "node_type": node.node_type.value}
                    for node in definition.nodes
                ],
                is_active=definition.is_active,
                created_at=definition.created_at,
            )
        )
        self.session.flush()

    def get_definition(self, definition_id: str) -> WorkflowDefinition | None:
        model = self.session.get(WorkflowDefinitionModel, definition_id)
        if model is None:
            return None
        return WorkflowDefinition(
            id=model.id,
            tenant_id=model.tenant_id,
            name=model.name,
            version=model.version,
            nodes=[
                WorkflowNode(**{**node, "node_type": WorkflowNodeType(node["node_type"])})
                for node in model.nodes_json or []
            ],
            is_active=model.is_active,
            created_at=model.created_at,
        )

    def save_instance(self, instance: WorkflowInstance) -> None:
        self.session.merge(
            WorkflowInstanceModel(
                id=instance.id,
                tenant_id=instance.tenant_id,
                definition_id=instance.definition_id,
                status=instance.status.value,
                current_node_id=instance.current_node_id,
                completed_nodes_json=list(instance.completed_nodes),
                execution_context_json=dict(instance.execution_context),
                created_at=instance.created_at,
                updated_at=instance.updated_at,
            )
        )
        self.session.flush()

    def get_instance(self, instance_id: str) -> WorkflowInstance | None:
        model = self.session.get(WorkflowInstanceModel, instance_id)
        if model is None:
            return None
        return WorkflowInstance(
            id=model.id,
            tenant_id=model.tenant_id,
            definition_id=model.definition_id,
            status=WorkflowStatus(model.status),
            current_node_id=model.current_node_id,
            completed_nodes=list(model.completed_nodes_json or []),
            execution_context=dict(model.execution_context_json or {}),
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    # ------------------------------------------------------------------ audit
    def save_audit_record(self, record: AuditRecordV2) -> None:
        self.session.add(
            AuditRecordV2Model(
                id=record.id,
                tenant_id=record.tenant_id,
                actor_id=record.actor_id,
                action_type=record.action_type.value,
                resource=record.resource,
                details=record.details,
                prev_hash=record.prev_hash,
                hash=record.hash,
                timestamp=record.timestamp,
            )
        )
        self.session.flush()

    def load_audit_chain(self, tenant_id: str) -> list[AuditRecordV2]:
        stmt = (
            select(AuditRecordV2Model)
            .where(AuditRecordV2Model.tenant_id == tenant_id)
            .order_by(AuditRecordV2Model.timestamp.asc())
        )
        return [
            AuditRecordV2(
                id=m.id,
                tenant_id=m.tenant_id,
                actor_id=m.actor_id,
                action_type=AuditActionType(m.action_type),
                resource=m.resource,
                details=m.details or {},
                prev_hash=m.prev_hash,
                hash=m.hash,
                timestamp=m.timestamp,
            )
            for m in self.session.execute(stmt).scalars()
        ]

    # ------------------------------------------------------------- resilience
    def get_policy(self, tenant_id: str) -> ResilienceV2Policy | None:
        model = self.session.execute(
            select(ResilienceV2PolicyModel).where(ResilienceV2PolicyModel.tenant_id == tenant_id)
        ).scalar_one_or_none()
        if model is None:
            return None
        return ResilienceV2Policy(
            id=model.id,
            tenant_id=model.tenant_id,
            max_retries=model.max_retries,
            circuit_breaker_threshold=model.circuit_breaker_threshold,
            auto_self_healing=model.auto_self_healing,
            created_at=model.created_at,
        )

    def save_policy(self, policy: ResilienceV2Policy) -> None:
        self.session.merge(
            ResilienceV2PolicyModel(
                id=policy.id,
                tenant_id=policy.tenant_id,
                max_retries=policy.max_retries,
                circuit_breaker_threshold=policy.circuit_breaker_threshold,
                auto_self_healing=policy.auto_self_healing,
                created_at=policy.created_at,
            )
        )
        self.session.flush()

    def save_self_healing_action(self, action: SelfHealingAction) -> None:
        self.session.add(
            SelfHealingLogModel(
                id=action.id,
                tenant_id=action.tenant_id,
                fault_type=action.fault_type,
                severity=action.severity.value,
                action_taken=action.action_taken.value,
                success=action.success,
                details=action.details,
                timestamp=action.timestamp,
            )
        )
        self.session.flush()

    def count_faults(self, tenant_id: str) -> int:
        return len(
            self.session.execute(
                select(SelfHealingLogModel.id).where(SelfHealingLogModel.tenant_id == tenant_id)
            ).all()
        )

    # ----------------------------------------------------------------- events
    def save_outbox_message(self, message: OutboxMessage) -> None:
        """Queue the event in the transactional outbox, which the worker publishes."""
        self.session.add(
            OutboxMessageModel(
                id=message.id,
                tenant_id=message.tenant_id,
                event_type=message.event_type,
                payload_json=json.dumps(message.payload, default=str),
                status="PENDING",
            )
        )
        self.session.flush()

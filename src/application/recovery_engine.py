"""
RecoveryEngine Application Service for Phase 10.
"""

from __future__ import annotations

import uuid
from typing import Any

from src.domain.events import (
    DomainEvent,
    RecoveryFailedEvent,
    RecoveryRequestedEvent,
    RecoveryStartedEvent,
    RecoverySucceededEvent,
    TaskEscalatedEvent,
    TaskReassignedEvent,
    TaskReworkRequestedEvent,
)
from src.domain.recovery import (
    FailureBudget,
    FailureCategory,
    FailureRecord,
    RecoveryAction,
    RecoveryStrategy,
)
from src.domain.verification import VerificationResult
from src.infrastructure.repositories.verification_repository import VerificationRepository


class RecoveryEngine:
    """Deterministic Recovery Engine managing failure classification and recovery workflows."""

    def __init__(
        self,
        repository: VerificationRepository,
        task_lifecycle_service: Any | None = None,
        employee_selector: Any | None = None,
        communication_service: Any | None = None,
        decision_service: Any | None = None,
        outbox_publisher: Any | None = None,
        default_budget: FailureBudget | None = None,
    ):
        self._repository = repository
        self._task_lifecycle_service = task_lifecycle_service
        self._employee_selector = employee_selector
        self._communication_service = communication_service
        self._decision_service = decision_service
        self._outbox_publisher = outbox_publisher
        self._budget = default_budget or FailureBudget()

    def _publish_event(self, event: DomainEvent) -> None:
        if self._outbox_publisher and hasattr(self._outbox_publisher, "publish"):
            self._outbox_publisher.publish(event)

    def classify_and_record_failure(
        self,
        task_id: str,
        category: FailureCategory,
        summary: str,
        verification_id: str | None = None,
        severity: str = "HIGH",
        details: dict[str, Any] | None = None,
        retryable: bool = True,
        agent_id: str | None = None,
        employee_id: str | None = None,
        execution_id: str | None = None,
        evidence_ids: list[str] | None = None,
    ) -> FailureRecord:
        failure_id = f"fail-{uuid.uuid4().hex[:8]}"

        # Recommend strategy based on category
        strategy_map = {
            FailureCategory.TEST_FAILURE: RecoveryStrategy.REWORK,
            FailureCategory.AGENT_FAILURE: RecoveryStrategy.REWORK,
            FailureCategory.TOOL_FAILURE: RecoveryStrategy.RETRY,
            FailureCategory.TIMEOUT: RecoveryStrategy.RETRY,
            FailureCategory.VALIDATION_FAILURE: RecoveryStrategy.REWORK,
            FailureCategory.AUTHORIZATION_FAILURE: RecoveryStrategy.ESCALATE,
            FailureCategory.POLICY_FAILURE: RecoveryStrategy.ESCALATE,
            FailureCategory.SECURITY_FAILURE: RecoveryStrategy.ESCALATE,
            FailureCategory.HUMAN_REVIEW_FAILURE: RecoveryStrategy.ESCALATE,
            FailureCategory.DEPENDENCY_FAILURE: RecoveryStrategy.SUSPEND,
        }

        recommended = strategy_map.get(category, RecoveryStrategy.REWORK)

        record = FailureRecord(
            failure_id=failure_id,
            task_id=task_id,
            verification_id=verification_id,
            category=category,
            severity=severity,
            summary=summary,
            details=details or {},
            retryable=retryable,
            recoverable=True,
            recommended_strategy=recommended,
            agent_id=agent_id,
            employee_id=employee_id,
            execution_id=execution_id,
            evidence_ids=evidence_ids or [],
        )

        self._repository.save_failure(record)
        return record

    def process_verification_failure(
        self,
        verification_result: VerificationResult,
    ) -> RecoveryAction:
        task_id = verification_result.task_id

        # Classify failure from verification result
        reason = verification_result.summary or "Verification failed"
        failed_rule_types = [c.rule_type for c in verification_result.failed_checks]

        category = FailureCategory.VALIDATION_FAILURE
        if "TEST_VERIFICATION" in failed_rule_types:
            category = FailureCategory.TEST_FAILURE
        elif "FILE_VERIFICATION" in failed_rule_types or "ARTIFACT_VERIFICATION" in failed_rule_types:
            category = FailureCategory.REQUIREMENT_FAILURE

        failure_record = self.classify_and_record_failure(
            task_id=task_id,
            verification_id=verification_result.verification_id,
            category=category,
            summary=reason,
            details={"failed_checks_count": len(verification_result.failed_checks)},
            evidence_ids=verification_result.evidence_ids,
        )

        return self.execute_recovery(failure_record.failure_id)

    def execute_recovery(self, failure_id: str) -> RecoveryAction:
        failures = self._repository.get_failures_by_task("")
        # Search failure across all or get by failure ID
        target_failure: FailureRecord | None = None

        # Fetch failure records
        # If repository supports get_failure, use it, else iterate
        stmt = select_failure(self._repository, failure_id)
        target_failure = stmt

        if not target_failure:
            raise ValueError(f"FailureRecord {failure_id} not found")

        task_id = target_failure.task_id
        past_actions = self._repository.get_recovery_actions_by_task(task_id)
        attempt_number = len(past_actions) + 1

        # Count past strategies
        rework_count = sum(1 for a in past_actions if a.strategy in ("REWORK", "REEXECUTE"))
        reassign_count = sum(1 for a in past_actions if a.strategy == "REASSIGN")
        retry_count = sum(1 for a in past_actions if a.strategy == "RETRY")

        selected_strategy = target_failure.recommended_strategy or RecoveryStrategy.REWORK

        # Check failure budget and loop protection
        if not target_failure.retryable:
            selected_strategy = RecoveryStrategy.ESCALATE

        if selected_strategy == RecoveryStrategy.RETRY and self._budget.is_retry_exhausted(retry_count):
            selected_strategy = RecoveryStrategy.REWORK

        if selected_strategy in (RecoveryStrategy.REWORK, RecoveryStrategy.REEXECUTE) and self._budget.is_rework_exhausted(rework_count):
            selected_strategy = RecoveryStrategy.REASSIGN

        if selected_strategy == RecoveryStrategy.REASSIGN and self._budget.is_reassignment_exhausted(reassign_count):
            selected_strategy = RecoveryStrategy.ESCALATE

        if attempt_number > self._budget.max_recovery_attempts:
            selected_strategy = RecoveryStrategy.ESCALATE

        action_id = f"act-{uuid.uuid4().hex[:8]}"
        self._publish_event(RecoveryRequestedEvent(recovery_action_id=action_id, failure_id=failure_id, task_id=task_id, strategy=selected_strategy.value))
        self._publish_event(RecoveryStartedEvent(recovery_action_id=action_id, task_id=task_id, strategy=selected_strategy.value))

        success = True
        details: dict[str, Any] = {"attempt_number": attempt_number}

        try:
            if selected_strategy in (RecoveryStrategy.REWORK, RecoveryStrategy.REEXECUTE, RecoveryStrategy.RETRY):
                if self._task_lifecycle_service and hasattr(self._task_lifecycle_service, "request_rework"):
                    self._task_lifecycle_service.request_rework(task_id, reason=target_failure.summary)
                self._publish_event(TaskReworkRequestedEvent(task_id=task_id, reason=target_failure.summary))

            elif selected_strategy == RecoveryStrategy.REASSIGN:
                new_employee_id = None
                if self._employee_selector and hasattr(self._employee_selector, "select_employee"):
                    new_employee_id = self._employee_selector.select_employee(task_id=task_id)
                if self._task_lifecycle_service and hasattr(self._task_lifecycle_service, "reassign_task"):
                    self._task_lifecycle_service.reassign_task(task_id, new_employee_id or "emp-backup-01")
                self._publish_event(TaskReassignedEvent(task_id=task_id, previous_employee_id=target_failure.employee_id, new_employee_id=new_employee_id or "emp-backup-01", reason=target_failure.summary))

            elif selected_strategy == RecoveryStrategy.ESCALATE:
                if self._communication_service and hasattr(self._communication_service, "send_message"):
                    self._communication_service.send_message(
                        sender_id="system",
                        recipient_id="manager",
                        content=f"ESCALATION: Task {task_id} recovery failed repeatedly. Failure: {target_failure.summary}",
                    )
                self._publish_event(TaskEscalatedEvent(task_id=task_id, objective_id="", escalated_by="SYSTEM", escalated_to="MANAGER", reason=target_failure.summary))
                details["escalated"] = True

        except Exception as e:
            success = False
            details["error"] = str(e)

        action = RecoveryAction(
            action_id=action_id,
            failure_id=failure_id,
            task_id=task_id,
            strategy=selected_strategy,
            attempt_number=attempt_number,
            success=success,
            details=details,
        )

        self._repository.save_recovery_action(action)

        if success:
            self._publish_event(RecoverySucceededEvent(recovery_action_id=action_id, task_id=task_id, strategy=selected_strategy.value))
        else:
            self._publish_event(RecoveryFailedEvent(recovery_action_id=action_id, task_id=task_id, strategy=selected_strategy.value, reason=str(details.get("error"))))

        return action


def select_failure(repository: VerificationRepository, failure_id: str) -> FailureRecord | None:
    """Helper to retrieve FailureRecord from repository."""
    model = repository._session.get(
        __import__("src.infrastructure.models.verification_model", fromlist=["FailureRecordModel"]).FailureRecordModel,
        failure_id,
    )
    if not model:
        return None
    return FailureRecord(
        failure_id=model.id,
        task_id=model.task_id,
        verification_id=model.verification_id,
        category=FailureCategory(model.category),
        severity=model.severity,
        summary=model.summary,
        details=model.details,
        retryable=model.retryable,
        recoverable=model.recoverable,
        recommended_strategy=RecoveryStrategy(model.recommended_strategy) if model.recommended_strategy else None,
        agent_id=model.agent_id,
        employee_id=model.employee_id,
        execution_id=model.execution_id,
        evidence_ids=model.evidence_ids or [],
        created_at=model.created_at,
    )

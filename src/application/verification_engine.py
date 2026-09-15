"""
VerificationEngine Application Service for Phase 10.
"""

from __future__ import annotations
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid

from src.domain.events import (
    DomainEvent,
    HumanVerificationApprovedEvent,
    HumanVerificationRejectedEvent,
    HumanVerificationRequestedEvent,
    VerificationFailedEvent,
    VerificationInconclusiveEvent,
    VerificationPassedEvent,
    VerificationRequestedEvent,
    VerificationStartedEvent,
)
from src.domain.verification import (
    ExpectedOutcome,
    EvidenceTrustLevel,
    RuleSeverity,
    VerificationCheckResult,
    VerificationEvidence,
    VerificationResult,
    VerificationRule,
    VerificationStatus,
    VerificationType,
)
from src.infrastructure.repositories.verification_repository import VerificationRepository


class VerificationEngine:
    """Generic Verification Engine responsible for evidence-based task outcome verification."""

    def __init__(self, repository: VerificationRepository, outbox_publisher: Optional[Any] = None):
        self._repository = repository
        self._outbox_publisher = outbox_publisher

    def _publish_event(self, event: DomainEvent) -> None:
        if self._outbox_publisher and hasattr(self._outbox_publisher, "publish"):
            self._outbox_publisher.publish(event)

    def define_expected_outcome(
        self,
        task_id: str,
        description: str,
        criteria: List[str],
        rules: List[VerificationRule],
        required_evidence_types: Optional[List[str]] = None,
        policy: Optional[Dict[str, Any]] = None,
    ) -> ExpectedOutcome:
        outcome = ExpectedOutcome(
            outcome_id=f"outcome-{uuid.uuid4().hex[:8]}",
            task_id=task_id,
            description=description,
            criteria=criteria,
            rules=rules,
            required_evidence_types=required_evidence_types or [],
            policy=policy or {},
        )
        self._repository.save_outcome(outcome)
        return outcome

    def add_evidence(
        self,
        source_type: str,
        source_id: str,
        task_id: Optional[str] = None,
        workspace_id: Optional[str] = None,
        agent_run_id: Optional[str] = None,
        employee_id: Optional[str] = None,
        tool_execution_id: Optional[str] = None,
        artifact_id: Optional[str] = None,
        trust_level: EvidenceTrustLevel = EvidenceTrustLevel.EXECUTED,
        checksum: Optional[str] = None,
        commit_sha: Optional[str] = None,
        artifact_version: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
    ) -> VerificationEvidence:
        evidence = VerificationEvidence(
            evidence_id=f"ev-{uuid.uuid4().hex[:8]}",
            source_type=source_type,
            source_id=source_id,
            task_id=task_id,
            workspace_id=workspace_id,
            agent_run_id=agent_run_id,
            employee_id=employee_id,
            tool_execution_id=tool_execution_id,
            artifact_id=artifact_id,
            trust_level=trust_level,
            checksum=checksum,
            commit_sha=commit_sha,
            artifact_version=artifact_version,
            payload=payload or {},
        )
        self._repository.save_evidence(evidence)
        return evidence

    def verify_task(
        self,
        task_id: str,
        evidence_ids: Optional[List[str]] = None,
    ) -> VerificationResult:
        outcome_model = self._repository.get_outcome_by_task(task_id)
        if not outcome_model:
            # If no explicit outcome defined, create default pass-through outcome
            outcome = self.define_expected_outcome(
                task_id=task_id,
                description="Default outcome",
                criteria=["Task completed"],
                rules=[],
            )
        else:
            # Reconstruct domain outcome from model
            rules = [
                VerificationRule(
                    rule_id=r["rule_id"],
                    rule_type=VerificationType(r["rule_type"]),
                    name=r["name"],
                    description=r["description"],
                    target=r["target"],
                    expected_condition=r["expected_condition"],
                    severity=RuleSeverity(r.get("severity", "CRITICAL")),
                    retryable=r.get("retryable", True),
                    requires_human=r.get("requires_human", False),
                    min_trust_level=EvidenceTrustLevel(r.get("min_trust_level", "EXECUTED")),
                    operator=r.get("operator", "AND"),
                )
                for r in outcome_model.rules_data
            ]
            outcome = ExpectedOutcome(
                outcome_id=outcome_model.id,
                task_id=outcome_model.task_id,
                description=outcome_model.description,
                criteria=outcome_model.criteria,
                rules=rules,
                required_evidence_types=outcome_model.required_evidence_types,
                policy=outcome_model.policy,
            )

        verification_id = f"verif-{uuid.uuid4().hex[:8]}"
        self._publish_event(VerificationRequestedEvent(verification_id=verification_id, task_id=task_id, outcome_id=outcome.outcome_id))
        self._publish_event(VerificationStartedEvent(verification_id=verification_id, task_id=task_id))

        # Collect evidence for task
        collected_evidence_models = self._repository.get_evidence_by_task(task_id)
        evidence_map: Dict[str, VerificationEvidence] = {}

        for em in collected_evidence_models:
            evidence_map[em.id] = VerificationEvidence(
                evidence_id=em.id,
                source_type=em.source_type,
                source_id=em.source_id,
                task_id=em.task_id,
                workspace_id=em.workspace_id,
                agent_run_id=em.agent_run_id,
                employee_id=em.employee_id,
                tool_execution_id=em.tool_execution_id,
                artifact_id=em.artifact_id,
                trust_level=EvidenceTrustLevel(em.trust_level),
                checksum=em.checksum,
                commit_sha=em.commit_sha,
                artifact_version=em.artifact_version,
                payload=em.payload,
                created_at=em.created_at,
            )

        passed_checks: List[VerificationCheckResult] = []
        failed_checks: List[VerificationCheckResult] = []
        used_evidence_ids: List[str] = list(evidence_map.keys())

        # Evaluate each rule
        for rule in outcome.rules:
            check_result = self._evaluate_rule(rule, list(evidence_map.values()), task_id)
            if check_result.passed:
                passed_checks.append(check_result)
            else:
                failed_checks.append(check_result)

        # Check if human verification required
        requires_human = any(r.requires_human for r in outcome.rules) or outcome.policy.get("requires_human_approval", False)

        if failed_checks:
            has_critical_failure = any(c.severity == RuleSeverity.CRITICAL for c in failed_checks)
            status = VerificationStatus.FAILED if has_critical_failure else VerificationStatus.INCONCLUSIVE
            recommended_recovery = "REWORK" if any(r.retryable for r in outcome.rules) else "ESCALATE"
            summary = f"Verification failed with {len(failed_checks)} failed check(s): {failed_checks[0].reason}"
        elif requires_human:
            status = VerificationStatus.INCONCLUSIVE
            recommended_recovery = None
            summary = "Automatic checks passed. Pending human verification."
            self._publish_event(HumanVerificationRequestedEvent(verification_id=verification_id, task_id=task_id, reason="Policy requires human review"))
        else:
            status = VerificationStatus.VERIFIED
            recommended_recovery = None
            summary = f"All {len(passed_checks)} verification checks passed successfully."

        result = VerificationResult(
            verification_id=verification_id,
            task_id=task_id,
            outcome_id=outcome.outcome_id,
            status=status,
            passed_checks=passed_checks,
            failed_checks=failed_checks,
            evidence_ids=used_evidence_ids,
            summary=summary,
            recommended_recovery=recommended_recovery,
        )

        self._repository.save_verification(result)

        if status == VerificationStatus.VERIFIED:
            self._publish_event(VerificationPassedEvent(verification_id=verification_id, task_id=task_id, evidence_count=len(used_evidence_ids)))
        elif status == VerificationStatus.FAILED:
            self._publish_event(VerificationFailedEvent(verification_id=verification_id, task_id=task_id, failed_check_count=len(failed_checks), recommended_recovery=recommended_recovery or "REWORK"))
        else:
            self._publish_event(VerificationInconclusiveEvent(verification_id=verification_id, task_id=task_id, reason=summary))

        return result

    def override_verification(
        self,
        verification_id: str,
        actor_id: str,
        reason: str,
        waive: bool = False,
    ) -> VerificationResult:
        model = self._repository.get_verification(verification_id)
        if not model:
            raise ValueError(f"Verification {verification_id} not found")

        status = VerificationStatus.WAIVED if waive else VerificationStatus.VERIFIED
        result = VerificationResult(
            verification_id=model.id,
            task_id=model.task_id,
            outcome_id=model.outcome_id,
            status=status,
            summary=f"Human override by {actor_id}: {reason}",
            is_human_verified=True,
            verified_by_actor_id=actor_id,
            override_reason=reason,
            evidence_ids=model.evidence_ids or [],
        )

        self._repository.save_verification(result)
        self._publish_event(HumanVerificationApprovedEvent(verification_id=verification_id, task_id=model.task_id, approved_by_actor_id=actor_id, reason=reason))
        return result

    def _evaluate_rule(
        self,
        rule: VerificationRule,
        evidences: List[VerificationEvidence],
        task_id: str,
    ) -> VerificationCheckResult:
        check_id = f"chk-{uuid.uuid4().hex[:8]}"

        # Filter evidence matching minimum trust level
        valid_evidences = [e for e in evidences if e.is_trusted_at_least(rule.min_trust_level)]

        if rule.rule_type == VerificationType.FILE_VERIFICATION:
            # Check if file execution/existence evidence exists
            file_ev = [e for e in valid_evidences if e.payload.get("file") == rule.target or e.payload.get("path") == rule.target]
            if not file_ev:
                return VerificationCheckResult(
                    check_id=check_id,
                    rule_id=rule.rule_id,
                    rule_name=rule.name,
                    rule_type=rule.rule_type,
                    severity=rule.severity,
                    passed=False,
                    reason=f"No trusted evidence found for file target '{rule.target}'",
                )
            exists = any(e.payload.get("exists", True) for e in file_ev)
            expected_exists = rule.expected_condition.get("exists", True)
            passed = (exists == expected_exists)
            return VerificationCheckResult(
                check_id=check_id,
                rule_id=rule.rule_id,
                rule_name=rule.name,
                rule_type=rule.rule_type,
                severity=rule.severity,
                passed=passed,
                evidence_ids=[e.evidence_id for e in file_ev],
                reason="File exists as expected" if passed else f"File target '{rule.target}' condition mismatch",
            )

        if rule.rule_type == VerificationType.TEST_VERIFICATION:
            test_ev = [e for e in valid_evidences if e.source_type == "TestRun"]
            if not test_ev:
                return VerificationCheckResult(
                    check_id=check_id,
                    rule_id=rule.rule_id,
                    rule_name=rule.name,
                    rule_type=rule.rule_type,
                    severity=rule.severity,
                    passed=False,
                    reason="No test run evidence recorded",
                )
            # Freshness: Sort evidence by created_at desc to inspect the latest test run
            test_ev.sort(key=lambda x: x.created_at, reverse=True)
            latest_test = test_ev[0]
            passed = (latest_test.payload.get("exit_code", 1) == rule.expected_condition.get("exit_code", 0) and latest_test.payload.get("failed_count", 0) == 0)
            return VerificationCheckResult(
                check_id=check_id,
                rule_id=rule.rule_id,
                rule_name=rule.name,
                rule_type=rule.rule_type,
                severity=rule.severity,
                passed=passed,
                evidence_ids=[latest_test.evidence_id],
                reason="Latest test run passed successfully" if passed else f"Latest test run failed with exit code {latest_test.payload.get('exit_code')}",
            )

        elif rule.rule_type == VerificationType.HUMAN_VERIFICATION:
            human_ev = [e for e in valid_evidences if e.source_type == "HumanReview" or e.payload.get("is_human") is True]
            approved = any(e.payload.get("approved") is True for e in human_ev)
            return VerificationCheckResult(
                check_id=check_id,
                rule_id=rule.rule_id,
                rule_name=rule.name,
                rule_type=rule.rule_type,
                severity=RuleSeverity.WARNING if not approved else RuleSeverity.CRITICAL,
                passed=approved,
                evidence_ids=[e.evidence_id for e in human_ev],
                reason="Human verification approved" if approved else "Pending authorized human verification",
            )

        elif rule.rule_type == VerificationType.ARTIFACT_VERIFICATION:
            art_ev = [e for e in valid_evidences if e.source_type == "Artifact"]
            if not art_ev:
                return VerificationCheckResult(
                    check_id=check_id,
                    rule_id=rule.rule_id,
                    rule_name=rule.name,
                    rule_type=rule.rule_type,
                    severity=rule.severity,
                    passed=False,
                    reason=f"No artifact evidence found for '{rule.target}'",
                )
            passed = any(e.payload.get("name") == rule.target or e.artifact_id == rule.target for e in art_ev)
            return VerificationCheckResult(
                check_id=check_id,
                rule_id=rule.rule_id,
                rule_name=rule.name,
                rule_type=rule.rule_type,
                severity=rule.severity,
                passed=passed,
                evidence_ids=[e.evidence_id for e in art_ev],
                reason=f"Artifact '{rule.target}' verified" if passed else f"Artifact '{rule.target}' missing",
            )

        # Default fallback rule evaluation
        matching_ev = [e for e in valid_evidences if e.payload.get("status") == "APPROVED" or e.payload.get("success") is True or e.payload.get("passed") is True]
        passed = len(matching_ev) > 0 or len(rule.expected_condition) == 0
        return VerificationCheckResult(
            check_id=check_id,
            rule_id=rule.rule_id,
            rule_name=rule.name,
            rule_type=rule.rule_type,
            severity=rule.severity,
            passed=passed,
            evidence_ids=[e.evidence_id for e in matching_ev],
            reason="Rule satisfied" if passed else f"Rule criteria not met for '{rule.name}'",
        )

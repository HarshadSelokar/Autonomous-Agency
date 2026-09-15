"""
Unit tests for Verification Domain Model (Phase 10).
"""

import pytest
from datetime import datetime, timezone
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


def test_evidence_trust_hierarchy():
    e1 = VerificationEvidence(
        evidence_id="e1",
        source_type="AgentRun",
        source_id="r1",
        trust_level=EvidenceTrustLevel.UNTRUSTED,
    )
    e2 = VerificationEvidence(
        evidence_id="e2",
        source_type="ToolExecution",
        source_id="t1",
        trust_level=EvidenceTrustLevel.EXECUTED,
    )
    e3 = VerificationEvidence(
        evidence_id="e3",
        source_type="IndependentVerifier",
        source_id="iv1",
        trust_level=EvidenceTrustLevel.AUTHORITATIVE,
    )

    assert e1.is_trusted_at_least(EvidenceTrustLevel.UNTRUSTED)
    assert not e1.is_trusted_at_least(EvidenceTrustLevel.EXECUTED)
    assert e2.is_trusted_at_least(EvidenceTrustLevel.EXECUTED)
    assert not e2.is_trusted_at_least(EvidenceTrustLevel.AUTHORITATIVE)
    assert e3.is_trusted_at_least(EvidenceTrustLevel.EXECUTED)
    assert e3.is_trusted_at_least(EvidenceTrustLevel.AUTHORITATIVE)


def test_verification_rule_creation():
    rule = VerificationRule(
        rule_id="r1",
        rule_type=VerificationType.TEST_VERIFICATION,
        name="All unit tests pass",
        description="Run pytest suite",
        target="pytest tests/",
        expected_condition={"exit_code": 0},
        severity=RuleSeverity.CRITICAL,
    )
    assert rule.rule_id == "r1"
    assert rule.rule_type == VerificationType.TEST_VERIFICATION
    assert rule.severity == RuleSeverity.CRITICAL
    assert rule.expected_condition["exit_code"] == 0


def test_verification_result_is_verified():
    res_passed = VerificationResult(
        verification_id="v1",
        task_id="t1",
        outcome_id="o1",
        status=VerificationStatus.VERIFIED,
    )
    assert res_passed.is_verified

    res_failed = VerificationResult(
        verification_id="v2",
        task_id="t1",
        outcome_id="o1",
        status=VerificationStatus.FAILED,
    )
    assert not res_failed.is_verified

    res_waived = VerificationResult(
        verification_id="v3",
        task_id="t1",
        outcome_id="o1",
        status=VerificationStatus.WAIVED,
    )
    assert res_waived.is_verified

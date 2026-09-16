"""
Unit tests for VerificationEngine (Phase 10).
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.application.verification_engine import VerificationEngine
from src.domain.verification import (
    EvidenceTrustLevel,
    RuleSeverity,
    VerificationRule,
    VerificationStatus,
    VerificationType,
)
from src.infrastructure.database import Base
from src.infrastructure.repositories.verification_repository import VerificationRepository


@pytest.fixture
def verification_engine():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    repo = VerificationRepository(session)
    return VerificationEngine(repository=repo)


def test_verification_engine_pass_flow(verification_engine):
    task_id = "task-pass-100"

    # Define rules
    rule1 = VerificationRule(
        rule_id="r1",
        rule_type=VerificationType.FILE_VERIFICATION,
        name="Source File Exists",
        description="Verify src/app.py exists",
        target="src/app.py",
        expected_condition={"exists": True},
        severity=RuleSeverity.CRITICAL,
    )
    rule2 = VerificationRule(
        rule_id="r2",
        rule_type=VerificationType.TEST_VERIFICATION,
        name="Unit Tests Pass",
        description="Verify tests exit with code 0",
        target="pytest",
        expected_condition={"exit_code": 0},
        severity=RuleSeverity.CRITICAL,
    )

    verification_engine.define_expected_outcome(
        task_id=task_id,
        description="Build App Feature",
        criteria=["file exists", "tests pass"],
        rules=[rule1, rule2],
    )

    # Add trusted evidence
    verification_engine.add_evidence(
        source_type="ToolExecution",
        source_id="te-1",
        task_id=task_id,
        trust_level=EvidenceTrustLevel.EXECUTED,
        payload={"file": "src/app.py", "exists": True},
    )
    verification_engine.add_evidence(
        source_type="TestRun",
        source_id="tr-1",
        task_id=task_id,
        trust_level=EvidenceTrustLevel.EXECUTED,
        payload={"exit_code": 0, "failed_count": 0},
    )

    # Execute verification
    result = verification_engine.verify_task(task_id=task_id)

    assert result.status == VerificationStatus.VERIFIED
    assert len(result.passed_checks) == 2
    assert len(result.failed_checks) == 0
    assert result.is_verified


def test_verification_engine_fail_flow(verification_engine):
    task_id = "task-fail-200"

    rule = VerificationRule(
        rule_id="r1",
        rule_type=VerificationType.TEST_VERIFICATION,
        name="Unit Tests Pass",
        description="Verify tests exit with code 0",
        target="pytest",
        expected_condition={"exit_code": 0},
        severity=RuleSeverity.CRITICAL,
    )

    verification_engine.define_expected_outcome(
        task_id=task_id,
        description="Failing Task",
        criteria=["tests pass"],
        rules=[rule],
    )

    # Evidence shows failing test
    verification_engine.add_evidence(
        source_type="TestRun",
        source_id="tr-2",
        task_id=task_id,
        trust_level=EvidenceTrustLevel.EXECUTED,
        payload={"exit_code": 1, "failed_count": 3},
    )

    result = verification_engine.verify_task(task_id=task_id)

    assert result.status == VerificationStatus.FAILED
    assert len(result.failed_checks) == 1
    assert result.recommended_recovery == "REWORK"
    assert not result.is_verified


def test_human_override_flow(verification_engine):
    task_id = "task-override-300"
    rule = VerificationRule(
        rule_id="r1",
        rule_type=VerificationType.FILE_VERIFICATION,
        name="Check File",
        description="Check file",
        target="missing.py",
        expected_condition={"exists": True},
    )

    verification_engine.define_expected_outcome(task_id=task_id, description="Missing file task", criteria=[], rules=[rule])
    res1 = verification_engine.verify_task(task_id=task_id)
    assert res1.status == VerificationStatus.FAILED

    # Authorized manager overrides failed verification
    res_override = verification_engine.override_verification(
        verification_id=res1.verification_id,
        actor_id="emp-manager-001",
        reason="File location approved under alternative path",
        waive=True,
    )

    assert res_override.status == VerificationStatus.WAIVED
    assert res_override.is_human_verified
    assert res_override.verified_by_actor_id == "emp-manager-001"
    assert res_override.is_verified

"""
Security & Provenance Tests for Phase 10 Verification Engine.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

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
import src.infrastructure.models  # noqa: F401


@pytest.fixture
def verification_engine():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    repo = VerificationRepository(Session())
    return VerificationEngine(repository=repo)


def test_agent_claim_cannot_self_verify(verification_engine):
    task_id = "task-sec-100"

    rule = VerificationRule(
        rule_id="r1",
        rule_type=VerificationType.TEST_VERIFICATION,
        name="Tests Pass",
        description="Verify tests",
        target="pytest",
        expected_condition={"exit_code": 0},
        min_trust_level=EvidenceTrustLevel.EXECUTED,
    )
    verification_engine.define_expected_outcome(task_id=task_id, description="Task", criteria=[], rules=[rule])

    # Agent provides UNTRUSTED text claim ("I ran the tests and they passed!")
    verification_engine.add_evidence(
        source_type="AgentRun",
        source_id="run-1",
        task_id=task_id,
        trust_level=EvidenceTrustLevel.UNTRUSTED,
        payload={"claim": "Tests passed successfully", "exit_code": 0},
    )

    # Verification MUST fail because UNTRUSTED evidence does not meet min_trust_level EXECUTED
    result = verification_engine.verify_task(task_id=task_id)
    assert result.status == VerificationStatus.FAILED
    assert not result.is_verified


def test_cross_task_evidence_isolation(verification_engine):
    task_a = "task-sec-A"
    task_b = "task-sec-B"

    rule = VerificationRule(
        rule_id="r1",
        rule_type=VerificationType.FILE_VERIFICATION,
        name="Source Check",
        description="Check file",
        target="main.py",
        expected_condition={"exists": True},
        min_trust_level=EvidenceTrustLevel.EXECUTED,
    )

    verification_engine.define_expected_outcome(task_id=task_a, description="Task A", criteria=[], rules=[rule])

    # Add evidence belonging ONLY to Task B
    verification_engine.add_evidence(
        source_type="ToolExecution",
        source_id="te-B",
        task_id=task_b,
        trust_level=EvidenceTrustLevel.EXECUTED,
        payload={"file": "main.py", "exists": True},
    )

    # Verifying Task A must fail because evidence is isolated to Task B
    result_a = verification_engine.verify_task(task_id=task_a)
    assert result_a.status == VerificationStatus.FAILED
    assert not result_a.is_verified


def test_audited_human_override_tracking(verification_engine):
    task_id = "task-sec-override"
    rule = VerificationRule(
        rule_id="r1",
        rule_type=VerificationType.FILE_VERIFICATION,
        name="Check file",
        description="Check file",
        target="missing.py",
        expected_condition={"exists": True},
    )

    verification_engine.define_expected_outcome(task_id=task_id, description="Task", criteria=[], rules=[rule])
    res_failed = verification_engine.verify_task(task_id=task_id)
    assert res_failed.status == VerificationStatus.FAILED

    # Human override
    res_override = verification_engine.override_verification(
        verification_id=res_failed.verification_id,
        actor_id="usr-sec-officer-99",
        reason="Verified via manual inspection",
        waive=False,
    )

    assert res_override.status == VerificationStatus.VERIFIED
    assert res_override.is_human_verified
    assert res_override.verified_by_actor_id == "usr-sec-officer-99"
    assert res_override.override_reason == "Verified via manual inspection"

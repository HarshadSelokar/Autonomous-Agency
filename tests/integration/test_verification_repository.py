"""
Integration tests for VerificationRepository (Phase 10).
"""

import pytest
import uuid
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.infrastructure.database import Base
from src.infrastructure.repositories.verification_repository import VerificationRepository
from src.domain.verification import (
    ExpectedOutcome,
    EvidenceTrustLevel,
    RuleSeverity,
    VerificationEvidence,
    VerificationResult,
    VerificationRule,
    VerificationStatus,
    VerificationType,
)
from src.domain.recovery import (
    FailureCategory,
    FailureRecord,
    RecoveryAction,
    RecoveryStrategy,
)


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_verification_repository_outcomes_and_verifications(db_session):
    repo = VerificationRepository(db_session)

    # 1. Outcome
    rule = VerificationRule(
        rule_id="r1",
        rule_type=VerificationType.FILE_VERIFICATION,
        name="File check",
        description="Verify src/main.py exists",
        target="src/main.py",
        expected_condition={"exists": True},
    )
    outcome = ExpectedOutcome(
        outcome_id="o1",
        task_id="t1",
        description="Must generate main.py",
        criteria=["file exists"],
        rules=[rule],
    )
    saved_outcome = repo.save_outcome(outcome)
    assert saved_outcome.outcome_id == "o1"

    fetched_outcome = repo.get_outcome("o1")
    assert fetched_outcome is not None
    assert fetched_outcome.task_id == "t1"

    # 2. Evidence
    evidence = VerificationEvidence(
        evidence_id="e1",
        source_type="ToolExecution",
        source_id="te1",
        task_id="t1",
        trust_level=EvidenceTrustLevel.EXECUTED,
        payload={"file": "src/main.py", "exists": True},
    )
    repo.save_evidence(evidence)
    fetched_evidence = repo.get_evidence("e1")
    assert fetched_evidence is not None
    assert fetched_evidence.trust_level == "EXECUTED"

    # 3. Verification Result
    result = VerificationResult(
        verification_id="v1",
        task_id="t1",
        outcome_id="o1",
        status=VerificationStatus.VERIFIED,
        summary="All checks passed",
        evidence_ids=["e1"],
    )
    repo.save_verification(result)
    fetched_v = repo.get_verification("v1")
    assert fetched_v is not None
    assert fetched_v.status == "VERIFIED"

    # 4. Failure Record
    failure = FailureRecord(
        failure_id="f1",
        task_id="t1",
        verification_id="v1",
        category=FailureCategory.TEST_FAILURE,
        severity="HIGH",
        summary="Pytest exit code 1",
        recommended_strategy=RecoveryStrategy.REWORK,
    )
    repo.save_failure(failure)
    failures = repo.get_failures_by_task("t1")
    assert len(failures) == 1
    assert failures[0].category == "TEST_FAILURE"

    # 5. Recovery Action
    action = RecoveryAction(
        action_id="ra1",
        failure_id="f1",
        task_id="t1",
        strategy=RecoveryStrategy.REWORK,
        attempt_number=1,
        success=True,
    )
    repo.save_recovery_action(action)
    actions = repo.get_recovery_actions_by_task("t1")
    assert len(actions) == 1
    assert actions[0].strategy == "REWORK"

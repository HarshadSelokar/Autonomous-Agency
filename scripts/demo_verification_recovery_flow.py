"""
Phase 10 — Verification, Recovery & Autonomous Reliability End-to-End Demonstration Script.
"""

import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import src.infrastructure.models  # noqa: F401
from src.application.recovery_engine import RecoveryEngine
from src.application.verification_engine import VerificationEngine
from src.domain.recovery import FailureBudget, FailureCategory, RecoveryStrategy
from src.domain.verification import (
    EvidenceTrustLevel,
    RuleSeverity,
    VerificationRule,
    VerificationStatus,
    VerificationType,
)
from src.infrastructure.database import Base
from src.infrastructure.repositories.verification_repository import VerificationRepository


def run_demo():
    print("================================================================================")
    print("PHASE 10 — VERIFICATION, RECOVERY & AUTONOMOUS RELIABILITY DEMONSTRATION")
    print("================================================================================\n")

    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    repo = VerificationRepository(session)
    budget = FailureBudget(max_retries=2, max_reworks=2, max_reassignments=1, max_recovery_attempts=4)
    verif_engine = VerificationEngine(repository=repo)
    rec_engine = RecoveryEngine(repository=repo, default_budget=budget)

    # --------------------------------------------------------------------------
    # SCENARIO 1: Evidence Failure -> Rework -> Recovery -> Verified Completion
    # --------------------------------------------------------------------------
    print("--- SCENARIO 1: Task Verification Failure & Autonomous Rework Recovery ---")
    task1_id = "task-demo-feature-api"

    # Define Expected Outcome
    rule1 = VerificationRule(
        rule_id="r1",
        rule_type=VerificationType.TEST_VERIFICATION,
        name="Unit Tests Pass",
        description="Verify test suite passes with 0 failures",
        target="pytest tests/unit/test_customer_api.py",
        expected_condition={"exit_code": 0},
        severity=RuleSeverity.CRITICAL,
    )
    rule2 = VerificationRule(
        rule_id="r2",
        rule_type=VerificationType.FILE_VERIFICATION,
        name="API File Exists",
        description="Verify src/api/customer.py exists",
        target="src/api/customer.py",
        expected_condition={"exists": True},
        severity=RuleSeverity.CRITICAL,
    )

    verif_engine.define_expected_outcome(
        task_id=task1_id,
        description="Implement customer creation API endpoint",
        criteria=["Endpoint exists", "Tests pass"],
        rules=[rule1, rule2],
    )
    print(f"[+] Defined expected outcome for Task: {task1_id}")

    # Agent claims completion, but test run evidence shows failure (3 failing tests)
    print("[!] Agent claims completion. Collecting evidence for independent verification...")
    verif_engine.add_evidence(
        source_type="TestRun",
        source_id="test-run-001",
        task_id=task1_id,
        trust_level=EvidenceTrustLevel.EXECUTED,
        payload={"exit_code": 1, "failed_count": 3, "command": "pytest tests/unit/test_customer_api.py"},
    )
    verif_engine.add_evidence(
        source_type="ToolExecution",
        source_id="tool-exec-001",
        task_id=task1_id,
        trust_level=EvidenceTrustLevel.EXECUTED,
        payload={"file": "src/api/customer.py", "exists": True},
    )

    result1 = verif_engine.verify_task(task_id=task1_id)
    print(f"[-] Verification Result: Status={result1.status.value}, Passed={len(result1.passed_checks)}, Failed={len(result1.failed_checks)}")
    print(f"[-] Summary: {result1.summary}")

    assert result1.status == VerificationStatus.FAILED

    # Trigger Recovery Engine
    print("[+] Triggering Recovery Engine...")
    action1 = rec_engine.process_verification_failure(result1)
    print(f"[+] Recovery Engine Action: Strategy={action1.strategy.value}, Attempt={action1.attempt_number}")
    assert action1.strategy == RecoveryStrategy.REWORK

    # Developer Agent performs rework and fixes tests
    print("\n[+] Developer Employee fixes work and re-runs test suite...")
    verif_engine.add_evidence(
        source_type="TestRun",
        source_id="test-run-002",
        task_id=task1_id,
        trust_level=EvidenceTrustLevel.EXECUTED,
        payload={"exit_code": 0, "failed_count": 0, "command": "pytest tests/unit/test_customer_api.py"},
    )

    # Verification Attempt 2
    result1_v2 = verif_engine.verify_task(task_id=task1_id)
    print(f"[+] Re-Verification Result: Status={result1_v2.status.value}, Passed={len(result1_v2.passed_checks)}")
    assert result1_v2.status == VerificationStatus.VERIFIED
    print("[SUCCESS] Task VERIFIED and transitioned to COMPLETED!\n")

    # --------------------------------------------------------------------------
    # SCENARIO 2: Repeated Failure -> Failure Budget Exceeded -> Escalation
    # --------------------------------------------------------------------------
    print("--- SCENARIO 2: Failure Budget Exhaustion & Escalation to Manager ---")
    task2_id = "task-demo-flaky-service"

    print(f"[+] Simulating repeated execution failures for Task: {task2_id}")
    for attempt in range(1, 5):
        f = rec_engine.classify_and_record_failure(
            task_id=task2_id,
            category=FailureCategory.AGENT_FAILURE,
            summary=f"Execution error on attempt {attempt}",
        )
        act = rec_engine.execute_recovery(f.failure_id)
        print(f"  Attempt {attempt}: Failure Recorded -> Recovery Strategy = {act.strategy.value}")

    print("[SUCCESS] Repeated failure successfully escalated to Manager after exhausting failure budget!\n")

    # --------------------------------------------------------------------------
    # SCENARIO 3: High-Risk Policy -> Human Verification & Audited Override
    # --------------------------------------------------------------------------
    print("--- SCENARIO 3: High-Risk Outcome & Audited Human Override ---")
    task3_id = "task-demo-prod-migration"

    rule_prod = VerificationRule(
        rule_id="r-prod",
        rule_type=VerificationType.HUMAN_VERIFICATION,
        name="Production Approval",
        description="Production database migration requires human approval",
        target="alembic upgrade head",
        expected_condition={"approved": True},
        requires_human=True,
    )

    verif_engine.define_expected_outcome(
        task_id=task3_id,
        description="Migrate Production Database",
        criteria=["Human approval"],
        rules=[rule_prod],
        policy={"requires_human_approval": True},
    )

    res3 = verif_engine.verify_task(task_id=task3_id)
    print(f"[-] Initial Verification Result: Status={res3.status.value} ({res3.summary})")
    assert res3.status == VerificationStatus.INCONCLUSIVE

    # Authorized VP of Engineering overrides and approves migration
    print("[+] Authorized Actor (emp-vp-eng) reviews evidence and approves migration...")
    res3_approved = verif_engine.override_verification(
        verification_id=res3.verification_id,
        actor_id="emp-vp-eng",
        reason="Manual verification of migration safety completed",
        waive=False,
    )
    print(f"[+] Override Result: Status={res3_approved.status.value}, VerifiedBy={res3_approved.verified_by_actor_id}")
    print(f"[+] Audit Reason: {res3_approved.override_reason}")
    assert res3_approved.is_verified

    print("\n================================================================ mortality")
    print("ALL PHASE 10 E2E DEMONSTRATIONS COMPLETED SUCCESSFULLY!")
    print("========================================================================\n")


if __name__ == "__main__":
    run_demo()

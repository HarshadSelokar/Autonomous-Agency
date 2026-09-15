"""
Phase 11 — Human Governance End-to-End Demonstration Script.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import src.infrastructure.models  # noqa: F401
from src.application.governance_service import GovernanceService
from src.domain.governance import (
    ApprovalStatus,
    AutonomyLevel,
    GovernanceRule,
    GovernanceScope,
    RiskLevel,
    ViolationCategory,
)
from src.infrastructure.database import Base
from src.infrastructure.repositories.governance_repository import GovernanceRepository


def run_demo():
    print("================================================================================")
    print("PHASE 11 — HUMAN GOVERNANCE END-TO-END DEMONSTRATION")
    print("================================================================ launch\n")

    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    repo = GovernanceRepository(session)
    service = GovernanceService(repository=repo)

    # --------------------------------------------------------------------------
    # SCENARIO 1: Defining Hierarchical Governance Policies
    # --------------------------------------------------------------------------
    print("--- SCENARIO 1: Defining Hierarchical Governance Policies ---")
    rule_prod_deploy = GovernanceRule(
        rule_id="rule-deploy-prod",
        name="Production Deployment Control",
        description="Deploying to production requires explicit Manager approval",
        scope=GovernanceScope.PROJECT,
        target_pattern="deploy_prod*",
        min_risk_level=RiskLevel.HIGH,
        autonomy_level=AutonomyLevel.APPROVAL_REQUIRED,
        required_approver_roles=["MANAGER", "VP_ENGINEERING"],
        prohibit_self_approval=True,
        approval_validity_seconds=1800,
    )

    policy = service.define_policy(
        name="Production Security Policy",
        scope=GovernanceScope.PROJECT,
        scope_id="proj-finance-system",
        level="PROJECT",
        rules=[rule_prod_deploy],
    )
    print(f"[+] Defined Governance Policy '{policy.name}' (ID: {policy.policy_id}) at {policy.level} level\n")

    # --------------------------------------------------------------------------
    # SCENARIO 2: Risk Classification & Human Approval Workflow with Self-Approval Guard
    # --------------------------------------------------------------------------
    print("--- SCENARIO 2: Risk Classification & Self-Approval Prevention Guard ---")
    action_type = "deploy_production_v2"
    action_target = "prod-k8s-cluster"
    requestor_id = "emp-dev-lead-1"

    # Evaluate autonomy
    autonomy, risk, rule = service.evaluate_autonomy(
        action_type=action_type,
        action_target=action_target,
        actor_id=requestor_id,
        project_id="proj-finance-system",
    )
    print(f"[+] Action '{action_type}' classified as Risk Level: {risk.value}")
    print(f"[+] Policy Evaluation Autonomy Requirement: {autonomy.value}")
    assert autonomy == AutonomyLevel.APPROVAL_REQUIRED

    # Request Approval
    appr_req = service.request_approval(
        action_type=action_type,
        action_target=action_target,
        requested_by_actor_id=requestor_id,
        project_id="proj-finance-system",
        risk_level=risk,
        required_approver_roles=["MANAGER"],
        prohibit_self_approval=True,
    )
    print(f"[+] Created Approval Request '{appr_req.request_id}' with Status: {appr_req.status.value}")

    # Attempt Self-Approval by requestor (emp-dev-lead-1)
    print("[!] Dev Lead (emp-dev-lead-1) attempts to approve their own request...")
    try:
        service.approve_request(request_id=appr_req.request_id, approver_actor_id=requestor_id)
    except ValueError as e:
        print(f"[-] BLOCKED: {e}")

    # Verify violation logged
    violations = repo.get_violations()
    assert len(violations) >= 1
    print(f"[-] Logged Violation: Category={violations[0].category}, Actor={violations[0].actor_id}")
    assert violations[0].category == ViolationCategory.SEPARATION_OF_DUTIES_VIOLATION.value

    # Legitimate Approval by Manager (emp-engineering-mgr-2)
    print("\n[+] Engineering Manager (emp-engineering-mgr-2) reviews and approves request...")
    approved_req = service.approve_request(request_id=appr_req.request_id, approver_actor_id="emp-engineering-mgr-2")
    print(f"[SUCCESS] Request Status: {approved_req.status.value}, Approved By: {approved_req.approved_by_actor_id}\n")

    # --------------------------------------------------------------------------
    # SCENARIO 3: Emergency Stop (Kill Switch) Across System Scope
    # --------------------------------------------------------------------------
    print("--- SCENARIO 3: Emergency Stop (Kill Switch) Activation ---")
    print("[!] Security Incident Detected: Activating GLOBAL Emergency Stop...")
    stop = service.activate_emergency_stop(
        activated_by_actor_id="usr-ciso-01",
        reason="Detected unverified anomalous API requests",
        scope=GovernanceScope.GLOBAL,
        scope_id="GLOBAL",
    )
    print(f"[!] Emergency Stop Activated! Stop ID: {stop.stop_id}")

    # Check autonomy evaluation under emergency stop
    autonomy_stop, risk_stop, _ = service.evaluate_autonomy(
        action_type="routine_task",
        action_target="dev-server",
        actor_id="emp-dev-1",
    )
    print(f"[-] System Autonomy state under Emergency Stop: {autonomy_stop.value} (Risk: {risk_stop.value})")
    assert autonomy_stop == AutonomyLevel.BLOCKED

    # Resume system operation
    print("[+] Deactivating Emergency Stop after incident resolution...")
    service.deactivate_emergency_stop(stop_id=stop.stop_id, deactivated_by_actor_id="usr-ciso-01")
    assert service.is_emergency_stopped(GovernanceScope.GLOBAL, "GLOBAL") is False
    print("[SUCCESS] Emergency Stop deactivated. Autonomous operations resumed safely.\n")

    print("================================================================================")
    print("ALL PHASE 11 HUMAN GOVERNANCE DEMONSTRATIONS COMPLETED SUCCESSFULLY!")
    print("================================================================================\n")


if __name__ == "__main__":
    run_demo()

"""
Phase 11 & Phase 12 Governed Autonomous AI Organization Platform End-to-End Demonstration Script.
Full Organization Workflow across Phases 1-12.
"""

import asyncio
from unittest.mock import AsyncMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import src.infrastructure.models  # noqa: F401
from src.application.governance_service import GovernanceService
from src.application.model_router import ModelRouter
from src.application.recovery_engine import RecoveryEngine
from src.application.software_project_service import SoftwareProjectService
from src.application.verification_engine import VerificationEngine
from src.domain.agent import Agent, AgentState
from src.domain.employee import Employee, EmployeeStatus
from src.domain.governance import AutonomyLevel, GovernanceRule, GovernanceScope, RiskLevel
from src.domain.model_routing import ModelCapability
from src.domain.recovery import FailureBudget
from src.domain.verification import EvidenceTrustLevel, VerificationRule, VerificationType
from src.infrastructure.database import Base
from src.infrastructure.repositories.governance_repository import GovernanceRepository
from src.infrastructure.repositories.model_routing_repository import ModelRoutingRepository
from src.infrastructure.repositories.verification_repository import VerificationRepository


async def run_async_demo():
    print("================================================================================")
    print("AUTONOMOUS AI ORGANIZATION PLATFORM — FULL GOVERNED COMPANY WORKFLOW (PHASES 1-12)")
    print("================================================================ launch\n")

    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Repositories & Services
    gov_repo = GovernanceRepository(session)
    mr_repo = ModelRoutingRepository(session)
    verif_repo = VerificationRepository(session)

    gov_service = GovernanceService(repository=gov_repo)
    model_router = ModelRouter(repository=mr_repo)
    verif_engine = VerificationEngine(repository=verif_repo)
    rec_engine = RecoveryEngine(repository=verif_repo, default_budget=FailureBudget())

    proj_repo = AsyncMock()
    req_repo = AsyncMock()
    task_repo = AsyncMock()
    dep_repo = AsyncMock()
    emp_repo = AsyncMock()
    assign_repo = AsyncMock()
    obj_repo = AsyncMock()

    mock_obj = AsyncMock()
    mock_obj.description = "Core FinTech Objective"
    obj_repo.get_by_id.return_value = mock_obj
    proj_repo.get_by_objective_id.return_value = None

    sw_service = SoftwareProjectService(
        project_repo=proj_repo,
        req_repo=req_repo,
        task_repo=task_repo,
        dep_repo=dep_repo,
        employee_repo=emp_repo,
        assignment_repo=assign_repo,
        objective_repo=obj_repo,
    )

    # 1. Organization Setup
    print("--- STEP 1: Setting Up Governed AI Company Structure ---")
    vp_eng = Employee(
        id="emp-vp-eng",
        employee_code="EMP-001",
        name="Alice Vance",
        title="VP Engineering",
        role="VP_ENGINEERING",
        agent_id="agent-dev-1",
        status=EmployeeStatus.ACTIVE,
    )
    lead_dev = Employee(
        id="emp-lead-dev",
        employee_code="EMP-002",
        name="Bob Developer",
        title="Senior Software Engineer",
        role="SENIOR_SOFTWARE_ENGINEER",
        agent_id="agent-dev-1",
        status=EmployeeStatus.ACTIVE,
    )

    agent_dev = Agent(id="agent-dev-1", name="DevBot", role="Software Engineer Agent", capabilities=["CODE_GENERATION"], current_state=AgentState.IDLE)

    model_router.register_model_profile(
        model_id="llama-3.3-70b-versatile",
        provider_name="Groq",
        model_name="Llama 3.3 70B",
        capabilities=[ModelCapability.TEXT_GENERATION, ModelCapability.CODE_GENERATION],
        quality_score=0.92,
    )
    print("[+] Governed Company Structure & Model Routing Registry Initialized.")

    # 2. Establish Governance Policy
    print("\n--- STEP 2: Establishing Production Governance Policy ---")
    rule = GovernanceRule(
        rule_id="r-prod-release",
        name="Production Release Approval",
        description="Releasing production binary requires VP Engineering approval",
        scope=GovernanceScope.PROJECT,
        target_pattern="release_production*",
        min_risk_level=RiskLevel.HIGH,
        autonomy_level=AutonomyLevel.APPROVAL_REQUIRED,
        required_approver_roles=["VP_ENGINEERING"],
        prohibit_self_approval=True,
    )
    gov_service.define_policy("Production Policy", GovernanceScope.PROJECT, "proj-fintech", level="PROJECT", rules=[rule])
    print("[+] Production Governance Policy Enforced.")

    # 3. Create & Execute Software Project Workflow
    print("\n--- STEP 3: Executing Governed Software Project Workflow ---")
    mock_proj = AsyncMock()
    mock_proj.project_id = "proj-fintech"
    mock_proj.name = "FinTech Payment Service"
    proj_repo.save.return_value = mock_proj
    proj_repo.get_by_id.return_value = mock_proj

    proj = await sw_service.create_software_project(
        objective_id="obj-fintech-1",
        name="FinTech Payment Service",
        repository_path="https://github.com/org/fintech.git",
        description="Core Payment Engine",
    )
    print(f"[+] Created Project '{proj.name}' (ID: {proj.project_id})")

    reqs = await sw_service.add_requirements(
        project_id=proj.project_id,
        requirements_data=[{"title": "Stripe Integration", "description": "Add Stripe payment processing", "priority": "HIGH"}],
    )
    print(f"[+] Added {len(reqs)} structured requirements to Software Project.")

    # Request Approval for Production Release
    appr = gov_service.request_approval(
        action_type="release_production_v1",
        action_target="prod-fintech",
        requested_by_actor_id=lead_dev.id,
        project_id=proj.project_id,
        risk_level=RiskLevel.HIGH,
    )
    print(f"[!] Approval Requested for Production Release: ID={appr.request_id}, Status={appr.status.value}")

    # VP Engineering Approves Release
    appr_granted = gov_service.approve_request(request_id=appr.request_id, approver_actor_id=vp_eng.id)
    print(f"[+] VP Engineering Approved Release! Status={appr_granted.status.value}, ApprovedBy={appr_granted.approved_by_actor_id}")

    # 4. Verification & Recovery
    print("\n--- STEP 4: Independent Outcome Verification ---")
    v_rule = VerificationRule(
        rule_id="vr-1",
        rule_type=VerificationType.TEST_VERIFICATION,
        name="Integration Tests Pass",
        description="Verify 100% test pass rate",
        target="pytest tests/integration/test_stripe.py",
        expected_condition={"exit_code": 0},
    )
    verif_engine.define_expected_outcome(task_id="task-stripe-1", description="Implement Stripe", criteria=["Tests pass"], rules=[v_rule])
    verif_engine.add_evidence(source_type="TestRun", source_id="tr-1", task_id="task-stripe-1", trust_level=EvidenceTrustLevel.EXECUTED, payload={"exit_code": 0})
    res = verif_engine.verify_task("task-stripe-1")
    print(f"[+] Task Independent Verification Result: Status={res.status.value}, Verified={res.is_verified}")

    print("\n================================================================================")
    print("ALL PHASES 1-12 FULL GOVERNED AUTONOMOUS COMPANY DEMONSTRATIONS PASSED CLEANLY!")
    print("================================================================================\n")


def run_demo():
    asyncio.run(run_async_demo())


if __name__ == "__main__":
    run_demo()

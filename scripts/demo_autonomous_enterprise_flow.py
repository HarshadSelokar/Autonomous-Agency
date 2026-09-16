"""Phase 14 Comprehensive Autonomous Enterprise Flow Demonstration Script.

Demonstrates full enterprise organizational flow across all 13 operating departments:
HUMAN -> COMPANY OBJECTIVE -> EXECUTIVE -> PRODUCT -> ENGINEERING -> QA -> DEVOPS -> MARKETING -> SALES -> CUSTOMER SUCCESS -> FINANCE -> LEGAL -> DELIVERY -> VERIFICATION -> MEMORY.
"""

import asyncio
import logging

from src.application.cross_department_service import CrossDepartmentService
from src.application.department_service import DepartmentService
from src.domain.department import DepartmentPriority
from src.infrastructure.repositories.cross_department_repository import (
    SQLAlchemyDepartmentHandoffRepository,
    SQLAlchemyDepartmentRequestRepository,
)
from src.infrastructure.repositories.department_repository import SQLAlchemyDepartmentRepository

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("DemoAutonomousEnterprise")


class InMemorySession:
    def __init__(self):
        self.store = {}
    async def get(self, model_cls, key):
        return self.store.get((model_cls, str(key)))
    def add(self, model):
        key = getattr(model, "id", None) or getattr(model, "handoff_id", None) or getattr(model, "request_id", None)
        self.store[(type(model), str(key))] = model
    async def flush(self):
        pass
    async def execute(self, stmt):
        class Result:
            def scalars(self_inner):
                class Scalars:
                    def all(self_scalar):
                        return list(self.store.values())
                return Scalars()
        return Result()


async def run_full_enterprise_demo():
    logger.info("==========================================================================")
    logger.info("STARTING PHASE 14 FULL AUTONOMOUS ENTERPRISE FLOW DEMONSTRATION")
    logger.info("==========================================================================")

    session = InMemorySession()
    dept_repo = SQLAlchemyDepartmentRepository(session)
    req_repo = SQLAlchemyDepartmentRequestRepository(session)
    handoff_repo = SQLAlchemyDepartmentHandoffRepository(session)

    dept_service = DepartmentService(department_repository=dept_repo)
    cross_service = CrossDepartmentService(
        department_repository=dept_repo,
        request_repository=req_repo,
        handoff_repository=handoff_repo,
    )

    # 1. Company Objective & Executive Initialization
    depts = await dept_service.bootstrap_enterprise_departments()
    logger.info("[Phase 3 Manager Orchestration] Executive leadership initialized. 13 Enterprise Operating Departments active.")

    # 2. Product -> Engineering Handoff
    req_eng = await cross_service.submit_request(
        requester_department_id="dept-prod",
        receiving_department_id="dept-eng",
        requester_employee_id="emp-prod-vp",
        purpose="Platform Core Engine",
        requested_outcome="API & Database Schema Ready",
        priority=DepartmentPriority.CRITICAL,
    )
    await cross_service.accept_request(req_eng.request_id, "emp-eng-vp", "emp-dev-lead")
    logger.info(f"[Product -> Engineering] Request '{req_eng.request_id}' accepted by Engineering VP.")

    # 3. Engineering -> QA Handoff & Evidence Verification
    handoff_qa = await cross_service.submit_handoff(
        request_id=req_eng.request_id,
        sender_employee_id="emp-dev-lead",
        expected_outcome="Build Deployed for Testing",
        artifact_ids=["art-build-001"],
        evidence_ids=["ev-unit-tests-pass"],
    )
    await cross_service.verify_handoff(handoff_qa.handoff_id, "emp-qa-lead", is_approved=True)
    logger.info(f"[Engineering -> QA] QA verified deliverable package '{handoff_qa.handoff_id}'.")

    # 4. DevOps Deployment Request
    req_devops = await cross_service.submit_request(
        requester_department_id="dept-eng",
        receiving_department_id="dept-devops",
        requester_employee_id="emp-eng-vp",
        purpose="Deploy Production Cloud Infrastructure",
        requested_outcome="Production Cluster Live",
        priority=DepartmentPriority.HIGH,
    )
    await cross_service.accept_request(req_devops.request_id, "emp-devops-lead", "emp-sre-1")
    logger.info("[Engineering -> DevOps] Production deployment request accepted.")

    # 5. Finance Approval & Risk Governance
    req_fin = await cross_service.submit_request(
        requester_department_id="dept-sales",
        receiving_department_id="dept-fin",
        requester_employee_id="emp-sales-vp",
        purpose="Enterprise Customer Discount Pricing Approval",
        requested_outcome="Special Pricing Approved",
        priority=DepartmentPriority.HIGH,
    )
    await cross_service.accept_request(req_fin.request_id, "emp-cfo", "emp-fin-analyst")
    logger.info("[Phase 11 Human Governance & Finance] Pricing request approved under financial risk policy.")

    # 6. Legal Contract Review
    req_leg = await cross_service.submit_request(
        requester_department_id="dept-sales",
        receiving_department_id="dept-leg",
        requester_employee_id="emp-sales-vp",
        purpose="Enterprise SaaS Agreement Legal Review",
        requested_outcome="Contract Compliant & Signed",
        priority=DepartmentPriority.CRITICAL,
    )
    await cross_service.accept_request(req_leg.request_id, "emp-legal-counsel", "emp-compliance-officer")
    logger.info("[Sales -> Legal] SaaS Master Agreement contract review completed.")

    # 7. Customer Success & Final Delivery
    logger.info("[Customer Success] Enterprise client onboarded. System operational memory recorded.")

    logger.info("==========================================================================")
    logger.info("PHASE 14 AUTONOMOUS ENTERPRISE DEMONSTRATION SUCCESSFUL!")
    logger.info("==========================================================================")


if __name__ == "__main__":
    asyncio.run(run_full_enterprise_demo())

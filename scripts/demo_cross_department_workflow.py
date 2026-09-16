"""Phase 14 Cross-Department Collaboration Workflow Demonstration Script.

Demonstrates formal request submission, acceptance, deliverable handoff, evidence verification,
and cross-department coordination across Product, Engineering, QA, Marketing, and Sales.
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
logger = logging.getLogger("DemoCrossDepartment")


class InMemorySession:
    """In-memory mock session for demonstration script."""
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


async def run_demo():
    logger.info("==========================================================================")
    logger.info("STARTING PHASE 14 CROSS-DEPARTMENT COLLABORATION WORKFLOW DEMO")
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

    # 1. Bootstrap Enterprise Departments
    depts = await dept_service.bootstrap_enterprise_departments()
    logger.info(f"[Step 1] Enterprise Departments bootstrapped ({len(depts)} active departments).")

    # 2. Product -> Engineering Request
    req_eng = await cross_service.submit_request(
        requester_department_id="dept-prod",
        receiving_department_id="dept-eng",
        requester_employee_id="emp-prod-head",
        purpose="Build SaaS Core Platform API",
        requested_outcome="Production-ready REST Endpoints",
        priority=DepartmentPriority.HIGH,
    )
    logger.info(f"[Step 2] Product submitted Request '{req_eng.request_id}' to Engineering.")

    # 3. Engineering Acceptance & Owner Assignment
    accepted_eng = await cross_service.accept_request(
        request_id=req_eng.request_id,
        receiving_manager_id="emp-eng-dir",
        delivery_owner_employee_id="emp-backend-dev",
    )
    logger.info(f"[Step 3] Engineering Manager accepted request. Assigned Delivery Owner: '{accepted_eng.delivery_owner_employee_id}'.")

    # 4. Engineering Deliverable Handoff to QA
    handoff_qa = await cross_service.submit_handoff(
        request_id=req_eng.request_id,
        sender_employee_id="emp-backend-dev",
        expected_outcome="Core Platform API Deployed to QA Environment",
        artifact_ids=["art-openapi-spec"],
        evidence_ids=["ev-test-results-pass"],
        acceptance_criteria=["OpenAPI spec compliant", "Test suite passing"],
    )
    logger.info(f"[Step 4] Engineering submitted Handoff Package '{handoff_qa.handoff_id}' to QA.")

    # 5. QA Evidence Verification & Acceptance
    verified_qa = await cross_service.verify_handoff(
        handoff_id=handoff_qa.handoff_id,
        verifier_employee_id="emp-qa-lead",
        is_approved=True,
    )
    logger.info(f"[Step 5] QA Lead verified deliverable using Phase 10 Evidence Verification. Status: {verified_qa.status.value} (VERIFIED).")

    # 6. Marketing Launch Campaign Request
    req_mkt = await cross_service.submit_request(
        requester_department_id="dept-prod",
        receiving_department_id="dept-mkt",
        requester_employee_id="emp-prod-head",
        purpose="Launch SaaS Marketing & Positioning Campaign",
        requested_outcome="Marketing Campaign & Content Deployed",
        priority=DepartmentPriority.MEDIUM,
    )
    accepted_mkt = await cross_service.accept_request(
        request_id=req_mkt.request_id,
        receiving_manager_id="emp-mkt-dir",
        delivery_owner_employee_id="emp-copywriter",
    )
    logger.info(f"[Step 6] Marketing accepted Launch Campaign Request '{accepted_mkt.request_id}'.")

    # 7. Department Health Evaluation
    health = await dept_service.evaluate_department_health("dept-eng", blocked_tasks_count=0)
    logger.info(f"[Step 7] Engineering Department Health Evaluation: {health.health.value} ({health.reason}).")

    logger.info("==========================================================================")
    logger.info("PHASE 14 CROSS-DEPARTMENT WORKFLOW DEMO COMPLETED SUCCESSFULLY!")
    logger.info("==========================================================================")


if __name__ == "__main__":
    asyncio.run(run_demo())

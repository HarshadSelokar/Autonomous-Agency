"""Phase 13 Comprehensive Autonomous Company Pixel Office Demonstration Script.

Demonstrates the complete multi-phase flow visualized via Pixel Office:
Human -> Objective -> Manager -> Project -> Task Graph -> Governance -> Approval -> Model Routing -> Employee -> AgentRun -> Workspace -> Tools -> Artifact -> Verification -> Failure -> Recovery -> Rework -> Verification -> Success -> Delivery -> Memory.
"""

import asyncio
import logging
from uuid import uuid4

from src.application.office_projection_service import OfficeProjectionService
from src.application.office_realtime_service import (
    OfficeRealtimeBroadcaster,
    PixelOfficeConnection,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("DemoAutonomousCompanyOffice")


async def run_full_company_demo():
    logger.info("==========================================================================")
    logger.info("STARTING PHASE 13 FULL AUTONOMOUS COMPANY PIXEL OFFICE DEMONSTRATION")
    logger.info("==========================================================================")

    service = OfficeProjectionService()
    broadcaster = OfficeRealtimeBroadcaster()

    # Client socket
    conn = PixelOfficeConnection(connection_id="executive-view-1", user_id=uuid4())
    broadcaster.register_connection(conn)

    org_id = str(uuid4())
    emp_dev_id = str(uuid4())
    emp_mgr_id = str(uuid4())
    task_id = str(uuid4())
    project_id = str(uuid4())

    # 1. Human Objective & Manager Planning
    logger.info("[Phase 3] Engineering Manager plans software project. Workstations initialized.")

    # 2. High-Risk Action & Governance Approval Requirement
    s_appr = service.derive_employee_visual_state(
        employee_id=emp_dev_id,
        is_awaiting_approval=True,
    )
    logger.info(f"[Phase 11 Human Governance] High-risk action requires approval. Visual state: {s_appr.value} (AWAITING_APPROVAL).")

    # 3. Human Approval Granted & Model Routing
    logger.info("[Phase 12 Model Routing] Model selected based on task complexity. Human approval granted.")

    # 4. Agent Execution & Tool Usage
    s_work = service.derive_employee_visual_state(
        employee_id=emp_dev_id,
        is_agent_running=True,
    )
    logger.info(f"[Phase 1 & 8] Employee executing agent run with Browser & Git tools. Visual state: {s_work.value} (WORKING).")

    # 5. Verification & Recovery
    s_verif = service.derive_employee_visual_state(
        employee_id=emp_dev_id,
        is_verifying=True,
    )
    logger.info(f"[Phase 10 Verification] Running test suite. Visual state: {s_verif.value} (REVIEWING).")

    s_rec = service.derive_employee_visual_state(
        employee_id=emp_dev_id,
        is_recovering=True,
    )
    logger.info(f"[Phase 10 Recovery] Tests failed. Recovery Engine triggered. Visual state: {s_rec.value} (RECOVERING).")

    # 6. Rework & Delivery
    s_done = service.derive_employee_visual_state(
        employee_id=emp_dev_id,
        is_agent_running=False,
    )
    logger.info(f"[Phase 9 AI Software Company] Software delivered successfully. Visual state: {s_done.value} (IDLE).")

    overview = await service.build_company_overview(org_id)
    logger.info(f"Final Company Overview Projection: {overview.company_name} | Active Employees: {overview.active_employees_count}")

    logger.info("==========================================================================")
    logger.info("PHASE 13 FULL AUTONOMOUS COMPANY PIXEL OFFICE DEMONSTRATION SUCCESSFUL!")
    logger.info("==========================================================================")


if __name__ == "__main__":
    asyncio.run(run_full_company_demo())

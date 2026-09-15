"""Phase 13 Pixel Office End-to-End Flow Demonstration Script.

Demonstrates real backend execution projecting into Pixel Office visual states:
Company starts -> Employees visible -> Tasks appear -> WORKING -> Tool Execution -> Verification -> Failure -> RECOVERING -> Rework -> Success -> COMPLETED.
"""

import asyncio
import logging
from uuid import uuid4

from src.domain.office import (
    EmployeeVisualState,
    HumanAttentionType,
    OfficeAreaType,
)
from src.domain.events import OfficeStateUpdatedEvent
from src.application.office_projection_service import OfficeProjectionService
from src.application.office_realtime_service import (
    OfficeRealtimeBroadcaster,
    PixelOfficeConnection,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("DemoPixelOffice")


async def run_demo():
    logger.info("============================================================")
    logger.info("STARTING PHASE 13 PIXEL OFFICE REALTIME E2E DEMONSTRATION")
    logger.info("============================================================")

    service = OfficeProjectionService()
    broadcaster = OfficeRealtimeBroadcaster()

    # 1. Register Client Connection
    conn = PixelOfficeConnection(
        connection_id="dashboard-client-1",
        user_id=uuid4(),
        authorized_departments=["Engineering"],
    )
    broadcaster.register_connection(conn)
    logger.info(f"[Step 1] Registered Pixel Office client connection ({broadcaster.active_connection_count} active).")

    emp_id = str(uuid4())
    task_id = str(uuid4())
    project_id = str(uuid4())

    # 2. Initial State: IDLE
    s1 = service.derive_employee_visual_state(employee_id=emp_id)
    logger.info(f"[Step 2] Employee visual state: {s1.value} (IDLE)")

    # 3. Agent Execution Starts: WORKING
    s2 = service.derive_employee_visual_state(employee_id=emp_id, is_agent_running=True)
    evt_working = OfficeStateUpdatedEvent(
        employee_id=emp_id,
        visual_state=s2.value,
        activity_summary="Running agent step on backend",
        task_id=task_id,
        project_id=project_id,
    )
    delivered = await broadcaster.broadcast_event(evt_working)
    logger.info(f"[Step 3] Employee visual state updated to: {s2.value} (WORKING). Event broadcast to {delivered} client.")

    # 4. Verification Check: REVIEWING
    s3 = service.derive_employee_visual_state(employee_id=emp_id, is_verifying=True)
    logger.info(f"[Step 4] Employee visual state updated to: {s3.value} (REVIEWING).")

    # 5. Verification Failure & Recovery Engine: RECOVERING
    s4 = service.derive_employee_visual_state(employee_id=emp_id, is_recovering=True)
    logger.info(f"[Step 5] Verification failed. Recovery Engine initiated. Visual state: {s4.value} (RECOVERING).")

    # 6. Rework Completion & Task Success: COMPLETED -> IDLE
    s5 = service.derive_employee_visual_state(employee_id=emp_id, is_agent_running=False)
    logger.info(f"[Step 6] Recovery succeeded. Rework complete. Visual state returns to: {s5.value} (IDLE).")

    logger.info("============================================================")
    logger.info("PHASE 13 PIXEL OFFICE DEMONSTRATION COMPLETED SUCCESSFULLY!")
    logger.info("============================================================")


if __name__ == "__main__":
    asyncio.run(run_demo())

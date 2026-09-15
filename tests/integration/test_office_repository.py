"""
Integration tests for Phase 13 GovernanceOfficeRepository.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import src.infrastructure.models  # noqa: F401
from src.domain.office import (
    EmployeeVisualState,
    EmployeeWorkstationProjection,
    HumanAttentionItem,
    HumanAttentionType,
    OfficeActivityItem,
    OfficeAreaType,
)
from src.infrastructure.database import Base
from src.infrastructure.repositories.office_repository import GovernanceOfficeRepository


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_office_repository_workstation_crud(db_session):
    repo = GovernanceOfficeRepository(db_session)

    ws = EmployeeWorkstationProjection(
        employee_id="emp-dev-10",
        employee_name="Charlie Dev",
        employee_title="Fullstack Developer",
        role="DEVELOPER",
        department_id="dept-eng",
        manager_id="emp-mgr-1",
        desk_id="desk-eng-10",
        area_type=OfficeAreaType.ENGINEERING,
        visual_state=EmployeeVisualState.WORKING,
        current_task_id="task-99",
        current_activity_summary="Fixing authentication bug",
    )

    saved_ws = repo.save_workstation(ws)
    assert saved_ws.employee_id == "emp-dev-10"

    retrieved = repo.get_workstation("emp-dev-10")
    assert retrieved is not None
    assert retrieved.employee_name == "Charlie Dev"
    assert retrieved.visual_state == EmployeeVisualState.WORKING

    all_ws = repo.list_workstations("dept-eng")
    assert len(all_ws) == 1
    assert all_ws[0].employee_id == "emp-dev-10"


def test_office_repository_activity_and_attention_queue(db_session):
    repo = GovernanceOfficeRepository(db_session)

    # Activity Log
    act = OfficeActivityItem(
        activity_id="act-10",
        title="Task Started",
        description="Developer started task-99",
        category="TASK",
        actor_id="emp-dev-10",
        entity_id="task-99",
    )
    repo.record_activity(act)

    recent = repo.get_recent_activities(limit=10)
    assert len(recent) == 1
    assert recent[0].title == "Task Started"

    # Attention Queue
    att = HumanAttentionItem(
        item_id="att-99",
        attention_type=HumanAttentionType.APPROVAL_REQUIRED,
        title="Approval Request",
        description="Deploy to prod requires manager review",
        entity_id="appr-10",
        entity_type="APPROVAL",
        severity="HIGH",
    )
    repo.save_attention_item(att)

    queue = repo.get_attention_queue()
    assert len(queue) == 1
    assert queue[0].item_id == "att-99"

    repo.delete_attention_item("att-99")
    queue_after = repo.get_attention_queue()
    assert len(queue_after) == 0

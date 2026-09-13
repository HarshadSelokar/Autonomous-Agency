"""
Integration tests for SQLAlchemyMeetingRepository and meeting ORM mappings.
"""

from datetime import UTC, datetime, timedelta
from typing import AsyncGenerator
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.domain.employee import Employee, EmployeeStatus
from src.domain.meeting import (
    AttendanceStatus,
    Meeting,
    MeetingPurpose,
    MeetingStatus,
    ParticipantRole,
)
from src.infrastructure.database import Base
from src.infrastructure.models.employee_model import employee_domain_to_model
from src.infrastructure.repositories.meeting_repository import SQLAlchemyMeetingRepository


@pytest_asyncio.fixture
async def async_session() -> AsyncGenerator[AsyncSession, None]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session_factory() as session:
        yield session

    await engine.dispose()


@pytest.mark.asyncio
async def test_meeting_repository_crud_and_queries(async_session: AsyncSession) -> None:
    # 1. Seed prerequisite employees
    emp_org = Employee(
        id="emp-org",
        name="Alice Manager",
        role="Manager",
        status=EmployeeStatus.ACTIVE,
        employee_code="EMP_ORG",
        title="Engineering Manager",
        agent_id="agent-org",
    )
    emp_part = Employee(
        id="emp-part",
        name="Bob Developer",
        role="Engineer",
        status=EmployeeStatus.ACTIVE,
        employee_code="EMP_PART",
        title="Senior Developer",
        agent_id="agent-part",
    )
    async_session.add(employee_domain_to_model(emp_org))
    async_session.add(employee_domain_to_model(emp_part))
    await async_session.flush()

    repo = SQLAlchemyMeetingRepository(async_session)

    # 2. Create Meeting domain object
    now = datetime.now(UTC)
    meeting = Meeting(
        id="m-repo-1",
        title="Sprint Architecture Sync",
        purpose=MeetingPurpose.REVIEW,
        organizer_employee_id="emp-org",
        scheduled_start=now,
        scheduled_end=now + timedelta(hours=1),
    )
    meeting.add_participant("emp-part", role=ParticipantRole.REQUIRED)
    meeting.add_agenda_item(item_id="ag-1", title="Database Migration Strategy", duration_minutes=30)
    meeting.record_attendance("emp-part", AttendanceStatus.ACCEPTED)

    # 3. Save to database
    saved = await repo.save(meeting)
    await async_session.commit()
    assert saved.id == "m-repo-1"

    # 4. Get by ID
    fetched = await repo.get_by_id("m-repo-1")
    assert fetched is not None
    assert fetched.title == "Sprint Architecture Sync"
    assert fetched.organizer_employee_id == "emp-org"
    assert "emp-part" in fetched.participants
    assert fetched.participants["emp-part"].role == ParticipantRole.REQUIRED
    assert len(fetched.agenda_items) == 1
    assert fetched.agenda_items[0].title == "Database Migration Strategy"
    assert fetched.attendance_records["emp-part"].status == AttendanceStatus.ACCEPTED

    # 5. List all
    all_meetings = await repo.list_all()
    assert len(all_meetings) == 1
    assert all_meetings[0].id == "m-repo-1"

    # 6. List by participant
    by_part = await repo.list_by_participant("emp-part")
    assert len(by_part) == 1
    assert by_part[0].id == "m-repo-1"

    by_other = await repo.list_by_participant("nonexistent-emp")
    assert len(by_other) == 0

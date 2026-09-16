"""
Unit tests for Meeting scheduling, agenda management, and conflict detection.
"""

from datetime import UTC, datetime, timedelta

import pytest

from src.application.meeting_scheduling_service import MeetingSchedulingService
from src.domain.employee import Employee, EmployeeStatus
from src.domain.exceptions import EmployeeNotFoundError
from src.domain.meeting import (
    AgendaItemStatus,
    Meeting,
    MeetingPurpose,
    MeetingSchedulingConflictError,
    MeetingStatus,
)
from src.domain.repository import EmployeeRepositoryInterface, MeetingRepositoryInterface


class MemoryMeetingRepository(MeetingRepositoryInterface):
    def __init__(self) -> None:
        self.meetings: dict[str, Meeting] = {}

    async def save(self, meeting: Meeting) -> Meeting:
        self.meetings[meeting.id] = meeting
        return meeting

    async def get_by_id(self, meeting_id: str) -> Meeting | None:
        return self.meetings.get(meeting_id)

    async def list_all(self) -> list[Meeting]:
        return list(self.meetings.values())

    async def list_by_participant(self, employee_id: str) -> list[Meeting]:
        return [
            m for m in self.meetings.values()
            if employee_id in m.participants
        ]


class MemoryEmployeeRepository(EmployeeRepositoryInterface):
    def __init__(self) -> None:
        self.employees: dict[str, Employee] = {}

    async def save(self, employee: Employee) -> Employee:
        self.employees[employee.id] = employee
        return employee

    async def get_by_id(self, employee_id: str) -> Employee | None:
        return self.employees.get(employee_id)

    async def get_by_code(self, employee_code: str) -> Employee | None:
        for emp in self.employees.values():
            if emp.employee_code == employee_code:
                return emp
        return None

    async def list_by_department_id(self, department_id: str) -> list[Employee]:
        return [emp for emp in self.employees.values() if emp.department_id == department_id]

    async def list_all(self) -> list[Employee]:
        return list(self.employees.values())

    async def delete(self, employee_id: str) -> bool:
        return self.employees.pop(employee_id, None) is not None


@pytest.mark.asyncio
async def test_agenda_management() -> None:
    meeting = Meeting(
        id="m-500",
        title="Agenda Test Meeting",
        purpose=MeetingPurpose.PLANNING,
        organizer_employee_id="emp-1",
    )

    item1 = meeting.add_agenda_item(item_id="ag-1", title="Opening & Objectives")
    item2 = meeting.add_agenda_item(item_id="ag-2", title="Architecture Alternatives", duration_minutes=20)

    assert len(meeting.agenda_items) == 2
    assert item1.order == 1
    assert item2.order == 2
    assert item2.duration_minutes == 20
    assert item1.status == AgendaItemStatus.PROPOSED


@pytest.mark.asyncio
async def test_meeting_scheduling_success() -> None:
    meeting_repo = MemoryMeetingRepository()
    employee_repo = MemoryEmployeeRepository()

    emp1 = Employee(
        id="emp-1",
        name="Alice",
        role="Engineer",
        status=EmployeeStatus.ACTIVE,
        employee_code="EMP001",
        title="Software Engineer",
        agent_id="agent-1",
    )
    emp2 = Employee(
        id="emp-2",
        name="Bob",
        role="Engineer",
        status=EmployeeStatus.ACTIVE,
        employee_code="EMP002",
        title="Software Engineer",
        agent_id="agent-2",
    )
    await employee_repo.save(emp1)
    await employee_repo.save(emp2)

    service = MeetingSchedulingService(meeting_repo=meeting_repo, employee_repo=employee_repo)

    meeting = await service.create_meeting(
        meeting_id="m-600",
        title="Sprint Sync",
        purpose=MeetingPurpose.COORDINATION,
        organizer_employee_id="emp-1",
        participant_ids=["emp-2"],
    )
    assert meeting.status == MeetingStatus.PROPOSED

    now = datetime.now(UTC)
    scheduled = await service.schedule_meeting(
        meeting_id="m-600",
        scheduled_start=now + timedelta(hours=1),
        scheduled_end=now + timedelta(hours=2),
    )
    assert scheduled.status == MeetingStatus.SCHEDULED


@pytest.mark.asyncio
async def test_meeting_scheduling_conflict_detection() -> None:
    meeting_repo = MemoryMeetingRepository()
    employee_repo = MemoryEmployeeRepository()

    emp1 = Employee(
        id="emp-1",
        name="Alice",
        role="Engineer",
        status=EmployeeStatus.ACTIVE,
        employee_code="EMP001",
        title="Software Engineer",
        agent_id="agent-1",
    )
    emp2 = Employee(
        id="emp-2",
        name="Bob",
        role="Engineer",
        status=EmployeeStatus.ACTIVE,
        employee_code="EMP002",
        title="Software Engineer",
        agent_id="agent-2",
    )
    await employee_repo.save(emp1)
    await employee_repo.save(emp2)

    service = MeetingSchedulingService(meeting_repo=meeting_repo, employee_repo=employee_repo)

    # Schedule Meeting 1: 10:00 - 11:00 with emp-1 and emp-2
    now = datetime.now(UTC)
    m1 = await service.create_meeting(
        meeting_id="m-1",
        title="First Meeting",
        purpose=MeetingPurpose.REVIEW,
        organizer_employee_id="emp-1",
        participant_ids=["emp-2"],
    )
    await service.schedule_meeting(
        meeting_id="m-1",
        scheduled_start=now + timedelta(hours=1),
        scheduled_end=now + timedelta(hours=2),
    )

    # Attempt to schedule Meeting 2: 10:30 - 11:30 with emp-2
    m2 = await service.create_meeting(
        meeting_id="m-2",
        title="Overlapping Meeting",
        purpose=MeetingPurpose.STATUS,
        organizer_employee_id="emp-1",
        participant_ids=["emp-2"],
    )

    with pytest.raises(MeetingSchedulingConflictError, match="has a scheduling conflict"):
        await service.schedule_meeting(
            meeting_id="m-2",
            scheduled_start=now + timedelta(hours=1, minutes=30),
            scheduled_end=now + timedelta(hours=2, minutes=30),
        )


@pytest.mark.asyncio
async def test_scheduling_invalid_organizer_or_participant() -> None:
    meeting_repo = MemoryMeetingRepository()
    employee_repo = MemoryEmployeeRepository()
    service = MeetingSchedulingService(meeting_repo=meeting_repo, employee_repo=employee_repo)

    with pytest.raises(EmployeeNotFoundError, match="Organizer employee"):
        await service.create_meeting(
            meeting_id="m-700",
            title="Invalid Organizer",
            purpose=MeetingPurpose.INCIDENT,
            organizer_employee_id="nonexistent-emp",
        )

"""
Unit tests for MemoryService lifecycle management, confirmation, promotion, and supersession.
"""

from typing import Any
import pytest

from src.application.memory_service import MemoryService, UnauthorizedMemoryPromotionError
from src.domain.employee import Employee, EmployeeStatus
from src.domain.memory import (
    MemoryAuthority,
    MemoryEntry,
    MemoryProvenance,
    MemoryScope,
    MemoryStatus,
    MemoryType,
)
from tests.unit.test_meeting_scheduling import MemoryEmployeeRepository


class MemoryMemoryRepository:
    def __init__(self) -> None:
        self.memories: dict[str, MemoryEntry] = {}

    async def save(self, memory: MemoryEntry) -> MemoryEntry:
        self.memories[memory.id] = memory
        return memory

    async def get_by_id(self, memory_id: str) -> MemoryEntry | None:
        return self.memories.get(memory_id)

    async def list_by_owner(self, owner_id: str) -> list[MemoryEntry]:
        return [m for m in self.memories.values() if m.owner_id == owner_id and m.status == MemoryStatus.ACTIVE]

    async def list_all(self) -> list[MemoryEntry]:
        return list(self.memories.values())


@pytest.mark.asyncio
async def test_create_memory_agent_run_cannot_be_directly_authoritative() -> None:
    mem_repo = MemoryMemoryRepository()
    emp_repo = MemoryEmployeeRepository()
    service = MemoryService(memory_repo=mem_repo, employee_repo=emp_repo)

    with pytest.raises(UnauthorizedMemoryPromotionError, match="cannot be created directly as AUTHORITATIVE"):
        await service.create_memory(
            memory_type=MemoryType.SEMANTIC,
            scope=MemoryScope.TASK,
            owner_id="TASK:t-1",
            content="Generated text",
            authority=MemoryAuthority.AUTHORITATIVE,
            provenance=MemoryProvenance.AGENT_RUN,
        )


@pytest.mark.asyncio
async def test_confirm_and_promote_memory() -> None:
    mem_repo = MemoryMemoryRepository()
    emp_repo = MemoryEmployeeRepository()

    mgr = Employee(
        id="emp-mgr",
        name="Bob Manager",
        role="Manager",
        status=EmployeeStatus.ACTIVE,
        employee_code="EMP_MGR",
        title="Engineering Manager",
        agent_id="agent-mgr",
    )
    await emp_repo.save(mgr)

    service = MemoryService(memory_repo=mem_repo, employee_repo=emp_repo)

    memory = await service.create_memory(
        memory_type=MemoryType.SEMANTIC,
        scope=MemoryScope.PROJECT,
        owner_id="PROJECT:p-1",
        content="PostgreSQL is selected for main database.",
        provenance=MemoryProvenance.AGENT_RUN,
    )
    assert memory.authority == MemoryAuthority.GENERATED

    confirmed = await service.confirm_memory(memory.id, actor_employee_id="emp-mgr")
    assert confirmed.authority == MemoryAuthority.CONFIRMED

    promoted = await service.promote_memory(
        memory.id, target_authority=MemoryAuthority.AUTHORITATIVE, actor_employee_id="emp-mgr"
    )
    assert promoted.authority == MemoryAuthority.AUTHORITATIVE


@pytest.mark.asyncio
async def test_supersede_memory() -> None:
    mem_repo = MemoryMemoryRepository()
    emp_repo = MemoryEmployeeRepository()
    service = MemoryService(memory_repo=mem_repo, employee_repo=emp_repo)

    m1 = await service.create_memory(
        memory_type=MemoryType.SEMANTIC,
        scope=MemoryScope.TASK,
        owner_id="TASK:t-1",
        content="Old DB choice: MySQL",
    )

    m2 = MemoryEntry(
        id="mem-new-2",
        memory_type=MemoryType.SEMANTIC,
        scope=MemoryScope.TASK,
        owner_id="TASK:t-1",
        content="New DB choice: PostgreSQL",
    )

    await service.supersede_memory(old_memory_id=m1.id, new_memory=m2, actor_employee_id="emp-mgr")

    stored_m1 = await mem_repo.get_by_id(m1.id)
    assert stored_m1 is not None
    assert stored_m1.status == MemoryStatus.SUPERSEDED

    stored_m2 = await mem_repo.get_by_id(m2.id)
    assert stored_m2 is not None
    assert stored_m2.status == MemoryStatus.ACTIVE
    assert stored_m2.previous_memory_id == m1.id

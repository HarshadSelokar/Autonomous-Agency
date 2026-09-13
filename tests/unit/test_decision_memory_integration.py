"""
Unit tests for Authoritative Memory derivation from approved Decisions.
"""

from typing import Any
import pytest

from src.application.decision_integration_service import DecisionIntegrationService
from src.application.memory_service import MemoryService
from src.domain.decision import Decision, DecisionStatus
from src.domain.memory import MemoryAuthority, MemoryProvenance
from tests.unit.test_decision_integration import MemoryDecisionRepository
from tests.unit.test_meeting_scheduling import MemoryEmployeeRepository
from tests.unit.test_memory_service import MemoryMemoryRepository


@pytest.mark.asyncio
async def test_approved_decision_creates_authoritative_memory() -> None:
    dec_repo = MemoryDecisionRepository()
    mem_repo = MemoryMemoryRepository()
    emp_repo = MemoryEmployeeRepository()

    memory_service = MemoryService(memory_repo=mem_repo, employee_repo=emp_repo)

    decision = Decision(
        id="d-mem-1",
        title="Official Database Selection",
        question="Which database engine should be used?",
        decision_maker_employee_id="emp-mgr",
        status=DecisionStatus.APPROVED,
        task_id="t-100",
        chosen_option="PostgreSQL",
        rationale="ACID guarantees and vector embedding support.",
    )
    await dec_repo.save(decision)

    service = DecisionIntegrationService(
        decision_repo=dec_repo,
        memory_service=memory_service,
    )

    res = await service.execute_approved_decision_actions("d-mem-1", actor_employee_id="emp-mgr")
    assert "Created Authoritative Memory for Decision d-mem-1" in res["executed_actions"]

    # Verify authoritative memory entry
    stored_mems = await mem_repo.list_all()
    assert len(stored_mems) == 1
    mem = stored_mems[0]
    assert mem.authority == MemoryAuthority.AUTHORITATIVE
    assert mem.provenance == MemoryProvenance.DECISION
    assert mem.decision_id == "d-mem-1"
    assert mem.task_id == "t-100"
    assert "PostgreSQL" in mem.content

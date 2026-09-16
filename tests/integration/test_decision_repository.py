"""
Integration tests for SQLAlchemyDecisionRepository, DecisionAuditModel, and Decision Supersession.
"""

from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.domain.decision import (
    Decision,
    DecisionProvenance,
    DecisionStatus,
    DecisionType,
)
from src.domain.employee import Employee, EmployeeStatus
from src.infrastructure.database import Base
from src.infrastructure.models.employee_model import employee_domain_to_model
from src.infrastructure.repositories.decision_repository import SQLAlchemyDecisionRepository


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
async def test_decision_repository_crud_audit_and_supersession(async_session: AsyncSession) -> None:
    # 1. Seed prerequisite employee
    emp_maker = Employee(
        id="emp-maker",
        name="Bob Manager",
        role="Manager",
        status=EmployeeStatus.ACTIVE,
        employee_code="EMP_MGR",
        title="Engineering Manager",
        agent_id="agent-mgr",
    )
    async_session.add(employee_domain_to_model(emp_maker))
    await async_session.flush()

    repo = SQLAlchemyDecisionRepository(async_session)

    # 2. Save Initial Decision (D1: Use REST)
    d1 = Decision(
        id="d-1",
        title="Use REST API Protocol",
        question="Which API protocol to use?",
        decision_maker_employee_id="emp-maker",
        decision_type=DecisionType.ARCHITECTURE,
        status=DecisionStatus.APPROVED,
        chosen_option="REST",
        alternatives=["GraphQL", "gRPC"],
        rationale="REST matches existing team skills.",
        provenance=DecisionProvenance.MANAGER,
    )
    await repo.save(d1)
    await async_session.commit()

    fetched_d1 = await repo.get_by_id("d-1")
    assert fetched_d1 is not None
    assert fetched_d1.status == DecisionStatus.APPROVED
    assert fetched_d1.chosen_option == "REST"

    # 3. Create Superseding Decision (D2: Use GraphQL)
    d2 = Decision(
        id="d-2",
        title="Migrate to GraphQL API Protocol",
        question="Which API protocol to use?",
        decision_maker_employee_id="emp-maker",
        decision_type=DecisionType.ARCHITECTURE,
        status=DecisionStatus.APPROVED,
        chosen_option="GraphQL",
        alternatives=["REST", "gRPC"],
        rationale="GraphQL provides typed client schemas.",
        previous_decision_id="d-1",
        provenance=DecisionProvenance.MANAGER,
    )
    await repo.save(d2)

    # 4. Supersede D1
    superseded_d1 = await repo.supersede_decision(
        old_decision_id="d-1",
        new_decision_id="d-2",
        actor_employee_id="emp-maker",
    )
    await async_session.commit()

    assert superseded_d1.status == DecisionStatus.SUPERSEDED

    # Verify D1 remains historically accessible in DB
    historical_d1 = await repo.get_by_id("d-1")
    assert historical_d1 is not None
    assert historical_d1.status == DecisionStatus.SUPERSEDED
    assert historical_d1.chosen_option == "REST"

    # Verify D2 is APPROVED
    current_d2 = await repo.get_by_id("d-2")
    assert current_d2 is not None
    assert current_d2.status == DecisionStatus.APPROVED
    assert current_d2.chosen_option == "GraphQL"
    assert current_d2.previous_decision_id == "d-1"

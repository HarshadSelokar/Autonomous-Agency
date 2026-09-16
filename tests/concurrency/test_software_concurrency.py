"""
Concurrency tests for Phase 9 AI Software Company workflows.
"""

import asyncio
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.application.code_review_service import CodeReviewService
from src.domain.software_company import CodeChangeStatus
from src.domain.task import Task
from src.infrastructure.database import Base
from src.infrastructure.repositories.software_company_repository import (
    SQLAlchemyCodeChangeRepository,
    SQLAlchemyCodeReviewRepository,
)
from src.infrastructure.repositories.task_repository import SQLAlchemyTaskRepository


@pytest_asyncio.fixture
async def session_factory() -> AsyncGenerator[sessionmaker, None]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    yield factory

    await engine.dispose()


@pytest.mark.asyncio
async def test_concurrent_code_change_submissions(session_factory: sessionmaker):
    # Setup initial task
    async with session_factory() as setup_session:
        task_repo = SQLAlchemyTaskRepository(setup_session)
        task = await task_repo.save(
            Task(id="task-conc-1", plan_id="plan-conc", title="Concurrent Task", description="Concurrent dev", required_capabilities=["BACKEND_DEVELOPMENT"])
        )
        await setup_session.commit()

    async def submit_change(idx: int):
        async with session_factory() as session:
            change_repo = SQLAlchemyCodeChangeRepository(session)
            review_repo = SQLAlchemyCodeReviewRepository(session)
            t_repo = SQLAlchemyTaskRepository(session)
            service = CodeReviewService(change_repo=change_repo, review_repo=review_repo, task_repo=t_repo)

            change = await service.submit_code_change(
                project_id="proj-conc",
                task_id="task-conc-1",
                author_employee_id=f"emp-dev-{idx}",
                files_changed=[f"file_{idx}.py"],
                diff_summary=f"+ diff {idx}",
            )
            await session.commit()
            return change

    # Concurrently submit 5 code changes using separate sessions
    results = await asyncio.gather(*[submit_change(i) for i in range(5)])

    assert len(results) == 5
    for r in results:
        assert r.change_id is not None
        assert r.status == CodeChangeStatus.PROPOSED

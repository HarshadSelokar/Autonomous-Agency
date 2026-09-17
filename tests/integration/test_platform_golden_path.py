"""
Integration tests for Platform 1.0 Golden Path & Canonical Operating Workflows across all 30 phases.
"""

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.infrastructure.database import Base
from src.infrastructure.repositories.enterprise_repository import SQLAlchemyEnterpriseRepository
from src.infrastructure.repositories.resilience_repository import SQLAlchemyResilienceRepository
from src.application.platform_control_plane import CompanyLifecycleState, PlatformControlPlane
from src.application.workflows.platform_workflows import WorkflowCategory, WorkflowState
from src.application.security_incident_engine import SecurityIncidentEngine
from src.application.data_integrity_engine import DataIntegrityEngine
from src.domain.enterprise import Enterprise


@pytest_asyncio.fixture
async def async_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    await engine.dispose()


@pytest.mark.asyncio
async def test_platform_1_0_golden_path_integration(async_session: AsyncSession):
    ent_repo = SQLAlchemyEnterpriseRepository(async_session)
    res_repo = SQLAlchemyResilienceRepository(async_session)
    control_plane = PlatformControlPlane()
    security_engine = SecurityIncidentEngine(res_repo)
    integrity_engine = DataIntegrityEngine(res_repo)

    # 1. Enterprise Creation
    ent = Enterprise(name="Golden Path Enterprise", code="GOLD")
    saved_ent = await ent_repo.save_enterprise(ent)
    assert saved_ent.code == "GOLD"

    # 2. Company Readiness Evaluation & Lifecycle State Transition
    company_id = "comp-golden"
    readiness = control_plane.evaluate_company_readiness(company_id)
    assert readiness.is_ready is True

    state = control_plane.transition_company_state(company_id, CompanyLifecycleState.ACTIVE, readiness_result=readiness)
    assert state == CompanyLifecycleState.ACTIVE

    # 3. Canonical Workflow Execution
    workflow = control_plane.workflow_engine.start_workflow(
        name="Golden Path Execution",
        category=WorkflowCategory.OBJECTIVE_TO_EXECUTION,
        company_id=company_id,
    )
    assert workflow.state == WorkflowState.RUNNING

    control_plane.workflow_engine.advance_step(workflow.workflow_id, "2_EXECUTION")
    completed = control_plane.workflow_engine.transition_state(workflow.workflow_id, WorkflowState.COMPLETED)
    assert completed.state == WorkflowState.COMPLETED

    # 4. Security Isolation & Secret Redaction
    raw_secret = "User token ghp_123456789012345678901234567890123456"
    redacted = security_engine.redact_secrets(raw_secret)
    assert "[REDACTED_GITHUB_TOKEN]" in redacted

    # 5. Immutable Audit Hash Chaining
    log1 = await integrity_engine.log_mutation("agent_lead", "EXECUTE_WORKFLOW", workflow.workflow_id)
    assert log1.checksum is not None

    valid, errors = await integrity_engine.verify_audit_chain()
    assert valid is True
    assert len(errors) == 0

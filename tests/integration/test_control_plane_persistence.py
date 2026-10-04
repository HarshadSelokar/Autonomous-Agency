"""The control plane keeps its state in the database, not in the API process."""

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.api.main import app
from src.application.audit_governance_v2 import AuditGovernanceV2Service
from src.application.resilience_v2_engine import ResilienceV2Engine
from src.application.workflow_engine_v2 import WorkflowEngineV2
from src.domain.audit_v2 import AuditActionType
from src.domain.resilience_v2 import RecoveryActionType
from src.domain.workflow_v2 import WorkflowNode, WorkflowStatus
from src.infrastructure.database import Base, get_db_session
from src.infrastructure.models.audit_v2_model import AuditRecordV2Model
from src.infrastructure.models.outbox_model import OutboxMessageModel
from src.infrastructure.repositories.v2_repository import V2Repository


@pytest.fixture
def session_factory(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'v2.db'}")
    Base.metadata.create_all(engine)
    yield sessionmaker(bind=engine)
    engine.dispose()


def test_workflow_survives_a_new_engine_instance(session_factory):
    nodes = [WorkflowNode(id="build", name="Build"), WorkflowNode(id="test", name="Test", dependencies=["build"])]
    with session_factory() as session:
        engine = WorkflowEngineV2(V2Repository(session))
        definition = engine.create_definition("t1", "release", nodes)
        instance = engine.start_workflow("t1", definition.id, {"ref": "main"})
        engine.execute_step(instance.id, "build", {"artifact": "a.zip"})
        session.commit()

    # A fresh engine (as after a restart) picks the workflow up where it stopped
    with session_factory() as session:
        engine = WorkflowEngineV2(V2Repository(session))
        assert [n.id for n in engine.get_next_runnable_nodes(instance.id)] == ["test"]
        finished = engine.execute_step(instance.id, "test")
        session.commit()
        assert finished.status == WorkflowStatus.COMPLETED
        assert finished.execution_context == {"ref": "main", "build": {"artifact": "a.zip"}}

    with session_factory() as session:
        engine = WorkflowEngineV2(V2Repository(session))
        with pytest.raises(ValueError, match="not RUNNING"):
            engine.execute_step(instance.id, "build")
        with pytest.raises(ValueError, match="tenant mismatch"):
            engine.start_workflow("other-tenant", definition.id)


def test_audit_chain_continues_across_instances_and_detects_tampering(session_factory):
    with session_factory() as session:
        AuditGovernanceV2Service(V2Repository(session)).record_action("t1", "u1", AuditActionType.USER_AUTH, "login")
        session.commit()
    with session_factory() as session:
        service = AuditGovernanceV2Service(V2Repository(session))
        second = service.record_action("t1", "u1", AuditActionType.TENANT_ACCESS, "read")
        session.commit()
        chain = service.get_audit_trail("t1")
        assert len(chain) == 2
        assert second.prev_hash == chain[0].hash  # linked to the record written earlier
        assert service.verify_audit_chain("t1")

    with session_factory() as session:
        row = session.execute(select(AuditRecordV2Model).where(AuditRecordV2Model.resource == "login")).scalar_one()
        row.resource = "something else"
        session.commit()
    with session_factory() as session:
        assert not AuditGovernanceV2Service(V2Repository(session)).verify_audit_chain("t1")


def test_resilience_policy_and_fault_count_are_stored(session_factory):
    with session_factory() as session:
        engine = ResilienceV2Engine(V2Repository(session))
        policy = engine.get_policy("t1")
        policy.circuit_breaker_threshold = 2
        engine.set_policy(policy)
        engine.handle_fault("t1", "disk_error")
        session.commit()
    with session_factory() as session:
        engine = ResilienceV2Engine(V2Repository(session))
        assert engine.get_policy("t1").circuit_breaker_threshold == 2
        # The fault recorded before the "restart" counts: this second one trips the breaker
        assert engine.handle_fault("t1", "disk_error").action_taken == RecoveryActionType.ISOLATE_TENANT


@pytest.fixture
async def client():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)

    async def override_get_db_session():
        async with factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db_session] = override_get_db_session
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as http:
        yield http, factory
    app.dependency_overrides.clear()
    await engine.dispose()


async def test_control_plane_api_persists_audit_and_queues_the_event(client):
    http, factory = client
    tenant_id = (await http.post("/tenants", json={"name": "Acme", "slug": "acme"})).json()["id"]
    headers = {"X-Tenant-ID": tenant_id, "X-User-ID": "user-1"}

    executed = await http.post("/control-plane/execute", json={"action": "run_workflow"}, headers=headers)
    assert executed.status_code == 200, executed.text
    assert executed.json()["status"] == "SUCCESS"
    assert executed.json()["selected_model"]
    await http.post("/control-plane/execute", json={"action": "second"}, headers=headers)

    overview = (await http.get(f"/control-plane/overview/{tenant_id}", headers=headers)).json()
    assert overview["tenant_name"] == "Acme"
    assert overview["audit_trail_count"] == 2  # counted from the database, across requests
    assert overview["audit_chain_intact"] is True
    assert overview["resilience_policy"]["max_retries"] == 3

    async with factory() as session:
        queued = (await session.execute(select(OutboxMessageModel))).scalars().all()
    assert [(m.event_type, m.status, m.tenant_id) for m in queued] == [
        ("control_plane.request.executed", "PENDING", tenant_id)
    ] * 2


async def test_control_plane_rejects_unknown_tenant_and_over_budget_requests(client):
    http, _ = client
    missing = await http.post("/control-plane/execute", json={"action": "x"}, headers={"X-Tenant-ID": "nope"})
    assert missing.status_code == 404
    assert (await http.post("/control-plane/execute", json={"action": "x"})).status_code == 400
    assert (await http.get("/control-plane/overview/nope", headers={"X-Tenant-ID": "nope"})).status_code == 404

    tenant_id = (await http.post("/tenants", json={"name": "Acme", "slug": "acme"})).json()["id"]
    headers = {"X-Tenant-ID": tenant_id}
    within = await http.post(
        "/control-plane/execute", json={"action": "x", "task_data": {"estimated_cost": 60}}, headers=headers
    )
    assert within.status_code == 200, within.text
    assert within.json()["execution_trace"]["budget_reserved"] == 60
    # The default budget is 100; a second 60 does not fit
    over = await http.post(
        "/control-plane/execute", json={"action": "y", "task_data": {"estimated_cost": 60}}, headers=headers
    )
    assert over.status_code == 402
    overview = (await http.get(f"/control-plane/overview/{tenant_id}", headers=headers)).json()
    assert overview["audit_trail_count"] == 1  # the refused request left no audit record

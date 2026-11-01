"""Security tests: rows written by one tenant are invisible to another, on every table."""

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.api.main import app
from src.infrastructure.config import settings
from src.infrastructure.database import Base, get_db_session
from src.infrastructure.models.outbox_model import OutboxMessageModel
from src.infrastructure.models.tenant_model import TenantModel
from src.infrastructure.tenant_context import _current_tenant_id

ADMIN_KEY = "test-admin-api-key"
ADMIN = {"X-API-Key": ADMIN_KEY}
PASSWORD = "correct horse battery"


class as_tenant:
    def __init__(self, tenant_id: str | None) -> None:
        self.tenant_id = tenant_id

    def __enter__(self) -> None:
        self.token = _current_tenant_id.set(self.tenant_id)

    def __exit__(self, *exc: object) -> None:
        _current_tenant_id.reset(self.token)


@pytest.fixture
async def session_factory():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield async_sessionmaker(engine, expire_on_commit=False)
    await engine.dispose()


def message(message_id: str) -> OutboxMessageModel:
    return OutboxMessageModel(id=message_id, event_type="E", payload_json="{}", status="PENDING")


async def ids(factory) -> list[str]:
    async with factory() as db:
        return sorted((await db.execute(select(OutboxMessageModel.id))).scalars().all())


def test_every_table_has_a_tenant_column():
    import src.infrastructure.models  # noqa: F401

    assert [name for name, table in Base.metadata.tables.items() if "tenant_id" not in table.c] == []


async def test_rows_are_stamped_and_reads_are_scoped(session_factory):
    for tenant, message_id in (("t-a", "a1"), ("t-b", "b1"), (None, "shared")):
        with as_tenant(tenant):
            async with session_factory() as db:
                db.add(message(message_id))
                await db.commit()

    with as_tenant("t-a"):
        assert await ids(session_factory) == ["a1"]
        async with session_factory() as db:
            assert await db.get(OutboxMessageModel, "b1") is None  # primary-key lookup is scoped too
            assert (await db.get(OutboxMessageModel, "a1")).tenant_id == "t-a"
    with as_tenant("t-b"):
        assert await ids(session_factory) == ["b1"]
    # No tenant bound (platform admin, workers): everything is visible
    assert await ids(session_factory) == ["a1", "b1", "shared"]


async def test_updates_and_deletes_cannot_reach_another_tenant(session_factory):
    for tenant, message_id in (("t-a", "a1"), ("t-b", "b1")):
        with as_tenant(tenant):
            async with session_factory() as db:
                db.add(message(message_id))
                await db.commit()

    with as_tenant("t-a"):
        async with session_factory() as db:
            await db.execute(update(OutboxMessageModel).values(status="HIJACKED"))
            await db.execute(delete(OutboxMessageModel).where(OutboxMessageModel.id == "b1"))
            await db.commit()

    async with session_factory() as db:
        rows = {m.id: m.status for m in (await db.execute(select(OutboxMessageModel))).scalars()}
    assert rows == {"a1": "HIJACKED", "b1": "PENDING"}


async def test_explicit_tenant_is_not_overwritten_by_the_context(session_factory):
    with as_tenant("t-a"):
        async with session_factory() as db:
            row = message("x1")
            row.tenant_id = "t-explicit"
            db.add(row)
            await db.commit()
    async with session_factory() as db:
        assert (await db.get(OutboxMessageModel, "x1")).tenant_id == "t-explicit"


async def test_tenant_row_belongs_to_itself(session_factory):
    async with session_factory() as db:
        db.add(TenantModel(id="t-a", name="A", slug="a"))
        db.add(TenantModel(id="t-b", name="B", slug="b"))
        await db.commit()
    with as_tenant("t-a"):
        async with session_factory() as db:
            assert (await db.execute(select(TenantModel.id))).scalars().all() == ["t-a"]


@pytest.fixture
async def client(monkeypatch: pytest.MonkeyPatch, session_factory) -> AsyncClient:
    monkeypatch.setattr(settings, "AUTH_REQUIRED", True)
    monkeypatch.setattr(settings, "ADMIN_API_KEY", ADMIN_KEY)

    async def override_get_db_session():
        async with session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db_session] = override_get_db_session
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as http:
        yield http
    app.dependency_overrides.clear()


async def token_for(client: AsyncClient, slug: str) -> dict[str, str]:
    tenant = await client.post("/tenants", json={"name": slug, "slug": slug}, headers=ADMIN)
    tenant_id = tenant.json()["id"]
    email = f"user@{slug}.example.com"
    created = await client.post(
        "/identity/users",
        json={"tenant_id": tenant_id, "email": email, "full_name": "U", "password": PASSWORD},
        headers=ADMIN,
    )
    assert created.status_code == 201, created.text
    login = await client.post("/auth/login", json={"email": email, "password": PASSWORD})
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


async def test_api_data_is_isolated_between_tenants_on_a_table_with_no_tenant_logic(client: AsyncClient):
    """Governance has no tenant code of its own; isolation comes entirely from the ORM scoping."""
    alpha = await token_for(client, "alpha")
    beta = await token_for(client, "beta")
    approval = {"action_type": "DEPLOY", "action_target": "prod", "requested_by_actor_id": "e1", "risk_level": "HIGH"}

    created = await client.post("/governance/approvals", json=approval, headers=alpha)
    assert created.status_code == 201, created.text
    request_id = created.json()["request_id"]

    assert [r["request_id"] for r in (await client.get("/governance/approvals", headers=alpha)).json()] == [request_id]
    assert (await client.get("/governance/approvals", headers=beta)).json() == []
    # Beta cannot act on Alpha's approval even knowing its id
    hijack = await client.post(f"/governance/approvals/{request_id}/approve", json={"actor_id": "x"}, headers=beta)
    assert hijack.status_code == 400
    # The platform admin, with no tenant selected, sees it
    assert len((await client.get("/governance/approvals", headers=ADMIN)).json()) == 1
    # ...and can scope to one tenant with the header
    tenant_beta = (await client.get("/auth/me", headers=beta)).json()["tenant_id"]
    assert (await client.get("/governance/approvals", headers={**ADMIN, "X-Tenant-ID": tenant_beta})).json() == []

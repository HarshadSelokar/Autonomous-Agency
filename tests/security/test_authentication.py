"""Security tests: authentication is enforced and the tenant comes from the credential."""

from datetime import UTC, datetime, timedelta

import jwt
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.api.main import app
from src.infrastructure.config import settings
from src.infrastructure.database import Base, get_db_session
from src.infrastructure.security.passwords import hash_password, verify_password
from src.infrastructure.security.tokens import create_access_token

ADMIN_KEY = "test-admin-api-key"
ADMIN = {"X-API-Key": ADMIN_KEY}
PASSWORD = "correct horse battery"


@pytest.fixture
async def client(monkeypatch: pytest.MonkeyPatch) -> AsyncClient:
    monkeypatch.setattr(settings, "AUTH_REQUIRED", True)
    monkeypatch.setattr(settings, "ADMIN_API_KEY", ADMIN_KEY)

    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

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
    await engine.dispose()


async def make_tenant(client: AsyncClient, slug: str) -> str:
    res = await client.post("/tenants", json={"name": f"Tenant {slug}", "slug": slug}, headers=ADMIN)
    assert res.status_code == 201, res.text
    return res.json()["id"]


async def make_user_token(client: AsyncClient, tenant_id: str, email: str) -> str:
    res = await client.post(
        "/identity/users",
        json={"tenant_id": tenant_id, "email": email, "full_name": "User", "password": PASSWORD},
        headers=ADMIN,
    )
    assert res.status_code == 201, res.text
    login = await client.post("/auth/login", json={"email": email, "password": PASSWORD})
    assert login.status_code == 200, login.text
    return login.json()["access_token"]


def bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_password_hashing_round_trip():
    stored = hash_password(PASSWORD)
    assert PASSWORD not in stored
    assert stored != hash_password(PASSWORD)  # salted
    assert verify_password(PASSWORD, stored)
    assert not verify_password("wrong", stored)
    assert not verify_password(PASSWORD, None)
    assert not verify_password(PASSWORD, "not-a-hash")


@pytest.mark.parametrize("path", ["/tenants", "/agents", "/studio/projects", "/governance/violations", "/auth/me"])
async def test_requests_without_credentials_are_rejected(client: AsyncClient, path: str):
    res = await client.get(path)
    assert res.status_code == 401
    assert res.json() == {"detail": "Authentication required."}


async def test_health_stays_public(client: AsyncClient):
    assert (await client.get("/health/live")).status_code == 200


async def test_invalid_credentials_are_rejected(client: AsyncClient):
    assert (await client.get("/tenants", headers={"X-API-Key": "wrong"})).status_code == 401
    assert (await client.get("/tenants", headers=bearer("not.a.token"))).status_code == 401

    forged = jwt.encode(
        {"sub": "u", "tid": "t", "adm": True, "exp": datetime.now(UTC) + timedelta(hours=1)},
        "some-other-secret-that-is-long-enough",
        algorithm="HS256",
    )
    assert (await client.get("/tenants", headers=bearer(forged))).status_code == 401

    expired = create_access_token("u", "t", ttl_minutes=-1)
    assert (await client.get("/tenants", headers=bearer(expired))).status_code == 401


async def test_unset_admin_api_key_never_matches(client: AsyncClient, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(settings, "ADMIN_API_KEY", "")
    assert (await client.get("/tenants", headers={"X-API-Key": ""})).status_code == 401
    assert (await client.get("/tenants", headers={"X-API-Key": "anything"})).status_code == 401


async def test_login_and_wrong_password(client: AsyncClient):
    tenant_id = await make_tenant(client, "alpha")
    token = await make_user_token(client, tenant_id, "alice@example.com")

    me = await client.get("/auth/me", headers=bearer(token))
    assert me.status_code == 200
    assert me.json()["tenant_id"] == tenant_id
    assert me.json()["is_platform_admin"] is False

    wrong = await client.post("/auth/login", json={"email": "alice@example.com", "password": "nope-nope-nope"})
    unknown = await client.post("/auth/login", json={"email": "nobody@example.com", "password": PASSWORD})
    assert wrong.status_code == unknown.status_code == 401
    assert wrong.json() == unknown.json()  # no way to tell which emails exist


async def test_tenant_comes_from_token_not_from_header(client: AsyncClient):
    tenant_a = await make_tenant(client, "alpha")
    tenant_b = await make_tenant(client, "beta")
    token_a = await make_user_token(client, tenant_a, "alice@example.com")

    own = await client.get(f"/tenants/{tenant_a}", headers=bearer(token_a))
    assert own.status_code == 200
    assert own.headers["X-Tenant-ID"] == tenant_a

    # Claiming another tenant in the header is refused outright
    spoofed = await client.get(f"/tenants/{tenant_a}", headers={**bearer(token_a), "X-Tenant-ID": tenant_b})
    assert spoofed.status_code == 403

    # And another tenant's resource is not readable
    other = await client.get(f"/tenants/{tenant_b}", headers=bearer(token_a))
    assert other.status_code == 403


async def test_tenant_user_cannot_use_admin_routes_or_escalate(client: AsyncClient):
    tenant_a = await make_tenant(client, "alpha")
    tenant_b = await make_tenant(client, "beta")
    token_a = await make_user_token(client, tenant_a, "alice@example.com")
    headers = bearer(token_a)

    assert (await client.get("/tenants", headers=headers)).status_code == 403
    assert (await client.post("/tenants", json={"name": "Mine", "slug": "mine"}, headers=headers)).status_code == 403
    assert (await client.delete(f"/tenants/{tenant_a}", headers=headers)).status_code == 403

    new_user = {"email": "eve@example.com", "full_name": "Eve", "password": PASSWORD}
    # No membership grants user:write, so creating users is refused even in the own tenant
    own = await client.post("/identity/users", json={**new_user, "tenant_id": tenant_a}, headers=headers)
    assert own.status_code == 403
    cross = await client.post("/identity/users", json={**new_user, "tenant_id": tenant_b}, headers=headers)
    assert cross.status_code == 403


async def test_only_platform_admin_can_grant_platform_admin(client: AsyncClient):
    tenant_id = await make_tenant(client, "alpha")
    owner_token = await make_user_token(client, tenant_id, "owner@example.com")
    me = (await client.get("/auth/me", headers=bearer(owner_token))).json()
    org = await client.post(
        "/identity/organizations", json={"tenant_id": tenant_id, "name": "Eng", "slug": "eng"}, headers=ADMIN
    )
    membership = await client.post(
        "/identity/memberships",
        json={"tenant_id": tenant_id, "organization_id": org.json()["id"], "user_id": me["user_id"], "role": "TENANT_OWNER"},
        headers=ADMIN,
    )
    assert membership.status_code == 201, membership.text

    # A tenant owner may create ordinary users in their tenant...
    ordinary = await client.post(
        "/identity/users",
        json={"tenant_id": tenant_id, "email": "bob@example.com", "full_name": "Bob", "password": PASSWORD},
        headers=bearer(owner_token),
    )
    assert ordinary.status_code == 201, ordinary.text
    # ...but not mint a platform administrator
    escalation = await client.post(
        "/identity/users",
        json={"tenant_id": tenant_id, "email": "root@example.com", "full_name": "Root",
              "password": PASSWORD, "is_platform_admin": True},
        headers=bearer(owner_token),
    )
    assert escalation.status_code == 403


async def test_office_websocket_requires_token(monkeypatch: pytest.MonkeyPatch):
    from starlette.testclient import TestClient
    from starlette.websockets import WebSocketDisconnect

    monkeypatch.setattr(settings, "AUTH_REQUIRED", True)
    with TestClient(app) as sync_client:
        with pytest.raises(WebSocketDisconnect):
            with sync_client.websocket_connect("/office/ws"):
                pass

        token = create_access_token("u1", "t1")
        with sync_client.websocket_connect(f"/office/ws?token={token}") as ws:
            ws.send_text("ping")
            assert ws.receive_text() == "pong"

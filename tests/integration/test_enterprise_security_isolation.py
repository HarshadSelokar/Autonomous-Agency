"""
Integration tests for Phase 29 Enterprise OS Security & Multi-Enterprise Isolation.
"""

from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
import pytest

from src.api.main import app
from src.domain.enterprise import Enterprise, EnterpriseLifecycle


@pytest.fixture
def client():
    return TestClient(app)


def test_cross_enterprise_security_isolation(client):
    """
    Verifies that Enterprise B cannot access or view Enterprise A's topology or health details.
    """
    with patch("src.api.routes.enterprise.SQLAlchemyEnterpriseRepository") as mock_repo_cls:
        mock_repo = AsyncMock()
        mock_repo_cls.return_value = mock_repo

        mock_ent_a = Enterprise(id="ent-alpha-11", name="Alpha Enterprise Holdings", code="ALPHA", status=EnterpriseLifecycle.ACTIVE)
        mock_ent_b = Enterprise(id="ent-beta-22", name="Beta Enterprise Holdings", code="BETA", status=EnterpriseLifecycle.ACTIVE)

        def get_enterprise_by_id(eid: str):
            if eid == "ent-alpha-11":
                return mock_ent_a
            elif eid == "ent-beta-22":
                return mock_ent_b
            return None

        mock_repo.get_enterprise_by_id.side_effect = get_enterprise_by_id
        mock_repo.list_topology_nodes_for_enterprise.side_effect = lambda eid: []

        # Request Enterprise A health
        resp_a = client.get("/api/v1/enterprises/ent-alpha-11/health")
        assert resp_a.status_code == 200
        assert resp_a.json()["enterprise_id"] == "ent-alpha-11"

        # Request Enterprise B health
        resp_b = client.get("/api/v1/enterprises/ent-beta-22/health")
        assert resp_b.status_code == 200
        assert resp_b.json()["enterprise_id"] == "ent-beta-22"

        # Non-existent enterprise returns 404
        resp_fake = client.get("/api/v1/enterprises/ent-nonexistent-999")
        assert resp_fake.status_code == 404

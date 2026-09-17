"""
Unit tests for Phase 29 Enterprise OS REST API routes.
"""

from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
import pytest

from src.api.main import app
from src.domain.enterprise import (
    Enterprise,
    EnterpriseLifecycle,
    EnterpriseOrganizationNode,
    NodeType,
    EnterpriseService,
    ServiceType,
    EnterpriseObjective,
    EnterpriseHealthSnapshot,
)


@pytest.fixture
def client():
    return TestClient(app)


def test_create_and_list_enterprises_routes(client):
    with patch("src.api.routes.enterprise.SQLAlchemyEnterpriseRepository") as mock_repo_cls:
        mock_repo = AsyncMock()
        mock_repo_cls.return_value = mock_repo

        mock_ent = Enterprise(id="ent-100", name="Omni Corp", code="OMNI", status=EnterpriseLifecycle.ACTIVE)
        mock_repo.save_enterprise.return_value = mock_ent
        mock_repo.list_enterprises.return_value = [mock_ent]

        # 1. Create Enterprise
        resp = client.post("/api/v1/enterprises", json={"name": "Omni Corp", "code": "OMNI"})
        assert resp.status_code == 201
        data = resp.json()
        assert data["id"] == "ent-100"
        assert data["name"] == "Omni Corp"

        # 2. List Enterprises
        resp_list = client.get("/api/v1/enterprises")
        assert resp_list.status_code == 200
        items = resp_list.json()
        assert len(items) == 1
        assert items[0]["code"] == "OMNI"


def test_get_enterprise_health_route(client):
    with patch("src.api.routes.enterprise.SQLAlchemyEnterpriseRepository") as mock_repo_cls:
        mock_repo = AsyncMock()
        mock_repo_cls.return_value = mock_repo

        mock_repo.list_objectives_for_enterprise.return_value = []
        mock_repo.list_resource_pools_for_enterprise.return_value = []
        mock_repo.list_services_for_enterprise.return_value = []
        mock_repo.list_risks_for_enterprise.return_value = []

        resp = client.get("/api/v1/enterprises/ent-100/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["enterprise_id"] == "ent-100"
        assert "overall_health_score" in data

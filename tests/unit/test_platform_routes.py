"""
Unit tests for Platform 1.0 Control Plane REST API routes.
"""

from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
import pytest

from src.api.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_control_plane_overview_route(client):
    resp = client.get("/api/v1/platform/control-plane")
    assert resp.status_code == 200
    data = resp.json()
    assert data["version"] == "1.0.0"
    assert data["status"] == "OPERATIONAL"
    assert "overall_health_score" in data


def test_company_and_enterprise_bootstrap_routes(client):
    # 1. Company Bootstrap
    resp_comp = client.post(
        "/api/v1/platform/companies/bootstrap",
        json={"company_name": "Apex AI Corp", "code": "APEX", "activate_immediately": True},
    )
    assert resp_comp.status_code == 200
    data_comp = resp_comp.json()
    assert data_comp["company_id"] == "comp-apex"
    assert data_comp["lifecycle_state"] == "ACTIVE"
    assert data_comp["is_ready"] is True

    # 2. Enterprise Bootstrap
    resp_ent = client.post(
        "/api/v1/platform/enterprises/bootstrap",
        json={"enterprise_name": "Apex Enterprise Systems", "code": "APEX_ENT"},
    )
    assert resp_ent.status_code == 200
    data_ent = resp_ent.json()
    assert data_ent["enterprise_id"] == "ent-apex_ent"
    assert data_ent["is_ready"] is True


def test_platform_views_and_search_routes(client):
    # Executive view
    resp_exec = client.get("/api/v1/platform/views/executive")
    assert resp_exec.status_code == 200
    assert resp_exec.json()["platform_version"] == "1.0.0"

    # Search
    resp_search = client.get("/api/v1/platform/search?q=ARR")
    assert resp_search.status_code == 200
    assert resp_search.json()["results_count"] > 0

    # Onboarding
    resp_onboarding = client.get("/api/v1/platform/onboarding")
    assert resp_onboarding.status_code == 200
    assert resp_onboarding.json()["onboarding_completed"] is True

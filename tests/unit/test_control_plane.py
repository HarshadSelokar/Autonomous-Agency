"""
Unit tests for Unified Autonomous Operations Control Plane (Phase 41).
"""

import pytest
from src.application.control_plane import ControlPlane
from src.domain.tenant import TenantStatus


@pytest.mark.asyncio
async def test_control_plane_tenant_overview():
    cp = ControlPlane()
    tenant_id = "acme-tenant"

    overview = await cp.get_tenant_overview(tenant_id)
    assert overview["tenant_id"] == tenant_id
    assert overview["tenant_status"] == TenantStatus.ACTIVE.value
    assert overview["active_workforce"] == 0
    assert overview["audit_trail_count"] == 0


def test_control_plane_execute_request_end_to_end():
    cp = ControlPlane()
    tenant_id = "globex-tenant"

    res = cp.execute_tenant_request(
        tenant_id=tenant_id,
        actor_id="user-globex-admin",
        action="deploy_agent_swarm",
        task_data={"swarm_name": "alpha_swarm"},
    )

    assert res["status"] == "SUCCESS"
    assert res["tenant_id"] == tenant_id
    assert res["action"] == "deploy_agent_swarm"
    assert res["selected_model"] is not None
    assert res["execution_trace"]["audit_logged"] is True
    assert res["execution_trace"]["event_published"] is True

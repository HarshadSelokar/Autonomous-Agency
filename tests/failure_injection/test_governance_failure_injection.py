"""
Failure Injection Tests for Governance and Model Router Resilience.
"""

from datetime import datetime, timedelta, timezone
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import src.infrastructure.models  # noqa: F401
from src.application.governance_service import GovernanceService
from src.application.model_router import ModelRouter
from src.domain.governance import (
    ApprovalStatus,
    RiskLevel,
    ViolationCategory,
)
from src.domain.model_routing import (
    ModelCapability,
    ModelSelectionRequest,
    RoutingStrategy,
)
from src.infrastructure.database import Base
from src.infrastructure.repositories.governance_repository import GovernanceRepository
from src.infrastructure.repositories.model_routing_repository import ModelRoutingRepository


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()


@pytest.fixture
def governance_service(db_session):
    repo = GovernanceRepository(db_session)
    return GovernanceService(repository=repo)


@pytest.fixture
def model_router(db_session):
    repo = ModelRoutingRepository(db_session)
    return ModelRouter(repository=repo)


def test_stale_approval_request_rejection(governance_service):
    # Request approval with 1 second validity
    req = governance_service.request_approval(
        action_type="UPDATE_DB_SCHEMA",
        action_target="prod_db",
        requested_by_actor_id="dev-1",
        risk_level=RiskLevel.HIGH,
        validity_seconds=-10,  # Already expired in past!
    )

    # Attempt approving expired request
    with pytest.raises(ValueError, match="expired"):
        governance_service.approve_request(request_id=req.request_id, approver_actor_id="mgr-1")

    # Verify status changed to EXPIRED and violation recorded
    updated_req_model = governance_service._repository.get_approval_request(req.request_id)
    assert updated_req_model.status == ApprovalStatus.EXPIRED.value

    violations = governance_service._repository.get_violations()
    assert any(v.category == ViolationCategory.STALE_APPROVAL.value for v in violations)


def test_provider_outage_fallback_routing(model_router):
    # Register Model A (Primary, High Quality) and Model B (Secondary, Backup)
    model_router.register_model_profile(
        model_id="primary-llm-70b",
        provider_name="PrimaryProvider",
        model_name="LLM 70B",
        capabilities=[ModelCapability.TEXT_GENERATION, ModelCapability.CODE_GENERATION],
        quality_score=0.95,
        is_active=True,
    )
    model_router.register_model_profile(
        model_id="backup-llm-8b",
        provider_name="BackupProvider",
        model_name="LLM 8B",
        capabilities=[ModelCapability.TEXT_GENERATION, ModelCapability.CODE_GENERATION],
        quality_score=0.80,
        is_active=True,
    )

    # Inject Provider Outage for PrimaryProvider
    model_router.update_provider_health(
        provider_name="PrimaryProvider",
        model_id="primary-llm-70b",
        is_healthy=False,
        error_rate=0.99,
        last_failure_reason="503 Service Unavailable / Connection Timeout",
    )

    req = ModelSelectionRequest(
        request_id="req-outage-1",
        required_capabilities=[ModelCapability.CODE_GENERATION],
        strategy=RoutingStrategy.QUALITY_AWARE,
    )

    decision = model_router.route_model(req)
    # Router must fall back to backup-llm-8b
    assert decision.selected_model_id == "backup-llm-8b"
    assert "Provider model unhealthy" in decision.rejected_candidates["primary-llm-70b"]

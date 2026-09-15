"""
Security and Policy Isolation Tests for Phase 11 & Phase 12 Governance & Model Routing.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import src.infrastructure.models  # noqa: F401
from src.application.governance_service import GovernanceService
from src.application.model_router import ModelRouter
from src.domain.governance import (
    ApprovalStatus,
    GovernanceScope,
    RiskLevel,
    ViolationCategory,
)
from src.domain.model_routing import (
    ModelCapability,
    ModelProfile,
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


def test_self_approval_prevention_records_violation(governance_service):
    # Request approval by emp-1
    req = governance_service.request_approval(
        action_type="FINANCIAL_TRANSFER",
        action_target="bank_account_x",
        requested_by_actor_id="emp-1",
        risk_level=RiskLevel.HIGH,
        prohibit_self_approval=True,
    )
    assert req.status == ApprovalStatus.PENDING

    # Attempt self-approval by emp-1
    with pytest.raises(ValueError, match="Self-approval prohibited"):
        governance_service.approve_request(request_id=req.request_id, approver_actor_id="emp-1")

    # Check policy violation was recorded
    violations = governance_service._repository.get_violations()
    assert len(violations) >= 1
    assert violations[0].category == ViolationCategory.SEPARATION_OF_DUTIES_VIOLATION.value
    assert violations[0].actor_id == "emp-1"


def test_kill_switch_bypass_prevention(governance_service):
    # Activate Emergency Stop for global
    governance_service.activate_emergency_stop(
        activated_by_actor_id="ciso-1",
        reason="Ransomware attack detected",
        scope=GovernanceScope.GLOBAL,
        scope_id="GLOBAL",
    )

    # Attempt evaluating autonomy under active emergency stop
    autonomy, risk, rule = governance_service.evaluate_autonomy(
        action_type="ANY_ACTION",
        action_target="any_target",
        actor_id="emp-99",
    )
    assert autonomy.value == "BLOCKED"
    assert risk.value == "CRITICAL"


def test_model_routing_blocklist_security(model_router):
    # Register model A and model B
    m_a = ModelProfile(
        model_id="unapproved-experimental-model",
        provider_name="untrusted-provider",
        model_name="Experimental Model",
        capabilities=[ModelCapability.TEXT_GENERATION, ModelCapability.CODE_GENERATION],
        quality_score=0.99,
        is_approved_for_production=False,  # Unapproved!
    )
    m_b = ModelProfile(
        model_id="safe-prod-model",
        provider_name="Groq",
        model_name="Llama 3 70B",
        capabilities=[ModelCapability.TEXT_GENERATION, ModelCapability.CODE_GENERATION],
        quality_score=0.85,
        is_approved_for_production=True,
    )
    model_router.register_model_profile(
        model_id=m_a.model_id,
        provider_name=m_a.provider_name,
        model_name=m_a.model_name,
        capabilities=m_a.capabilities,
        quality_score=m_a.quality_score,
        is_approved_for_production=False,
    )
    model_router.register_model_profile(
        model_id=m_b.model_id,
        provider_name=m_b.provider_name,
        model_name=m_b.model_name,
        capabilities=m_b.capabilities,
        quality_score=m_b.quality_score,
        is_approved_for_production=True,
    )

    req = ModelSelectionRequest(
        request_id="req-sec-1",
        required_capabilities=[ModelCapability.CODE_GENERATION],
        strategy=RoutingStrategy.QUALITY_AWARE,
        blocklist_models=["unapproved-experimental-model"],
    )

    decision = model_router.route_model(req)
    # Must select safe-prod-model despite lower quality score because unapproved is blocklisted
    assert decision.selected_model_id == "safe-prod-model"
    assert "unapproved-experimental-model" in decision.rejected_candidates

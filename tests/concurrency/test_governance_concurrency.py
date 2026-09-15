"""
Concurrency Tests for Governance Approval Requests and Emergency Stop.
"""

from concurrent.futures import ThreadPoolExecutor
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import src.infrastructure.models  # noqa: F401
from src.application.governance_service import GovernanceService
from src.domain.governance import (
    ApprovalStatus,
    GovernanceScope,
    RiskLevel,
)
from src.infrastructure.database import Base
from src.infrastructure.repositories.governance_repository import GovernanceRepository


@pytest.fixture
def session_factory():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)


def test_concurrent_approval_decision_race(session_factory):
    # Setup initial request
    session = session_factory()
    repo = GovernanceRepository(session)
    service = GovernanceService(repository=repo)

    req = service.request_approval(
        action_type="DELETE_DATABASE",
        action_target="prod",
        requested_by_actor_id="agent-rogue-1",
        risk_level=RiskLevel.CRITICAL,
        prohibit_self_approval=True,
    )
    req_id = req.request_id
    session.close()

    approvers = [f"mgr-{i}" for i in range(10)]
    results = []
    errors = []

    def try_approve(mgr_id: str):
        t_session = session_factory()
        t_repo = GovernanceRepository(t_session)
        t_service = GovernanceService(repository=t_repo)
        try:
            res = t_service.approve_request(req_id, mgr_id)
            results.append(res)
        except Exception as e:
            errors.append(str(e))
        finally:
            t_session.close()

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(try_approve, mgr) for mgr in approvers]
        for f in futures:
            f.result()

    # Exactly one approval succeeds, rest fail because status is no longer PENDING
    assert len(results) == 1
    assert results[0].status == ApprovalStatus.APPROVED
    assert len(errors) == 9
    assert all("not in PENDING state" in err or "expected PENDING" in err for err in errors)


def test_concurrent_emergency_stop_activation(session_factory):
    admin_ids = [f"admin-{i}" for i in range(5)]
    stops = []

    def activate_stop(admin_id: str):
        t_session = session_factory()
        t_repo = GovernanceRepository(t_session)
        t_service = GovernanceService(repository=t_repo)
        try:
            stop = t_service.activate_emergency_stop(
                activated_by_actor_id=admin_id,
                reason=f"Emergency trigger by {admin_id}",
                scope=GovernanceScope.GLOBAL,
                scope_id="GLOBAL",
            )
            stops.append(stop)
        finally:
            t_session.close()

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(activate_stop, adm) for adm in admin_ids]
        for f in futures:
            f.result()

    assert len(stops) == 5

    # Check emergency stop active on main session
    session = session_factory()
    service = GovernanceService(GovernanceRepository(session))
    assert service.is_emergency_stopped(GovernanceScope.GLOBAL, "GLOBAL") is True
    session.close()

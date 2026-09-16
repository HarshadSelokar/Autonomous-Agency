"""
Concurrency & Race Condition Tests for Phase 10 Verification Engine.
"""

import asyncio

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import src.infrastructure.models  # noqa: F401
from src.application.verification_engine import VerificationEngine
from src.domain.verification import (
    EvidenceTrustLevel,
    VerificationRule,
    VerificationStatus,
    VerificationType,
)
from src.infrastructure.database import Base
from src.infrastructure.repositories.verification_repository import VerificationRepository


@pytest.fixture
def verification_engine():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    repo = VerificationRepository(Session())
    return VerificationEngine(repository=repo)


@pytest.mark.asyncio
async def test_concurrent_verification_requests(verification_engine):
    task_id = "task-conc-100"

    rule = VerificationRule(
        rule_id="r1",
        rule_type=VerificationType.FILE_VERIFICATION,
        name="File Check",
        description="Verify file",
        target="data.json",
        expected_condition={"exists": True},
    )
    verification_engine.define_expected_outcome(task_id=task_id, description="Concurrent Task", criteria=[], rules=[rule])
    verification_engine.add_evidence(
        source_type="ToolExecution",
        source_id="te-conc-1",
        task_id=task_id,
        trust_level=EvidenceTrustLevel.EXECUTED,
        payload={"file": "data.json", "exists": True},
    )

    # Launch 5 concurrent verification tasks
    async def run_verif():
        return verification_engine.verify_task(task_id=task_id)

    results = await asyncio.gather(*(run_verif() for _ in range(5)))

    assert len(results) == 5
    for r in results:
        assert r.status == VerificationStatus.VERIFIED
        assert r.is_verified

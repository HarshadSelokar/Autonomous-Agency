"""
Unit tests for Phase 29 Enterprise OS application services.
"""

from datetime import datetime, timedelta, timezone, UTC
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.infrastructure.database import Base
from src.infrastructure.repositories.enterprise_repository import SQLAlchemyEnterpriseRepository
from src.application.enterprise_topology_service import EnterpriseTopologyService
from src.application.enterprise_federation_service import EnterpriseFederationService
from src.application.enterprise_strategy_service import EnterpriseStrategyService
from src.application.enterprise_governance_service import EnterpriseGovernanceService
from src.application.enterprise_health_service import EnterpriseHealthAndIntelligenceService
from src.application.enterprise_context_builder import EnterpriseContextBuilder
from src.domain.enterprise import (
    Enterprise,
    NodeType,
    RelationshipType,
    ServiceType,
    PortfolioCategory,
    ObjectiveScope,
)
from src.domain.exceptions import (
    InvalidTopologyCycleError,
    AuthorityExpiredError,
    ResourceAllocationConflictError,
    UnauthorizedEnterpriseActionError,
)


@pytest_asyncio.fixture
async def async_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    await engine.dispose()


@pytest.mark.asyncio
async def test_topology_cycle_detection(async_session: AsyncSession):
    repo = SQLAlchemyEnterpriseRepository(async_session)
    top_svc = EnterpriseTopologyService(repo)

    ent = await repo.save_enterprise(Enterprise(name="Cycle Test Ent", code="CTEST"))

    n1 = await top_svc.create_node(ent.id, "Node A", NodeType.COMPANY)
    n2 = await top_svc.create_node(ent.id, "Node B", NodeType.SUBSIDIARY, parent_node_id=n1.id)

    # Attempt to make N1 child of N2 -> Cycle!
    with pytest.raises(InvalidTopologyCycleError):
        await top_svc.add_relationship(ent.id, source_node_id=n2.id, target_node_id=n1.id, relationship_type=RelationshipType.PARENT_CHILD)


@pytest.mark.asyncio
async def test_federation_and_intercompany_request(async_session: AsyncSession):
    repo = SQLAlchemyEnterpriseRepository(async_session)
    fed_svc = EnterpriseFederationService(repo)

    ent = await repo.save_enterprise(Enterprise(name="Federation Ent", code="FEDENT"))

    c1 = await fed_svc.attach_company_to_enterprise(ent.id, "comp-001", "Company 1")
    c2 = await fed_svc.attach_company_to_enterprise(ent.id, "comp-002", "Company 2")

    req = await fed_svc.submit_intercompany_request(
        enterprise_id=ent.id,
        source_company_id="comp-001",
        destination_company_id="comp-002",
        requester_id="req-user",
        requested_capability="INVENTORY_AUDIT",
        purpose="Q4 Audit",
    )
    assert req.id is not None

    auth_req = await fed_svc.authorize_intercompany_request(req.id, ent.id, "gov-appr-999")
    assert auth_req.governance_approval_id == "gov-appr-999"

    exec_req = await fed_svc.execute_intercompany_request(req.id, ent.id, {"status": "SUCCESS"})
    assert exec_req.result_data["status"] == "SUCCESS"


@pytest.mark.asyncio
async def test_strategy_cascading_and_resources(async_session: AsyncSession):
    repo = SQLAlchemyEnterpriseRepository(async_session)
    strat_svc = EnterpriseStrategyService(repo)

    ent = await repo.save_enterprise(Enterprise(name="Strategy Ent", code="STRAT"))

    parent_obj = await strat_svc.create_enterprise_objective(ent.id, "Increase ARR", "Group ARR target", "ARR_USD", 50000000.0)
    child_obj = await strat_svc.create_enterprise_objective(ent.id, "Company A ARR", "Comp A target", "ARR_USD", 20000000.0, scope=ObjectiveScope.COMPANY)

    cascade = await strat_svc.cascade_objective(parent_obj.id, child_obj.id, "node-comp-a", 0.40)
    assert cascade.contribution_weight == 0.40

    pool = await strat_svc.create_resource_pool(ent.id, "GPU Cluster Pool", "GPU_COMPUTE", 100.0)
    alloc = await strat_svc.allocate_resource(pool.id, "consumer-1", 30.0)
    assert alloc.allocated_amount == 30.0

    with pytest.raises(ResourceAllocationConflictError):
        await strat_svc.allocate_resource(pool.id, "consumer-2", 80.0)


@pytest.mark.asyncio
async def test_governance_policy_resolution(async_session: AsyncSession):
    repo = SQLAlchemyEnterpriseRepository(async_session)
    gov_svc = EnterpriseGovernanceService(repo)

    ent = await repo.save_enterprise(Enterprise(name="Gov Ent", code="GOVENT"))

    # Root policy: max spend $50,000
    await gov_svc.set_policy_profile(ent.id, ent.id, max_single_budget_spend_usd=50000.0)

    # Child tries to request $100,000 spend
    await gov_svc.set_policy_profile(ent.id, "child-node-001", max_single_budget_spend_usd=100000.0)

    effective = await gov_svc.resolve_effective_policy(ent.id, "child-node-001")
    # Must NOT weaken root policy ($50,000)
    assert effective["effective_max_single_budget_spend_usd"] == 50000.0


@pytest.mark.asyncio
async def test_health_and_context_builder(async_session: AsyncSession):
    repo = SQLAlchemyEnterpriseRepository(async_session)
    health_svc = EnterpriseHealthAndIntelligenceService(repo)
    ctx_builder = EnterpriseContextBuilder(repo)

    ent = await repo.save_enterprise(Enterprise(name="Health Ent", code="HEALTH"))

    snapshot = await health_svc.aggregate_enterprise_health(ent.id)
    assert snapshot.overall_health_score > 0.0

    context_str = await ctx_builder.build_enterprise_context(ent.id)
    assert "=== BEGIN ENTERPRISE OS ADVISORY CONTEXT ===" in context_str
    assert ent.name in context_str

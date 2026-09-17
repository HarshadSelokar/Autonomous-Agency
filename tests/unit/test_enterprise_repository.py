"""
Unit tests for SQLAlchemyEnterpriseRepository persistence operations.
"""

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.infrastructure.database import Base
from src.infrastructure.repositories.enterprise_repository import SQLAlchemyEnterpriseRepository
from src.domain.enterprise import (
    Enterprise,
    EnterpriseLifecycle,
    EnterpriseOrganizationNode,
    NodeType,
    EnterpriseService,
    ServiceType,
    EnterprisePortfolio,
    PortfolioItem,
    EnterpriseObjective,
    EnterprisePolicyProfile,
    AuthorityGrant,
    EnterpriseResourcePool,
    InterCompanyRequest,
    InterCompanyRequestStatus,
    EnterpriseRisk,
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
async def test_enterprise_repository_crud(async_session: AsyncSession):
    repo = SQLAlchemyEnterpriseRepository(async_session)

    # 1. Create Enterprise
    ent = Enterprise(name="Apex Enterprise", code="APEX")
    saved_ent = await repo.save_enterprise(ent)
    assert saved_ent.id == ent.id

    fetched_ent = await repo.get_enterprise_by_id(ent.id)
    assert fetched_ent is not None
    assert fetched_ent.name == "Apex Enterprise"
    assert fetched_ent.code == "APEX"

    # 2. Add Topology Node
    node = EnterpriseOrganizationNode(
        enterprise_id=ent.id,
        name="Company Alpha",
        node_type=NodeType.COMPANY,
        region="NORTH_AMERICA",
    )
    await repo.save_topology_node(node)

    nodes = await repo.list_topology_nodes_for_enterprise(ent.id)
    assert len(nodes) == 1
    assert nodes[0].name == "Company Alpha"

    # 3. Add Shared Service
    svc = EnterpriseService(
        enterprise_id=ent.id,
        owner_node_id=node.id,
        name="Security Intelligence Swarm",
        service_type=ServiceType.SECURITY,
        capacity_units=200,
    )
    await repo.save_service(svc)

    services = await repo.list_services_for_enterprise(ent.id)
    assert len(services) == 1
    assert services[0].service_type == ServiceType.SECURITY

    # 4. Create InterCompany Request
    ic_req = InterCompanyRequest(
        enterprise_id=ent.id,
        source_company_id="comp-a",
        destination_company_id="comp-b",
        requester_id="req-123",
        requested_capability="DATA_ANALYSIS",
        purpose="Cross-tenant audit synthesis",
        status=InterCompanyRequestStatus.PENDING,
    )
    await repo.save_intercompany_request(ic_req)

    reqs = await repo.list_intercompany_requests_for_enterprise(ent.id)
    assert len(reqs) == 1
    assert reqs[0].status == InterCompanyRequestStatus.PENDING

"""
FastAPI REST API Routes for Phase 29 Enterprise OS, Federation & Large-Scale Operations.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database import get_db
from src.infrastructure.repositories.enterprise_repository import SQLAlchemyEnterpriseRepository
from src.application.enterprise_topology_service import EnterpriseTopologyService
from src.application.enterprise_federation_service import EnterpriseFederationService
from src.application.enterprise_strategy_service import EnterpriseStrategyService
from src.application.enterprise_governance_service import EnterpriseGovernanceService
from src.application.enterprise_health_service import EnterpriseHealthAndIntelligenceService
from src.application.enterprise_context_builder import EnterpriseContextBuilder
from src.domain.enterprise import (
    Enterprise,
    EnterpriseLifecycle,
    NodeType,
    RelationshipType,
    ServiceType,
    PortfolioCategory,
    PortfolioPriority,
    ObjectiveScope,
    DataClassification,
)
from src.domain.exceptions import (
    UnauthorizedEnterpriseActionError,
    InvalidTopologyCycleError,
    CrossEnterpriseAccessError,
    AuthorityExpiredError,
    ResourceAllocationConflictError,
)

router = APIRouter(prefix="/api/v1/enterprises", tags=["Enterprise OS & Federation"])


# Request Schemas
class CreateEnterpriseRequest(BaseModel):
    name: str
    code: str
    industry: str = "GLOBAL_TECHNOLOGY_ENTERPRISE"
    headquarters_region: str = "NORTH_AMERICA"
    operating_currency: str = "USD"
    description: str = ""


class CreateTopologyNodeRequest(BaseModel):
    name: str
    node_type: str = "COMPANY"
    reference_id: Optional[str] = None
    parent_node_id: Optional[str] = None
    region: str = "GLOBAL"
    data_classification: str = "INTERNAL"


class AddRelationshipRequest(BaseModel):
    source_node_id: str
    target_node_id: str
    relationship_type: str = "PARENT_CHILD"
    description: str = ""


class AttachCompanyRequest(BaseModel):
    company_id: str
    company_name: str
    region: str = "GLOBAL"
    parent_node_id: Optional[str] = None


class RegisterSharedServiceRequest(BaseModel):
    owner_node_id: str
    name: str
    service_type: str = "INFRASTRUCTURE"
    capacity_units: int = 100
    sla_description: str = "99.9% Availability"
    governance_required: bool = True


class CreateServiceAgreementRequest(BaseModel):
    consumer_node_id: str
    allocated_units: int = 10
    cost_allocation_usd: float = 0.0


class CreateObjectiveRequest(BaseModel):
    title: str
    description: str
    target_metric: str
    target_value: float = 100.0
    scope: str = "ENTERPRISE"
    owner_node_id: Optional[str] = None


class CascadeObjectiveRequest(BaseModel):
    child_objective_id: str
    child_node_id: str
    contribution_weight: float = 1.0


class CreatePortfolioRequest(BaseModel):
    name: str
    description: str = ""
    total_budget_usd: float = 0.0


class AddPortfolioItemRequest(BaseModel):
    name: str
    category: str = "COMPANY"
    reference_id: str
    priority: str = "MEDIUM"
    allocated_budget_usd: float = 0.0
    expected_roi: float = 0.20


class SetPolicyProfileRequest(BaseModel):
    node_id: str
    mandatory_security_level: str = "HIGH"
    max_single_budget_spend_usd: float = 50000.0
    prohibited_external_actions: Optional[List[str]] = None
    require_human_governance: bool = True


class GrantAuthorityRequest(BaseModel):
    grantor_node_id: str
    grantee_node_id: str
    scope: str
    action: str
    max_impact_usd: float = 100000.0


class CreateResourcePoolRequest(BaseModel):
    name: str
    resource_type: str = "COMPUTE"
    total_capacity: float = 1000.0
    unit: str = "UNITS"


class AllocateResourceRequest(BaseModel):
    consumer_node_id: str
    allocated_amount: float = 50.0


class SubmitInterCompanyRequest(BaseModel):
    source_company_id: str
    destination_company_id: str
    requester_id: str
    requested_capability: str
    purpose: str


class AuthorizeInterCompanyRequest(BaseModel):
    governance_approval_id: str


class RecordRiskRequest(BaseModel):
    title: str
    description: str
    impact_usd: float = 500000.0
    probability: float = 0.25
    owner_node_id: Optional[str] = None


class RecordOpportunityRequest(BaseModel):
    title: str
    description: str
    potential_value_usd: float = 2000000.0
    confidence: float = 0.80


# Route Handlers
@router.post("", status_code=status.HTTP_201_CREATED)
async def create_enterprise(
    payload: CreateEnterpriseRequest,
    db: AsyncSession = Depends(get_db),
):
    repo = SQLAlchemyEnterpriseRepository(db)
    ent = Enterprise(
        name=payload.name,
        code=payload.code,
        status=EnterpriseLifecycle.ACTIVE,
    )
    ent.profile.industry = payload.industry
    ent.profile.headquarters_region = payload.headquarters_region
    ent.profile.operating_currency = payload.operating_currency
    ent.profile.description = payload.description

    saved = await repo.save_enterprise(ent)
    return {
        "id": saved.id,
        "name": saved.name,
        "code": saved.code,
        "status": saved.status.value if hasattr(saved.status, "value") else str(saved.status),
    }


@router.get("")
async def list_enterprises(
    db: AsyncSession = Depends(get_db),
):
    repo = SQLAlchemyEnterpriseRepository(db)
    ents = await repo.list_enterprises()
    return [
        {
            "id": e.id,
            "name": e.name,
            "code": e.code,
            "status": e.status.value if hasattr(e.status, "value") else str(e.status),
        }
        for e in ents
    ]


@router.get("/{enterprise_id}")
async def get_enterprise(
    enterprise_id: str,
    db: AsyncSession = Depends(get_db),
):
    repo = SQLAlchemyEnterpriseRepository(db)
    ent = await repo.get_enterprise_by_id(enterprise_id)
    if not ent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Enterprise '{enterprise_id}' not found.")
    return {
        "id": ent.id,
        "name": ent.name,
        "code": ent.code,
        "status": ent.status.value if hasattr(ent.status, "value") else str(ent.status),
        "profile": {
            "industry": ent.profile.industry,
            "headquarters_region": ent.profile.headquarters_region,
            "operating_currency": ent.profile.operating_currency,
            "description": ent.profile.description,
        },
    }


@router.post("/{enterprise_id}/topology/nodes", status_code=status.HTTP_201_CREATED)
async def create_topology_node(
    enterprise_id: str,
    payload: CreateTopologyNodeRequest,
    db: AsyncSession = Depends(get_db),
):
    repo = SQLAlchemyEnterpriseRepository(db)
    svc = EnterpriseTopologyService(repo)
    try:
        ntype = NodeType(payload.node_type)
    except ValueError:
        ntype = NodeType.COMPANY

    try:
        dclass = DataClassification(payload.data_classification)
    except ValueError:
        dclass = DataClassification.INTERNAL

    try:
        node = await svc.create_node(
            enterprise_id=enterprise_id,
            name=payload.name,
            node_type=ntype,
            reference_id=payload.reference_id,
            parent_node_id=payload.parent_node_id,
            region=payload.region,
            data_classification=dclass,
        )
        return {
            "id": node.id,
            "enterprise_id": node.enterprise_id,
            "name": node.name,
            "node_type": node.node_type.value if hasattr(node.node_type, "value") else str(node.node_type),
        }
    except InvalidTopologyCycleError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.get("/{enterprise_id}/topology")
async def get_topology(
    enterprise_id: str,
    db: AsyncSession = Depends(get_db),
):
    repo = SQLAlchemyEnterpriseRepository(db)
    svc = EnterpriseTopologyService(repo)
    tree = await svc.get_topology_tree(enterprise_id)
    return tree


@router.post("/{enterprise_id}/companies/attach", status_code=status.HTTP_201_CREATED)
async def attach_company(
    enterprise_id: str,
    payload: AttachCompanyRequest,
    db: AsyncSession = Depends(get_db),
):
    repo = SQLAlchemyEnterpriseRepository(db)
    svc = EnterpriseFederationService(repo)
    node = await svc.attach_company_to_enterprise(
        enterprise_id=enterprise_id,
        company_id=payload.company_id,
        company_name=payload.company_name,
        region=payload.region,
        parent_node_id=payload.parent_node_id,
    )
    return {
        "node_id": node.id,
        "enterprise_id": node.enterprise_id,
        "company_id": node.reference_id,
        "company_name": node.name,
    }


@router.post("/{enterprise_id}/services", status_code=status.HTTP_201_CREATED)
async def register_shared_service(
    enterprise_id: str,
    payload: RegisterSharedServiceRequest,
    db: AsyncSession = Depends(get_db),
):
    repo = SQLAlchemyEnterpriseRepository(db)
    svc = EnterpriseFederationService(repo)
    try:
        stype = ServiceType(payload.service_type)
    except ValueError:
        stype = ServiceType.INFRASTRUCTURE

    service = await svc.register_shared_service(
        enterprise_id=enterprise_id,
        owner_node_id=payload.owner_node_id,
        name=payload.name,
        service_type=stype,
        capacity_units=payload.capacity_units,
        sla_description=payload.sla_description,
        governance_required=payload.governance_required,
    )
    return {
        "id": service.id,
        "enterprise_id": service.enterprise_id,
        "name": service.name,
        "capacity_units": service.capacity_units,
    }


@router.get("/{enterprise_id}/services")
async def list_shared_services(
    enterprise_id: str,
    db: AsyncSession = Depends(get_db),
):
    repo = SQLAlchemyEnterpriseRepository(db)
    services = await repo.list_services_for_enterprise(enterprise_id)
    return [
        {
            "id": s.id,
            "name": s.name,
            "service_type": s.service_type.value if hasattr(s.service_type, "value") else str(s.service_type),
            "capacity_units": s.capacity_units,
            "available_units": s.available_units,
        }
        for s in services
    ]


@router.post("/{enterprise_id}/objectives", status_code=status.HTTP_201_CREATED)
async def create_objective(
    enterprise_id: str,
    payload: CreateObjectiveRequest,
    db: AsyncSession = Depends(get_db),
):
    repo = SQLAlchemyEnterpriseRepository(db)
    svc = EnterpriseStrategyService(repo)
    try:
        scope = ObjectiveScope(payload.scope)
    except ValueError:
        scope = ObjectiveScope.ENTERPRISE

    obj = await svc.create_enterprise_objective(
        enterprise_id=enterprise_id,
        title=payload.title,
        description=payload.description,
        target_metric=payload.target_metric,
        target_value=payload.target_value,
        scope=scope,
        owner_node_id=payload.owner_node_id,
    )
    return {
        "id": obj.id,
        "enterprise_id": obj.enterprise_id,
        "title": obj.title,
        "target_value": obj.target_value,
    }


@router.get("/{enterprise_id}/objectives")
async def list_objectives(
    enterprise_id: str,
    db: AsyncSession = Depends(get_db),
):
    repo = SQLAlchemyEnterpriseRepository(db)
    objs = await repo.list_objectives_for_enterprise(enterprise_id)
    return [
        {
            "id": o.id,
            "title": o.title,
            "target_metric": o.target_metric,
            "target_value": o.target_value,
            "current_value": o.current_value,
            "scope": o.scope.value if hasattr(o.scope, "value") else str(o.scope),
        }
        for o in objs
    ]


@router.post("/{enterprise_id}/policy/profiles", status_code=status.HTTP_201_CREATED)
async def set_policy_profile(
    enterprise_id: str,
    payload: SetPolicyProfileRequest,
    db: AsyncSession = Depends(get_db),
):
    repo = SQLAlchemyEnterpriseRepository(db)
    svc = EnterpriseGovernanceService(repo)
    prof = await svc.set_policy_profile(
        enterprise_id=enterprise_id,
        node_id=payload.node_id,
        mandatory_security_level=payload.mandatory_security_level,
        max_single_budget_spend_usd=payload.max_single_budget_spend_usd,
        prohibited_external_actions=payload.prohibited_external_actions,
        require_human_governance=payload.require_human_governance,
    )
    return {
        "id": prof.id,
        "node_id": prof.node_id,
        "mandatory_security_level": prof.mandatory_security_level,
        "max_single_budget_spend_usd": prof.max_single_budget_spend_usd,
    }


@router.get("/{enterprise_id}/nodes/{node_id}/effective-policy")
async def get_effective_policy(
    enterprise_id: str,
    node_id: str,
    db: AsyncSession = Depends(get_db),
):
    repo = SQLAlchemyEnterpriseRepository(db)
    svc = EnterpriseGovernanceService(repo)
    effective = await svc.resolve_effective_policy(enterprise_id, node_id)
    return effective


@router.post("/{enterprise_id}/authority/grants", status_code=status.HTTP_201_CREATED)
async def grant_authority(
    enterprise_id: str,
    payload: GrantAuthorityRequest,
    db: AsyncSession = Depends(get_db),
):
    repo = SQLAlchemyEnterpriseRepository(db)
    svc = EnterpriseGovernanceService(repo)
    grant = await svc.grant_authority(
        enterprise_id=enterprise_id,
        grantor_node_id=payload.grantor_node_id,
        grantee_node_id=payload.grantee_node_id,
        scope=payload.scope,
        action=payload.action,
        max_impact_usd=payload.max_impact_usd,
    )
    return {
        "id": grant.id,
        "grantee_node_id": grant.grantee_node_id,
        "action": grant.action,
        "max_impact_usd": grant.max_impact_usd,
    }


@router.get("/{enterprise_id}/capacity")
async def get_capacity_snapshot(
    enterprise_id: str,
    db: AsyncSession = Depends(get_db),
):
    repo = SQLAlchemyEnterpriseRepository(db)
    svc = EnterpriseStrategyService(repo)
    snap = await svc.get_capacity_snapshot(enterprise_id)
    return {
        "enterprise_id": snap.enterprise_id,
        "total_agent_execution_capacity": snap.total_agent_execution_capacity,
        "used_agent_execution_capacity": snap.used_agent_execution_capacity,
        "shared_service_utilization_pct": snap.shared_service_utilization_pct,
        "capacity_gap_identified": snap.capacity_gap_identified,
    }


@router.post("/{enterprise_id}/intercompany-requests", status_code=status.HTTP_201_CREATED)
async def submit_intercompany_request(
    enterprise_id: str,
    payload: SubmitInterCompanyRequest,
    db: AsyncSession = Depends(get_db),
):
    repo = SQLAlchemyEnterpriseRepository(db)
    svc = EnterpriseFederationService(repo)
    req = await svc.submit_intercompany_request(
        enterprise_id=enterprise_id,
        source_company_id=payload.source_company_id,
        destination_company_id=payload.destination_company_id,
        requester_id=payload.requester_id,
        requested_capability=payload.requested_capability,
        purpose=payload.purpose,
    )
    return {
        "id": req.id,
        "enterprise_id": req.enterprise_id,
        "source_company_id": req.source_company_id,
        "destination_company_id": req.destination_company_id,
        "status": req.status.value if hasattr(req.status, "value") else str(req.status),
    }


@router.post("/{enterprise_id}/intercompany-requests/{request_id}/authorize")
async def authorize_intercompany_request(
    enterprise_id: str,
    request_id: str,
    payload: AuthorizeInterCompanyRequest,
    db: AsyncSession = Depends(get_db),
):
    repo = SQLAlchemyEnterpriseRepository(db)
    svc = EnterpriseFederationService(repo)
    try:
        req = await svc.authorize_intercompany_request(
            request_id=request_id,
            enterprise_id=enterprise_id,
            governance_approval_id=payload.governance_approval_id,
        )
        return {
            "id": req.id,
            "status": req.status.value if hasattr(req.status, "value") else str(req.status),
            "governance_approval_id": req.governance_approval_id,
        }
    except UnauthorizedEnterpriseActionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e


@router.get("/{enterprise_id}/health")
async def get_enterprise_health(
    enterprise_id: str,
    db: AsyncSession = Depends(get_db),
):
    repo = SQLAlchemyEnterpriseRepository(db)
    svc = EnterpriseHealthAndIntelligenceService(repo)
    health = await svc.aggregate_enterprise_health(enterprise_id)
    return {
        "enterprise_id": health.enterprise_id,
        "overall_health_score": health.overall_health_score,
        "objective_health_score": health.objective_health_score,
        "workforce_capacity_score": health.workforce_capacity_score,
        "financial_health_score": health.financial_health_score,
        "infrastructure_health_score": health.infrastructure_health_score,
        "governance_compliance_score": health.governance_compliance_score,
        "signals": health.health_signals,
    }


@router.get("/{enterprise_id}/context")
async def get_enterprise_context(
    enterprise_id: str,
    db: AsyncSession = Depends(get_db),
):
    repo = SQLAlchemyEnterpriseRepository(db)
    builder = EnterpriseContextBuilder(repo)
    context_str = await builder.build_enterprise_context(enterprise_id)
    return {"enterprise_id": enterprise_id, "context": context_str}

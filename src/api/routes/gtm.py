"""
FastAPI Routes for Phase 24 Product, Customer & GTM Operations.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.gtm import (
    FeedbackCategory,
    OpportunityStage,
    SupportPriority,
)
from src.domain.exceptions import (
    CustomerDataIsolationError,
    PricingPolicyViolationError,
    UnauthorizedCommercialCommitmentError,
)
from src.infrastructure.database import get_db
from src.infrastructure.repositories.gtm_repository import SQLAlchemyGTMRepository
from src.infrastructure.repositories.business_repository import SQLAlchemyBusinessRepository
from src.application.business_operations_service import BusinessOperationsService
from src.application.gtm_operations_service import GTMOperationsService

router = APIRouter(prefix="/gtm", tags=["gtm"])


def get_gtm_service(db: AsyncSession = Depends(get_db)) -> GTMOperationsService:
    gtm_repo = SQLAlchemyGTMRepository(db)
    biz_repo = SQLAlchemyBusinessRepository(db)
    biz_service = BusinessOperationsService(biz_repo)
    return GTMOperationsService(gtm_repository=gtm_repo, business_service=biz_service)


# --- Request/Response Schemas ---

class CreateProductRequest(BaseModel):
    name: str
    code: str
    description: str
    owner_employee_id: str
    base_price_cents: int = 0
    currency: str = "USD"
    category: str = "SOFTWARE"


class RecordFeedbackRequest(BaseModel):
    customer_id: str
    summary: str
    raw_content: str
    category: str = "FEATURE_REQUEST"
    importance_score: int = 5


class CreateLeadRequest(BaseModel):
    company_name: str
    contact_name: str
    contact_email: str
    source: str = "INBOUND_WEB"
    assigned_owner_id: Optional[str] = None


class QualifyLeadRequest(BaseModel):
    qualified_by: str
    score: int = 80


class CreateOpportunityRequest(BaseModel):
    title: str
    product_id: str
    owner_id: str
    estimated_value_cents: int
    lead_id: Optional[str] = None
    customer_id: Optional[str] = None
    currency: str = "USD"


class CreateProposalRequest(BaseModel):
    opportunity_id: str
    title: str
    product_id: str
    base_amount_cents: int
    owner_id: str
    discount_pct: float = 0.0


class ApproveProposalRequest(BaseModel):
    actor_id: str
    governance_approval_id: Optional[str] = None


class CreateSupportCaseRequest(BaseModel):
    customer_id: str
    subject: str
    description: str
    priority: str = "MEDIUM"
    assigned_employee_id: Optional[str] = None


class ResolveSupportCaseRequest(BaseModel):
    resolved_by: str
    resolution_notes: str


class CreateCampaignRequest(BaseModel):
    name: str
    objective: str
    target_audience: str
    channel: str = "EMAIL"
    budget_cents: int = 0
    owner_id: str = "MARKETING_LEAD"


class LaunchCampaignRequest(BaseModel):
    actor_id: str
    governance_approval_id: Optional[str] = None


class DealWonRequest(BaseModel):
    actor_id: str
    governance_approval_id: Optional[str] = None


# --- Route Handlers ---

@router.get("/products")
async def list_products(service: GTMOperationsService = Depends(get_gtm_service)) -> List[Dict[str, Any]]:
    prods = await service.repository.list_products()
    return [
        {
            "id": p.id,
            "name": p.name,
            "code": p.code,
            "lifecycle": p.lifecycle.value,
            "base_price_cents": p.base_price_cents,
            "dollars": p.money_base_price.to_dollars(),
        }
        for p in prods
    ]


@router.post("/products", status_code=status.HTTP_201_CREATED)
async def create_product(
    req: CreateProductRequest,
    service: GTMOperationsService = Depends(get_gtm_service),
) -> Dict[str, Any]:
    prod = await service.product_service.create_product(
        name=req.name,
        code=req.code,
        description=req.description,
        owner_employee_id=req.owner_employee_id,
        base_price_cents=req.base_price_cents,
        currency=req.currency,
        category=req.category,
    )
    return {"id": prod.id, "name": prod.name, "code": prod.code}


@router.post("/products/{id}/feedback", status_code=status.HTTP_201_CREATED)
async def record_feedback(
    id: str,
    req: RecordFeedbackRequest,
    service: GTMOperationsService = Depends(get_gtm_service),
) -> Dict[str, Any]:
    fb = await service.product_service.record_customer_feedback(
        product_id=id,
        customer_id=req.customer_id,
        summary=req.summary,
        raw_content=req.raw_content,
        category=FeedbackCategory(req.category.upper()),
        importance_score=req.importance_score,
    )
    return {"id": fb.id, "status": fb.status}


@router.get("/customers")
async def list_customers(service: GTMOperationsService = Depends(get_gtm_service)) -> List[Dict[str, Any]]:
    custs = await service.repository.list_customers()
    return [
        {
            "id": c.id,
            "name": c.name,
            "domain": c.domain,
            "lifecycle_state": c.lifecycle_state.value,
            "health_score": c.health_score,
        }
        for c in custs
    ]


@router.get("/leads")
async def list_leads(service: GTMOperationsService = Depends(get_gtm_service)) -> List[Dict[str, Any]]:
    leads = await service.repository.list_leads()
    return [
        {
            "id": l.id,
            "company_name": l.company_name,
            "contact_email": l.contact_email,
            "status": l.status.value,
            "score": l.score,
        }
        for l in leads
    ]


@router.post("/leads", status_code=status.HTTP_201_CREATED)
async def create_lead(
    req: CreateLeadRequest,
    service: GTMOperationsService = Depends(get_gtm_service),
) -> Dict[str, Any]:
    lead = await service.crm_service.create_lead(
        company_name=req.company_name,
        contact_name=req.contact_name,
        contact_email=req.contact_email,
        source=req.source,
        assigned_owner_id=req.assigned_owner_id,
    )
    return {"id": lead.id, "company_name": lead.company_name, "status": lead.status.value}


@router.post("/leads/{id}/qualify")
async def qualify_lead(
    id: str,
    req: QualifyLeadRequest,
    service: GTMOperationsService = Depends(get_gtm_service),
) -> Dict[str, Any]:
    lead = await service.crm_service.qualify_lead(id, req.qualified_by, req.score)
    return {"id": lead.id, "status": lead.status.value, "score": lead.score}


@router.get("/opportunities")
async def list_opportunities(service: GTMOperationsService = Depends(get_gtm_service)) -> List[Dict[str, Any]]:
    opps = await service.repository.list_opportunities()
    return [
        {
            "id": o.id,
            "title": o.title,
            "stage": o.stage.value,
            "estimated_value_cents": o.estimated_value_cents,
            "probability_pct": o.probability_pct,
        }
        for o in opps
    ]


@router.post("/opportunities", status_code=status.HTTP_201_CREATED)
async def create_opportunity(
    req: CreateOpportunityRequest,
    service: GTMOperationsService = Depends(get_gtm_service),
) -> Dict[str, Any]:
    opp = await service.crm_service.create_opportunity(
        title=req.title,
        product_id=req.product_id,
        owner_id=req.owner_id,
        estimated_value_cents=req.estimated_value_cents,
        lead_id=req.lead_id,
        customer_id=req.customer_id,
        currency=req.currency,
    )
    return {"id": opp.id, "title": opp.title, "stage": opp.stage.value}


@router.post("/opportunities/{id}/won")
async def mark_opportunity_won(
    id: str,
    req: DealWonRequest,
    service: GTMOperationsService = Depends(get_gtm_service),
) -> Dict[str, Any]:
    res = await service.execute_deal_won_and_onboard(id, actor_id=req.actor_id, governance_approval_id=req.governance_approval_id)
    return res


@router.post("/proposals", status_code=status.HTTP_201_CREATED)
async def create_proposal(
    req: CreateProposalRequest,
    service: GTMOperationsService = Depends(get_gtm_service),
) -> Dict[str, Any]:
    try:
        prop = await service.crm_service.create_proposal(
            opportunity_id=req.opportunity_id,
            title=req.title,
            product_id=req.product_id,
            base_amount_cents=req.base_amount_cents,
            owner_id=req.owner_id,
            discount_pct=req.discount_pct,
        )
        return {"id": prop.id, "status": prop.status.value, "total_amount_cents": prop.total_amount_cents}
    except PricingPolicyViolationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/proposals/{id}/approve")
async def approve_proposal(
    id: str,
    req: ApproveProposalRequest,
    service: GTMOperationsService = Depends(get_gtm_service),
) -> Dict[str, Any]:
    try:
        prop = await service.crm_service.approve_and_send_proposal(
            proposal_id=id,
            actor_id=req.actor_id,
            governance_approval_id=req.governance_approval_id,
        )
        return {"id": prop.id, "status": prop.status.value}
    except UnauthorizedCommercialCommitmentError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.get("/support")
async def list_support_cases(service: GTMOperationsService = Depends(get_gtm_service)) -> List[Dict[str, Any]]:
    cases = await service.repository.list_support_cases()
    return [
        {
            "id": c.id,
            "customer_id": c.customer_id,
            "subject": c.subject,
            "priority": c.priority.value,
            "status": c.status.value,
        }
        for c in cases
    ]


@router.post("/support", status_code=status.HTTP_201_CREATED)
async def create_support_case(
    req: CreateSupportCaseRequest,
    service: GTMOperationsService = Depends(get_gtm_service),
) -> Dict[str, Any]:
    case = await service.customer_service.create_support_case(
        customer_id=req.customer_id,
        subject=req.subject,
        description=req.description,
        priority=SupportPriority(req.priority.upper()),
        assigned_employee_id=req.assigned_employee_id,
    )
    return {"id": case.id, "status": case.status.value}


@router.post("/support/{id}/resolve")
async def resolve_support_case(
    id: str,
    req: ResolveSupportCaseRequest,
    service: GTMOperationsService = Depends(get_gtm_service),
) -> Dict[str, Any]:
    case = await service.customer_service.resolve_support_case(
        case_id=id,
        resolved_by=req.resolved_by,
        resolution_notes=req.resolution_notes,
    )
    return {"id": case.id, "status": case.status.value}


@router.get("/campaigns")
async def list_campaigns(service: GTMOperationsService = Depends(get_gtm_service)) -> List[Dict[str, Any]]:
    camps = await service.repository.list_marketing_campaigns()
    return [
        {
            "id": c.id,
            "name": c.name,
            "channel": c.channel,
            "budget_cents": c.budget_cents,
            "status": c.status.value,
        }
        for c in camps
    ]


@router.post("/campaigns", status_code=status.HTTP_201_CREATED)
async def create_campaign(
    req: CreateCampaignRequest,
    service: GTMOperationsService = Depends(get_gtm_service),
) -> Dict[str, Any]:
    camp = await service.marketing_service.create_campaign(
        name=req.name,
        objective=req.objective,
        target_audience=req.target_audience,
        channel=req.channel,
        budget_cents=req.budget_cents,
        owner_id=req.owner_id,
    )
    return {"id": camp.id, "name": camp.name, "status": camp.status.value}


@router.post("/campaigns/{id}/launch")
async def launch_campaign(
    id: str,
    req: LaunchCampaignRequest,
    service: GTMOperationsService = Depends(get_gtm_service),
) -> Dict[str, Any]:
    camp = await service.marketing_service.approve_and_launch_campaign(
        campaign_id=id,
        actor_id=req.actor_id,
        governance_approval_id=req.governance_approval_id,
    )
    return {"id": camp.id, "status": camp.status.value}

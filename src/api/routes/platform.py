"""
FastAPI REST API Routes for Phase 31 — Unified Control Plane, Readiness, Operating Views & Search.
"""

from datetime import datetime, timezone, UTC
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database import get_db
from src.application.platform_control_plane import CompanyLifecycleState, PlatformControlPlane
from src.application.workflows.platform_workflows import WorkflowCategory, WorkflowState

router = APIRouter(prefix="/api/v1/platform", tags=["Platform 1.0 Control Plane"])

# Single global control plane instance for state tracking
control_plane = PlatformControlPlane()


# Request Schemas
class BootstrapCompanyRequest(BaseModel):
    company_name: str
    code: str
    industry: str = "TECHNOLOGY"
    activate_immediately: bool = True


class BootstrapEnterpriseRequest(BaseModel):
    enterprise_name: str
    code: str
    node_count: int = 3
    shared_services_count: int = 2
    activate_immediately: bool = True


class StartWorkflowRequest(BaseModel):
    name: str
    category: str = "OBJECTIVE_TO_EXECUTION"
    company_id: str = "comp-main-01"
    enterprise_id: Optional[str] = None
    initial_context: Dict[str, Any] = Field(default_factory=dict)


class OnboardingStepRequest(BaseModel):
    company_id: str = "comp-main-01"
    step_name: str = "CONFIGURE_DEPARTMENTS"


# 1. Control Plane Overview
@router.get("/control-plane")
async def get_control_plane_overview() -> Dict[str, Any]:
    exec_view = control_plane.assemble_executive_view()
    return {
        "platform_name": "Autonomous AI Organization Platform 1.0",
        "version": "1.0.0",
        "status": "OPERATIONAL",
        "active_company_lifecycle": exec_view["lifecycle_state"],
        "overall_health_score": exec_view["overall_health_score"],
        "health_dimensions": exec_view["health_dimensions"],
        "timestamp": datetime.now(UTC).isoformat(),
    }


# 2. Company & Enterprise Bootstrap API
@router.post("/companies/bootstrap")
async def bootstrap_company(payload: BootstrapCompanyRequest) -> Dict[str, Any]:
    company_id = f"comp-{payload.code.lower()}"
    readiness = control_plane.evaluate_company_readiness(company_id)

    target_state = CompanyLifecycleState.ACTIVE if payload.activate_immediately else CompanyLifecycleState.READY
    try:
        final_state = control_plane.transition_company_state(company_id, target_state, readiness_result=readiness)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {
        "company_id": company_id,
        "company_name": payload.company_name,
        "lifecycle_state": final_state.value,
        "readiness_score": readiness.readiness_score,
        "is_ready": readiness.is_ready,
        "checklist": readiness.checklist,
    }


@router.post("/enterprises/bootstrap")
async def bootstrap_enterprise(payload: BootstrapEnterpriseRequest) -> Dict[str, Any]:
    enterprise_id = f"ent-{payload.code.lower()}"
    readiness = control_plane.evaluate_enterprise_readiness(
        enterprise_id,
        node_count=payload.node_count,
        shared_services_count=payload.shared_services_count,
    )

    return {
        "enterprise_id": enterprise_id,
        "enterprise_name": payload.enterprise_name,
        "is_ready": readiness.is_ready,
        "readiness_score": readiness.readiness_score,
        "checklist": readiness.checklist,
    }


# 3. Canonical Workflows API
@router.get("/workflows")
async def list_workflows(company_id: Optional[str] = None, state: Optional[str] = None) -> List[Dict[str, Any]]:
    wf_state = WorkflowState(state) if state else None
    workflows = control_plane.workflow_engine.list_workflows(company_id=company_id, state=wf_state)
    return [
        {
            "workflow_id": w.workflow_id,
            "name": w.name,
            "category": w.category.value,
            "company_id": w.company_id,
            "state": w.state.value,
            "current_step": w.current_step,
            "completed_steps": w.completed_steps,
            "started_at": w.started_at.isoformat(),
            "completed_at": w.completed_at.isoformat() if w.completed_at else None,
        }
        for w in workflows
    ]


@router.post("/workflows")
async def start_workflow(payload: StartWorkflowRequest) -> Dict[str, Any]:
    cat = WorkflowCategory(payload.category)
    record = control_plane.workflow_engine.start_workflow(
        name=payload.name,
        category=cat,
        company_id=payload.company_id,
        enterprise_id=payload.enterprise_id,
        initial_context=payload.initial_context,
    )
    return {
        "workflow_id": record.workflow_id,
        "name": record.name,
        "category": record.category.value,
        "state": record.state.value,
        "current_step": record.current_step,
    }


# 4. Multi-Dimensional Views (Executive, Manager, Employee)
@router.get("/views/executive")
async def get_executive_view(company_id: str = "comp-main-01") -> Dict[str, Any]:
    return control_plane.assemble_executive_view(company_id=company_id)


@router.get("/views/manager")
async def get_manager_view(company_id: str = "comp-main-01") -> Dict[str, Any]:
    return control_plane.assemble_manager_view(company_id=company_id)


@router.get("/views/employee")
async def get_employee_view(company_id: str = "comp-main-01") -> Dict[str, Any]:
    return control_plane.assemble_employee_agent_view(company_id=company_id)


# 5. Permission-Aware Search & Onboarding API
@router.get("/search")
async def search_platform(q: str = Query(..., min_length=2), company_id: str = "comp-main-01") -> Dict[str, Any]:
    # Multi-entity permission-scoped match simulation
    results = [
        {"type": "OBJECTIVE", "title": "Achieve $100M ARR", "id": "obj-101", "company_id": company_id},
        {"type": "PROJECT", "title": "Software Engine v2", "id": "prj-202", "company_id": company_id},
        {"type": "EMPLOYEE", "title": "VP of Engineering Agent", "id": "emp-303", "company_id": company_id},
        {"type": "DECISION", "title": "Authorize Q4 Capital Expansion", "id": "dec-404", "company_id": company_id},
    ]

    query_lower = q.lower()
    filtered = [r for r in results if query_lower in r["title"].lower() or query_lower in r["type"].lower()]

    return {
        "query": q,
        "company_id": company_id,
        "results_count": len(filtered),
        "results": filtered,
    }


@router.get("/onboarding")
async def get_onboarding_status(company_id: str = "comp-main-01") -> Dict[str, Any]:
    return {
        "company_id": company_id,
        "steps": [
            {"step": "1_CREATE_COMPANY", "title": "Create Enterprise & Company", "status": "COMPLETED"},
            {"step": "2_CONFIGURE_DEPARTMENTS", "title": "Structure Departments & Workforce", "status": "COMPLETED"},
            {"step": "3_CONFIGURE_POLICIES", "title": "Set Governance Policies & Spending Limits", "status": "COMPLETED"},
            {"step": "4_CONFIGURE_MODELS", "title": "Register Approved LLM Providers & Tools", "status": "COMPLETED"},
            {"step": "5_SET_OBJECTIVES", "title": "Formulate Strategic Objectives & Plans", "status": "COMPLETED"},
            {"step": "6_EXECUTE_GOLDEN_PATH", "title": "Execute Canonical Operating Loop", "status": "COMPLETED"},
        ],
        "onboarding_completed": True,
    }

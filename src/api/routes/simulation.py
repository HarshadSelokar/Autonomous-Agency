"""
Company Simulation REST API Endpoints for Phase 25.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database import get_db_session
from src.infrastructure.repositories.company_repository import SQLAlchemyMultiCompanyRepository
from src.application.company_simulation_service import CompanySimulationService
from src.application.simulation_scenario_engine import SimulationScenarioEngine
from src.domain.company import ExecutionEnvironment
from src.domain.simulation import SimulationStatus
from src.domain.exceptions import SimulationProductionMutationError
from src.api.middleware.company_context import get_company_context, CompanyContext

simulation_router = APIRouter(prefix="/api/v1/simulations", tags=["Company Simulation"])
router = simulation_router


class CreateSnapshotRequest(BaseModel):
    snapshot_name: str
    baseline_metrics: Dict[str, Any]


class CreateScenarioRequest(BaseModel):
    name: str
    description: str = ""
    variables: Dict[str, Any]


class CreateSimulationRequest(BaseModel):
    name: str
    scenario_id: str
    snapshot_id: str


@simulation_router.post("/snapshots", status_code=status.HTTP_201_CREATED)
async def create_snapshot(
    req: CreateSnapshotRequest,
    session: AsyncSession = Depends(get_db_session),
    ctx: CompanyContext = Depends(get_company_context),
):
    repo = SQLAlchemyMultiCompanyRepository(session)
    service = CompanySimulationService(repo)
    try:
        sn = await service.create_snapshot(ctx.company_id, req.snapshot_name, req.baseline_metrics)
        await session.commit()
        return {"snapshot_id": sn.id, "snapshot_name": sn.snapshot_name}
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@simulation_router.post("/scenarios", status_code=status.HTTP_201_CREATED)
async def create_scenario(
    req: CreateScenarioRequest,
    session: AsyncSession = Depends(get_db_session),
    ctx: CompanyContext = Depends(get_company_context),
):
    repo = SQLAlchemyMultiCompanyRepository(session)
    service = CompanySimulationService(repo)
    try:
        sc = await service.create_scenario(ctx.company_id, req.name, req.description, req.variables)
        await session.commit()
        return {"scenario_id": sc.id, "name": sc.name}
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@simulation_router.post("", status_code=status.HTTP_201_CREATED)
async def create_simulation(
    req: CreateSimulationRequest,
    session: AsyncSession = Depends(get_db_session),
    ctx: CompanyContext = Depends(get_company_context),
):
    repo = SQLAlchemyMultiCompanyRepository(session)
    service = CompanySimulationService(repo)
    try:
        sim = await service.create_simulation(
            company_id=ctx.company_id,
            name=req.name,
            scenario_id=req.scenario_id,
            snapshot_id=req.snapshot_id,
            owner_id=ctx.user_id,
        )
        await session.commit()
        return {"simulation_id": sim.id, "status": sim.status.value, "environment": sim.environment.value}
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@simulation_router.post("/{simulation_id}/run")
async def run_simulation(
    simulation_id: str,
    session: AsyncSession = Depends(get_db_session),
    ctx: CompanyContext = Depends(get_company_context),
):
    repo = SQLAlchemyMultiCompanyRepository(session)
    sim_svc = CompanySimulationService(repo)
    engine_svc = SimulationScenarioEngine(repo)

    try:
        await sim_svc.start_simulation(simulation_id)
        result = await engine_svc.run_simulation(simulation_id)
        await session.commit()
        return {
            "result_id": result.id,
            "scenario_name": result.scenario_name,
            "baseline_metrics": result.baseline_metrics,
            "simulated_metrics": result.simulated_metrics,
            "variance_analysis": result.variance_analysis,
        }
    except SimulationProductionMutationError as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@simulation_router.get("/{simulation_id}/results")
async def get_simulation_results(
    simulation_id: str,
    session: AsyncSession = Depends(get_db_session),
    ctx: CompanyContext = Depends(get_company_context),
):
    repo = SQLAlchemyMultiCompanyRepository(session)
    res = await repo.get_simulation_result_by_simulation_id(simulation_id)
    if not res:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No results found for simulation '{simulation_id}'.")

    ctx.verify_company_access(res.company_id, "simulation_results")
    return {
        "result_id": res.id,
        "scenario_name": res.scenario_name,
        "baseline_metrics": res.baseline_metrics,
        "simulated_metrics": res.simulated_metrics,
        "variance_analysis": res.variance_analysis,
        "confidence_score": res.confidence_score,
    }

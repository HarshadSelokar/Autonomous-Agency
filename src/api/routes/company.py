"""FastAPI Router for Phase 16 Autonomous Company Operations."""

from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.schemas.company import (
    CompanyHealthResponse,
    CompanyOperatingCycleResponse,
    CompanyResponse,
    CompanyStrategyResponse,
    CreateCompanyRequest,
    CreatePortfolioItemRequest,
    CreateStrategyProposalRequest,
    CreateStrategyRequest,
    ExecutiveReportResponse,
    PortfolioItemResponse,
    RunSimulationRequest,
    StartOperatingCycleRequest,
    StrategyProposalResponse,
    StrategySimulationResponse,
    TransitionCycleStateRequest,
)
from src.application.company_observation_service import CompanyObservationService
from src.application.company_operating_cycle_service import CompanyOperatingCycleService
from src.application.executive_orchestration_service import ExecutiveOrchestrationService
from src.application.strategic_intelligence_service import StrategicIntelligenceService
from src.domain.company import AutonomousCompany, CompanyStatus, OperatingCycleState
from src.domain.strategy import StrategyProposalType
from src.infrastructure.database import get_db_session
from src.infrastructure.repositories.company_repository import SQLAlchemyCompanyRepository

router = APIRouter(prefix="/company", tags=["Autonomous Company OS"])


def get_company_repo(session: AsyncSession = Depends(get_db_session)) -> SQLAlchemyCompanyRepository:
    return SQLAlchemyCompanyRepository(session)


def get_observation_service(repo: SQLAlchemyCompanyRepository = Depends(get_company_repo)) -> CompanyObservationService:
    return CompanyObservationService(repo)


def get_intelligence_service(repo: SQLAlchemyCompanyRepository = Depends(get_company_repo)) -> StrategicIntelligenceService:
    return StrategicIntelligenceService(repo)


def get_cycle_service(
    repo: SQLAlchemyCompanyRepository = Depends(get_company_repo),
    obs_svc: CompanyObservationService = Depends(get_observation_service),
    strat_svc: StrategicIntelligenceService = Depends(get_intelligence_service),
) -> CompanyOperatingCycleService:
    return CompanyOperatingCycleService(repo, obs_svc, strat_svc)


def get_executive_service(repo: SQLAlchemyCompanyRepository = Depends(get_company_repo)) -> ExecutiveOrchestrationService:
    return ExecutiveOrchestrationService(repo)


# -------------------------------------------------------------
# Company Management
# -------------------------------------------------------------
@router.post("", status_code=status.HTTP_201_CREATED, response_model=CompanyResponse)
async def create_company(
    payload: CreateCompanyRequest,
    repo: SQLAlchemyCompanyRepository = Depends(get_company_repo),
) -> Any:
    company = AutonomousCompany(
        name=payload.name,
        code=payload.code,
        mission=payload.mission,
        status=CompanyStatus.ACTIVE,
        settings=payload.settings,
    )
    saved = await repo.save_company(company)
    return saved


@router.get("/{company_id}", response_model=CompanyResponse)
async def get_company(
    company_id: str,
    repo: SQLAlchemyCompanyRepository = Depends(get_company_repo),
) -> Any:
    company = await repo.get_company_by_id(company_id)
    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    return company


# -------------------------------------------------------------
# Operating Cycles
# -------------------------------------------------------------
@router.post("/{company_id}/cycles", status_code=status.HTTP_201_CREATED, response_model=CompanyOperatingCycleResponse)
async def start_operating_cycle(
    company_id: str,
    payload: StartOperatingCycleRequest,
    cycle_svc: CompanyOperatingCycleService = Depends(get_cycle_service),
) -> Any:
    try:
        cycle = await cycle_svc.start_new_cycle(company_id, payload.initiated_by_id)
        return cycle
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{company_id}/cycles/{cycle_id}/transition", response_model=CompanyOperatingCycleResponse)
async def transition_cycle_state(
    company_id: str,
    cycle_id: str,
    payload: TransitionCycleStateRequest,
    cycle_svc: CompanyOperatingCycleService = Depends(get_cycle_service),
) -> Any:
    try:
        target = OperatingCycleState(payload.target_state)
        cycle = await cycle_svc.transition_phase(cycle_id, target, payload.checkpoint_data)
        return cycle
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{company_id}/cycles/run-full", response_model=CompanyOperatingCycleResponse)
async def run_full_operating_cycle(
    company_id: str,
    initiated_by_id: str = "api_request",
    cycle_svc: CompanyOperatingCycleService = Depends(get_cycle_service),
) -> Any:
    cycle = await cycle_svc.execute_full_cycle(company_id, initiated_by_id)
    return cycle


@router.get("/{company_id}/cycles", response_model=list[CompanyOperatingCycleResponse])
async def list_operating_cycles(
    company_id: str,
    repo: SQLAlchemyCompanyRepository = Depends(get_company_repo),
) -> Any:
    cycles = await repo.list_cycles_for_company(company_id)
    return cycles


# -------------------------------------------------------------
# Health & Observations
# -------------------------------------------------------------
@router.get("/{company_id}/health", response_model=CompanyHealthResponse)
async def get_company_health(
    company_id: str,
    obs_svc: CompanyObservationService = Depends(get_observation_service),
) -> Any:
    health = await obs_svc.evaluate_company_health(company_id)
    return health


# -------------------------------------------------------------
# Strategy & Proposals
# -------------------------------------------------------------
@router.post("/{company_id}/strategies", response_model=CompanyStrategyResponse)
async def formulate_strategy(
    company_id: str,
    payload: CreateStrategyRequest,
    intel_svc: StrategicIntelligenceService = Depends(get_intelligence_service),
) -> Any:
    strategy = await intel_svc.Formulate_or_update_strategy(
        company_id=company_id,
        title=payload.title,
        themes=payload.themes,
        priorities=payload.priorities,
        targets=payload.targets,
        change_rationale=payload.change_rationale,
    )
    return strategy


@router.get("/{company_id}/strategies/active", response_model=CompanyStrategyResponse)
async def get_active_strategy(
    company_id: str,
    repo: SQLAlchemyCompanyRepository = Depends(get_company_repo),
) -> Any:
    strat = await repo.get_active_strategy_for_company(company_id)
    if not strat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Active strategy not found")
    return strat


@router.post("/{company_id}/proposals", status_code=status.HTTP_201_CREATED, response_model=StrategyProposalResponse)
async def create_strategy_proposal(
    company_id: str,
    payload: CreateStrategyProposalRequest,
    intel_svc: StrategicIntelligenceService = Depends(get_intelligence_service),
) -> Any:
    prop_type = StrategyProposalType(payload.proposal_type)
    proposal = await intel_svc.create_strategy_proposal(
        company_id=company_id,
        proposal_type=prop_type,
        title=payload.title,
        proposal_body=payload.proposal_body,
        reason=payload.reason,
        benefits=payload.benefits,
        resource_impact=payload.resource_impact,
        governance_level=payload.governance_level,
    )
    return proposal


@router.get("/{company_id}/proposals", response_model=list[StrategyProposalResponse])
async def list_strategy_proposals(
    company_id: str,
    repo: SQLAlchemyCompanyRepository = Depends(get_company_repo),
) -> Any:
    proposals = await repo.list_proposals_for_company(company_id)
    return proposals


# -------------------------------------------------------------
# What-If Strategy Simulations
# -------------------------------------------------------------
@router.post("/{company_id}/simulations", status_code=status.HTTP_201_CREATED, response_model=StrategySimulationResponse)
async def run_strategy_simulation(
    company_id: str,
    payload: RunSimulationRequest,
    intel_svc: StrategicIntelligenceService = Depends(get_intelligence_service),
) -> Any:
    sim = await intel_svc.run_what_if_simulation(
        company_id=company_id,
        title=payload.title,
        assumptions=payload.assumptions,
        input_parameters=payload.input_parameters,
    )
    return sim


@router.get("/{company_id}/simulations", response_model=list[StrategySimulationResponse])
async def list_strategy_simulations(
    company_id: str,
    repo: SQLAlchemyCompanyRepository = Depends(get_company_repo),
) -> Any:
    sims = await repo.list_simulations_for_company(company_id)
    return sims


# -------------------------------------------------------------
# Executive Reporting & Portfolio
# -------------------------------------------------------------
@router.get("/{company_id}/executive-report", response_model=ExecutiveReportResponse)
async def get_executive_report(
    company_id: str,
    exec_svc: ExecutiveOrchestrationService = Depends(get_executive_service),
) -> Any:
    try:
        report = await exec_svc.generate_executive_report(company_id)
        return report
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/{company_id}/portfolio", status_code=status.HTTP_201_CREATED, response_model=PortfolioItemResponse)
async def add_portfolio_item(
    company_id: str,
    payload: CreatePortfolioItemRequest,
    exec_svc: ExecutiveOrchestrationService = Depends(get_executive_service),
) -> Any:
    item = await exec_svc.add_portfolio_item(
        company_id=company_id,
        title=payload.title,
        reference_id=payload.reference_id,
        item_type=payload.item_type,
        priority=payload.priority,
    )
    return item


@router.get("/{company_id}/portfolio", response_model=list[PortfolioItemResponse])
async def list_portfolio_items(
    company_id: str,
    repo: SQLAlchemyCompanyRepository = Depends(get_company_repo),
) -> Any:
    items = await repo.list_portfolio_items_for_company(company_id)
    return items

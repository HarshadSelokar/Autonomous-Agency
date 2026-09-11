"""
FastAPI Router for Agent management endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.schemas.agent_schemas import AgentResponse, CreateAgentRequest
from src.domain.agent import (
    Agent,
    CommunicationPolicy,
    ModelConfiguration,
    PermissionProfile,
    VerificationPolicy,
)
from src.infrastructure.database import get_db_session
from src.infrastructure.repositories.agent_repository import SQLAlchemyAgentRepository

router = APIRouter(prefix="/agents", tags=["Agents"])


@router.post("", response_model=AgentResponse, status_code=status.HTTP_201_CREATED)
async def create_agent(
    req: CreateAgentRequest,
    session: AsyncSession = Depends(get_db_session),
) -> AgentResponse:
    repo = SQLAlchemyAgentRepository(session)

    existing = await repo.get_by_id(req.id)
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Agent with ID '{req.id}' already exists.",
        )

    agent = Agent(
        id=req.id,
        name=req.name,
        role=req.role,
        description=req.description,
        responsibilities=req.responsibilities,
        capabilities=req.capabilities,
        manager_id=req.manager_id,
        model_configuration=ModelConfiguration(
            provider=req.model_configuration.provider,
            model=req.model_configuration.model,
            temperature=req.model_configuration.temperature,
            max_tokens=req.model_configuration.max_tokens,
            top_p=req.model_configuration.top_p,
            extra_params=req.model_configuration.extra_params,
        ),
        permission_profile=PermissionProfile(permissions=req.permission_profile.permissions),
        verification_policy=VerificationPolicy(
            required=req.verification_policy.required,
            verifier_role=req.verification_policy.verifier_role,
        ),
        communication_policy=CommunicationPolicy(
            allowed_channels=req.communication_policy.allowed_channels,
            restricted=req.communication_policy.restricted,
        ),
        metadata=req.metadata,
    )

    saved = await repo.save(agent)
    return AgentResponse.from_domain(saved)


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: str,
    session: AsyncSession = Depends(get_db_session),
) -> AgentResponse:
    repo = SQLAlchemyAgentRepository(session)
    agent = await repo.get_by_id(agent_id)
    if agent is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{agent_id}' not found.",
        )
    return AgentResponse.from_domain(agent)


@router.get("", response_model=list[AgentResponse])
async def list_agents(
    session: AsyncSession = Depends(get_db_session),
) -> list[AgentResponse]:
    repo = SQLAlchemyAgentRepository(session)
    agents = await repo.list_all()
    return [AgentResponse.from_domain(a) for a in agents]

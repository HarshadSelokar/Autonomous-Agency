"""
SQLAlchemy ORM Model for Agent persistence and conversion utilities.
"""

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import JSON, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.domain.agent import (
    Agent,
    AgentState,
    CommunicationPolicy,
    ModelConfiguration,
    PermissionProfile,
    VerificationPolicy,
)
from src.infrastructure.database import Base


class AgentModel(Base):
    __tablename__ = "agents"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    role: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    responsibilities: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    capabilities: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    manager_id: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # Serialized Value Objects
    model_configuration: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    permission_profile: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    verification_policy: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    communication_policy: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)

    current_state: Mapped[str] = mapped_column(
        String(32), nullable=False, default=AgentState.IDLE.value
    )
    current_task_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSON, nullable=False, default=dict
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )


def agent_model_to_domain(model: AgentModel) -> Agent:
    """Map SQLAlchemy AgentModel to pure Domain Agent entity."""
    return Agent(
        id=model.id,
        name=model.name,
        role=model.role,
        description=model.description,
        responsibilities=list(model.responsibilities or []),
        capabilities=list(model.capabilities or []),
        manager_id=model.manager_id,
        model_configuration=ModelConfiguration(
            provider=model.model_configuration.get("provider", "groq"),
            model=model.model_configuration.get("model", "llama-3.3-70b-versatile"),
            temperature=float(model.model_configuration.get("temperature", 0.7)),
            max_tokens=int(model.model_configuration.get("max_tokens", 4096)),
            top_p=float(model.model_configuration.get("top_p", 1.0)),
            extra_params=dict(model.model_configuration.get("extra_params", {})),
        ),
        permission_profile=PermissionProfile(
            permissions=list(model.permission_profile.get("permissions", []))
        ),
        verification_policy=VerificationPolicy(
            required=bool(model.verification_policy.get("required", False)),
            verifier_role=model.verification_policy.get("verifier_role"),
        ),
        communication_policy=CommunicationPolicy(
            allowed_channels=list(model.communication_policy.get("allowed_channels", [])),
            restricted=bool(model.communication_policy.get("restricted", False)),
        ),
        current_state=AgentState(model.current_state),
        current_task_id=model.current_task_id,
        metadata=dict(model.metadata_json or {}),
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def agent_domain_to_model(agent: Agent) -> AgentModel:
    """Map pure Domain Agent entity to SQLAlchemy AgentModel."""
    return AgentModel(
        id=agent.id,
        name=agent.name,
        role=agent.role,
        description=agent.description,
        responsibilities=agent.responsibilities,
        capabilities=agent.capabilities,
        manager_id=agent.manager_id,
        model_configuration={
            "provider": agent.model_configuration.provider,
            "model": agent.model_configuration.model,
            "temperature": agent.model_configuration.temperature,
            "max_tokens": agent.model_configuration.max_tokens,
            "top_p": agent.model_configuration.top_p,
            "extra_params": agent.model_configuration.extra_params,
        },
        permission_profile={
            "permissions": agent.permission_profile.permissions,
        },
        verification_policy={
            "required": agent.verification_policy.required,
            "verifier_role": agent.verification_policy.verifier_role,
        },
        communication_policy={
            "allowed_channels": agent.communication_policy.allowed_channels,
            "restricted": agent.communication_policy.restricted,
        },
        current_state=agent.current_state.value,
        current_task_id=agent.current_task_id,
        metadata_json=agent.metadata,
        created_at=agent.created_at,
        updated_at=agent.updated_at,
    )

"""
Pydantic Request and Response Schemas for Agent API Endpoints.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from src.domain.agent import Agent, AgentState


class ModelConfigDTO(BaseModel):
    provider: str = "groq"
    model: str = "llama-3.3-70b-versatile"
    temperature: float = 0.7
    max_tokens: int = 4096
    top_p: float = 1.0
    extra_params: dict[str, Any] = Field(default_factory=dict)


class PermissionProfileDTO(BaseModel):
    permissions: list[str] = Field(default_factory=list)


class VerificationPolicyDTO(BaseModel):
    required: bool = False
    verifier_role: str | None = None


class CommunicationPolicyDTO(BaseModel):
    allowed_channels: list[str] = Field(default_factory=list)
    restricted: bool = False


class CreateAgentRequest(BaseModel):
    id: str
    name: str
    role: str
    description: str = ""
    responsibilities: list[str] = Field(default_factory=list)
    capabilities: list[str] = Field(default_factory=list)
    manager_id: str | None = None
    model_configuration: ModelConfigDTO = Field(default_factory=ModelConfigDTO)
    permission_profile: PermissionProfileDTO = Field(default_factory=PermissionProfileDTO)
    verification_policy: VerificationPolicyDTO = Field(default_factory=VerificationPolicyDTO)
    communication_policy: CommunicationPolicyDTO = Field(default_factory=CommunicationPolicyDTO)
    metadata: dict[str, Any] = Field(default_factory=dict)


class AgentResponse(BaseModel):
    id: str
    name: str
    role: str
    description: str
    responsibilities: list[str]
    capabilities: list[str]
    manager_id: str | None
    model_configuration: ModelConfigDTO
    permission_profile: PermissionProfileDTO
    verification_policy: VerificationPolicyDTO
    communication_policy: CommunicationPolicyDTO
    current_state: AgentState
    current_task_id: str | None
    metadata: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_domain(cls, agent: Agent) -> "AgentResponse":
        return cls(
            id=agent.id,
            name=agent.name,
            role=agent.role,
            description=agent.description,
            responsibilities=agent.responsibilities,
            capabilities=agent.capabilities,
            manager_id=agent.manager_id,
            model_configuration=ModelConfigDTO(
                provider=agent.model_configuration.provider,
                model=agent.model_configuration.model,
                temperature=agent.model_configuration.temperature,
                max_tokens=agent.model_configuration.max_tokens,
                top_p=agent.model_configuration.top_p,
                extra_params=agent.model_configuration.extra_params,
            ),
            permission_profile=PermissionProfileDTO(
                permissions=agent.permission_profile.permissions
            ),
            verification_policy=VerificationPolicyDTO(
                required=agent.verification_policy.required,
                verifier_role=agent.verification_policy.verifier_role,
            ),
            communication_policy=CommunicationPolicyDTO(
                allowed_channels=agent.communication_policy.allowed_channels,
                restricted=agent.communication_policy.restricted,
            ),
            current_state=agent.current_state,
            current_task_id=agent.current_task_id,
            metadata=agent.metadata,
            created_at=agent.created_at,
            updated_at=agent.updated_at,
        )

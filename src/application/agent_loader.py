"""
Configuration-Driven Agent Loader.
Parses YAML / JSON agent definitions into Domain Agent entities.
"""

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field

from src.domain.agent import (
    Agent,
    CommunicationPolicy,
    ModelConfiguration,
    PermissionProfile,
    VerificationPolicy,
)


class ModelConfigSchema(BaseModel):
    provider: str = "groq"
    model: str = "llama-3.3-70b-versatile"
    temperature: float = 0.7
    max_tokens: int = 4096
    top_p: float = 1.0
    extra_params: dict[str, Any] = Field(default_factory=dict)


class VerificationPolicySchema(BaseModel):
    required: bool = False
    verifier_role: str | None = None


class CommunicationPolicySchema(BaseModel):
    allowed_channels: list[str] = Field(default_factory=list)
    restricted: bool = False


class AgentDefinitionSchema(BaseModel):
    id: str
    name: str
    role: str
    description: str = ""
    responsibilities: list[str] = Field(default_factory=list)
    capabilities: list[str] = Field(default_factory=list)
    manager_id: str | None = None
    model: ModelConfigSchema = Field(default_factory=ModelConfigSchema)
    permissions: list[str] = Field(default_factory=list)
    verification: VerificationPolicySchema = Field(default_factory=VerificationPolicySchema)
    communication: CommunicationPolicySchema = Field(default_factory=CommunicationPolicySchema)
    metadata: dict[str, Any] = Field(default_factory=dict)


def parse_agent_definition(data: dict[str, Any]) -> Agent:
    """Parse raw dictionary data into a Domain Agent entity."""
    # Support top-level 'agent' key wrapper if present
    agent_data = data.get("agent", data)
    schema = AgentDefinitionSchema.model_validate(agent_data)

    return Agent(
        id=schema.id,
        name=schema.name,
        role=schema.role,
        description=schema.description,
        responsibilities=schema.responsibilities,
        capabilities=schema.capabilities,
        manager_id=schema.manager_id,
        model_configuration=ModelConfiguration(
            provider=schema.model.provider,
            model=schema.model.model,
            temperature=schema.model.temperature,
            max_tokens=schema.model.max_tokens,
            top_p=schema.model.top_p,
            extra_params=schema.model.extra_params,
        ),
        permission_profile=PermissionProfile(permissions=schema.permissions),
        verification_policy=VerificationPolicy(
            required=schema.verification.required,
            verifier_role=schema.verification.verifier_role,
        ),
        communication_policy=CommunicationPolicy(
            allowed_channels=schema.communication.allowed_channels,
            restricted=schema.communication.restricted,
        ),
        metadata=schema.metadata,
    )


def load_agent_from_yaml(yaml_path: str | Path) -> Agent:
    """Load and parse an Agent entity from a YAML definition file."""
    path = Path(yaml_path)
    if not path.is_file():
        raise FileNotFoundError(f"Agent configuration file not found at '{yaml_path}'")

    with open(path, encoding="utf-8") as f:
        content = yaml.safe_load(f)

    if not isinstance(content, dict):
        raise ValueError(f"Invalid YAML configuration content in '{yaml_path}'")

    return parse_agent_definition(content)

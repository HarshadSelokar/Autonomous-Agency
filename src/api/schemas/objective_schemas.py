"""
Pydantic schemas for Objective API endpoints.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from src.domain.objective import Objective, ObjectiveStatus


class CreateObjectiveRequest(BaseModel):
    id: str
    title: str
    description: str
    requester: str
    priority: str = "medium"
    constraints: list[str] = Field(default_factory=list)
    manager_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class RequestClarificationRequest(BaseModel):
    questions: list[str]


class ProvideClarificationRequest(BaseModel):
    answers: dict[str, str]


class ObjectiveResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    description: str
    requester: str
    priority: str
    constraints: list[str]
    status: ObjectiveStatus
    manager_id: str | None
    plan_id: str | None
    metadata: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_domain(cls, obj: Objective) -> "ObjectiveResponse":
        return cls(
            id=obj.id,
            title=obj.title,
            description=obj.description,
            requester=obj.requester,
            priority=obj.priority,
            constraints=obj.constraints,
            status=obj.status,
            manager_id=obj.manager_id,
            plan_id=obj.plan_id,
            metadata=obj.metadata,
            created_at=obj.created_at,
            updated_at=obj.updated_at,
        )

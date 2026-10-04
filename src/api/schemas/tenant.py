"""
Pydantic Schemas for Multi-Tenant Management APIs (Phase 32).
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class TenantConfigurationSchema(BaseModel):
    max_users: int = 100
    max_projects: int = 50
    max_workflows: int = 20
    allowed_providers: List[str] = Field(default_factory=lambda: ["groq", "fake"])
    custom_settings: Dict[str, Any] = Field(default_factory=dict)


class TenantCreateSchema(BaseModel):
    name: str = Field(..., min_length=2, max_length=256)
    slug: str = Field(..., min_length=2, max_length=128)
    plan: str = "FREE"
    configuration: Optional[TenantConfigurationSchema] = None
    tenant_id: Optional[str] = None


class TenantUpdateSchema(BaseModel):
    name: Optional[str] = None
    plan: Optional[str] = None
    status: Optional[str] = None
    configuration: Optional[TenantConfigurationSchema] = None


class TenantResponseSchema(BaseModel):
    id: str
    name: str
    slug: str
    status: str
    plan: str
    configuration: TenantConfigurationSchema
    created_at: str
    updated_at: str

"""
Pydantic Schemas for Identity, Organization, and Membership APIs (Phase 33).
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, EmailStr, Field


class UserCreateSchema(BaseModel):
    tenant_id: str
    email: EmailStr
    full_name: str
    is_platform_admin: bool = False
    password: Optional[str] = Field(default=None, min_length=10, max_length=256)


class LoginRequestSchema(BaseModel):
    email: EmailStr
    password: str
    tenant_id: Optional[str] = None


class TokenResponseSchema(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_seconds: int


class PrincipalResponseSchema(BaseModel):
    user_id: str
    tenant_id: Optional[str]
    is_platform_admin: bool
    email: Optional[str]


class UserResponseSchema(BaseModel):
    id: str
    tenant_id: str
    email: str
    full_name: str
    status: str
    is_platform_admin: bool
    created_at: str
    updated_at: str


class OrganizationCreateSchema(BaseModel):
    tenant_id: str
    name: str = Field(..., min_length=2, max_length=256)
    slug: str = Field(..., min_length=2, max_length=128)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class OrganizationResponseSchema(BaseModel):
    id: str
    tenant_id: str
    name: str
    slug: str
    status: str
    metadata: Dict[str, Any]
    created_at: str
    updated_at: str


class MembershipCreateSchema(BaseModel):
    tenant_id: str
    organization_id: str
    user_id: str
    role: str = "EMPLOYEE"


class MembershipResponseSchema(BaseModel):
    id: str
    tenant_id: str
    organization_id: str
    user_id: str
    role: str
    is_active: bool
    created_at: str

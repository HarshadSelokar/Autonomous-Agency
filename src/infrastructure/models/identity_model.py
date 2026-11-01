"""
SQLAlchemy ORM Models for Identity, Organization, and Membership persistence (Phase 33).
"""

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from src.domain.identity import (
    User,
    UserStatus,
    Organization,
    OrganizationStatus,
    Membership,
    Role,
)
from src.infrastructure.database import Base


class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(256), nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String(256), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="ACTIVE", index=True)
    is_platform_admin: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    password_hash: Mapped[str | None] = mapped_column(String(256), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )


class OrganizationModel(Base):
    __tablename__ = "organizations"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    slug: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="ACTIVE", index=True)
    metadata_json: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )


class MembershipModel(Base):
    __tablename__ = "memberships"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    organization_id: Mapped[str] = mapped_column(String(64), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(String(64), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(32), nullable=False, default="EMPLOYEE", index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )


def user_model_to_domain(model: UserModel) -> User:
    return User(
        id=model.id,
        tenant_id=model.tenant_id,
        email=model.email,
        full_name=model.full_name,
        status=UserStatus(model.status),
        is_platform_admin=model.is_platform_admin,
        password_hash=model.password_hash,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def user_domain_to_model(domain: User) -> UserModel:
    return UserModel(
        id=domain.id,
        tenant_id=domain.tenant_id,
        email=domain.email,
        full_name=domain.full_name,
        status=domain.status.value if isinstance(domain.status, UserStatus) else str(domain.status),
        is_platform_admin=domain.is_platform_admin,
        password_hash=domain.password_hash,
        created_at=domain.created_at,
        updated_at=domain.updated_at,
    )


def organization_model_to_domain(model: OrganizationModel) -> Organization:
    return Organization(
        id=model.id,
        tenant_id=model.tenant_id,
        name=model.name,
        slug=model.slug,
        status=OrganizationStatus(model.status),
        metadata_json=model.metadata_json or {},
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def organization_domain_to_model(domain: Organization) -> OrganizationModel:
    return OrganizationModel(
        id=domain.id,
        tenant_id=domain.tenant_id,
        name=domain.name,
        slug=domain.slug,
        status=domain.status.value if isinstance(domain.status, OrganizationStatus) else str(domain.status),
        metadata_json=domain.metadata_json,
        created_at=domain.created_at,
        updated_at=domain.updated_at,
    )


def membership_model_to_domain(model: MembershipModel) -> Membership:
    return Membership(
        id=model.id,
        tenant_id=model.tenant_id,
        organization_id=model.organization_id,
        user_id=model.user_id,
        role=Role(model.role),
        is_active=model.is_active,
        created_at=model.created_at,
    )


def membership_domain_to_model(domain: Membership) -> MembershipModel:
    return MembershipModel(
        id=domain.id,
        tenant_id=domain.tenant_id,
        organization_id=domain.organization_id,
        user_id=domain.user_id,
        role=domain.role.value if isinstance(domain.role, Role) else str(domain.role),
        is_active=domain.is_active,
        created_at=domain.created_at,
    )

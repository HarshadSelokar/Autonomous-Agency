"""
Company Management Application Service for Phase 25.

Orchestrates company creation, lifecycle state machine transitions, company profile configuration,
and membership management with event publishing.
"""

from datetime import UTC, datetime
from typing import Any, Dict, List, Optional
import uuid

from src.domain.company import (
    Company,
    CompanyProfile,
    CompanyMembership,
    CompanyLifecycle,
    CompanyType,
    CompanyRole,
)
from src.domain.events import (
    CompanyCreatedEvent,
    CompanyActivatedEvent,
    CompanyPausedEvent,
    CompanyResumedEvent,
    CompanySuspendedEvent,
    CompanyArchivedEvent,
    CompanyMemberAddedEvent,
    CompanyMemberRemovedEvent,
)
from src.domain.repository import MultiCompanyRepositoryInterface


class CompanyService:
    """Manages multi-company lifecycle, profiles, and memberships."""

    def __init__(self, repository: MultiCompanyRepositoryInterface, outbox_publisher: Optional[Any] = None) -> None:
        self.repository = repository
        self.outbox_publisher = outbox_publisher

    def _publish_event(self, event: Any) -> None:
        if self.outbox_publisher and hasattr(self.outbox_publisher, "publish"):
            self.outbox_publisher.publish(event)

    async def create_company(
        self,
        name: str,
        slug: str,
        description: str = "",
        legal_name: str = "",
        company_type: CompanyType = CompanyType.AUTONOMOUS,
        industry: str = "TECHNOLOGY",
        currency: str = "USD",
        owner_id: str = "SYSTEM",
    ) -> Company:
        existing = await self.repository.get_company_by_slug(slug)
        if existing:
            raise ValueError(f"Company with slug '{slug}' already exists.")

        company = Company(
            id=str(uuid.uuid4()),
            name=name,
            slug=slug,
            description=description,
            legal_name=legal_name,
            company_type=company_type,
            industry=industry,
            currency=currency,
            lifecycle=CompanyLifecycle.PROPOSED,
            owner_id=owner_id,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        saved = await self.repository.save_company(company)

        # Create default company profile
        profile = CompanyProfile(
            id=str(uuid.uuid4()),
            company_id=saved.id,
            operating_hours="24/7",
            updated_at=datetime.now(UTC),
        )
        await self.repository.save_company_profile(profile)

        # Create initial owner membership
        if owner_id:
            membership = CompanyMembership(
                id=str(uuid.uuid4()),
                company_id=saved.id,
                user_id=owner_id,
                role=CompanyRole.OWNER,
                assigned_at=datetime.now(UTC),
            )
            await self.repository.save_membership(membership)

        self._publish_event(
            CompanyCreatedEvent(
                company_id=saved.id,
                name=saved.name,
                slug=saved.slug,
                company_type=saved.company_type.value,
            )
        )
        return saved

    async def transition_company_lifecycle(
        self,
        company_id: str,
        target_lifecycle: CompanyLifecycle,
        actor_id: str = "SYSTEM",
        reason: str = "",
    ) -> Company:
        company = await self.repository.get_company_by_id(company_id)
        if not company:
            raise ValueError(f"Company '{company_id}' not found.")

        prev_lifecycle = company.lifecycle
        company.transition_lifecycle(target_lifecycle)
        saved = await self.repository.save_company(company)

        # Publish specific lifecycle domain events
        if target_lifecycle == CompanyLifecycle.ACTIVE:
            self._publish_event(CompanyActivatedEvent(company_id=saved.id))
        elif target_lifecycle == CompanyLifecycle.PAUSED:
            self._publish_event(CompanyPausedEvent(company_id=saved.id, paused_by=actor_id, reason=reason))
        elif target_lifecycle == CompanyLifecycle.SUSPENDED:
            self._publish_event(CompanySuspendedEvent(company_id=saved.id, suspended_by=actor_id, reason=reason))
        elif target_lifecycle == CompanyLifecycle.ARCHIVED:
            self._publish_event(CompanyArchivedEvent(company_id=saved.id, archived_by=actor_id))

        return saved

    async def add_company_member(self, company_id: str, user_id: str, role: CompanyRole = CompanyRole.VIEWER) -> CompanyMembership:
        company = await self.repository.get_company_by_id(company_id)
        if not company:
            raise ValueError(f"Company '{company_id}' not found.")

        membership = CompanyMembership(
            id=str(uuid.uuid4()),
            company_id=company_id,
            user_id=user_id,
            role=role,
            assigned_at=datetime.now(UTC),
        )
        saved = await self.repository.save_membership(membership)
        self._publish_event(CompanyMemberAddedEvent(company_id=company_id, user_id=user_id, role=role.value))
        return saved

    async def get_company_profile(self, company_id: str) -> Optional[CompanyProfile]:
        return await self.repository.get_company_profile(company_id)

    async def update_company_profile(
        self,
        company_id: str,
        model_routing_policy: Optional[Dict[str, Any]] = None,
        tool_policy: Optional[Dict[str, Any]] = None,
        governance_defaults: Optional[Dict[str, Any]] = None,
    ) -> CompanyProfile:
        profile = await self.repository.get_company_profile(company_id)
        if not profile:
            profile = CompanyProfile(id=str(uuid.uuid4()), company_id=company_id)

        if model_routing_policy is not None:
            profile.model_routing_policy = model_routing_policy
        if tool_policy is not None:
            profile.tool_policy = tool_policy
        if governance_defaults is not None:
            profile.governance_defaults = governance_defaults

        profile.updated_at = datetime.now(UTC)
        return await self.repository.save_company_profile(profile)

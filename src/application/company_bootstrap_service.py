"""
Company Bootstrap & Template Application Service for Phase 25.

Orchestrates controlled, idempotent initialization of new autonomous companies from templates.
"""

from datetime import UTC, datetime
from typing import Any, Dict, List, Optional
import uuid

from src.domain.company import (
    Company,
    CompanyTemplate,
    CompanyLifecycle,
    CompanyProfile,
    CompanyResourceQuota,
)
from src.domain.events import CompanyInitializedEvent
from src.domain.repository import MultiCompanyRepositoryInterface


class CompanyBootstrapService:
    """Idempotently bootstraps company organizational structures, defaults, and governance."""

    def __init__(self, repository: MultiCompanyRepositoryInterface, outbox_publisher: Optional[Any] = None) -> None:
        self.repository = repository
        self.outbox_publisher = outbox_publisher

    def _publish_event(self, event: Any) -> None:
        if self.outbox_publisher and hasattr(self.outbox_publisher, "publish"):
            self.outbox_publisher.publish(event)

    async def create_template(
        self,
        name: str,
        description: str,
        industry: str,
        default_departments: List[str],
        default_roles: List[str],
        structure_json: Optional[Dict[str, Any]] = None,
    ) -> CompanyTemplate:
        tmpl = CompanyTemplate(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            industry=industry,
            default_departments=default_departments,
            default_roles=default_roles,
            structure_json=structure_json or {},
            created_at=datetime.now(UTC),
        )
        return await self.repository.save_template(tmpl)

    async def bootstrap_company(
        self,
        company_id: str,
        template_id: Optional[str] = None,
        custom_governance: Optional[Dict[str, Any]] = None,
    ) -> Company:
        company = await self.repository.get_company_by_id(company_id)
        if not company:
            raise ValueError(f"Company '{company_id}' not found.")

        # If already ACTIVE or ARCHIVED, idempotent return
        if company.lifecycle in [CompanyLifecycle.ACTIVE, CompanyLifecycle.ARCHIVED]:
            return company

        # Advance lifecycle to INITIALIZING if PROPOSED
        if company.lifecycle == CompanyLifecycle.PROPOSED:
            company.transition_lifecycle(CompanyLifecycle.INITIALIZING)
            await self.repository.save_company(company)

        # Apply template structure if provided
        template = None
        if template_id:
            template = await self.repository.get_template_by_id(template_id)

        profile = await self.repository.get_company_profile(company_id)
        if not profile:
            profile = CompanyProfile(id=str(uuid.uuid4()), company_id=company_id)

        if template:
            profile.workforce_config = {
                "template_name": template.name,
                "departments": template.default_departments,
                "roles": template.default_roles,
                "structure": template.structure_json,
            }
            profile.governance_defaults = custom_governance or {"autonomy_level": "GOVERNED", "max_spend_cents": 500000}
            await self.repository.save_company_profile(profile)

        # Initialize default company resource quota
        quota = await self.repository.get_resource_quota_by_company_id(company_id)
        if not quota:
            quota = CompanyResourceQuota(
                id=str(uuid.uuid4()),
                company_id=company_id,
                max_concurrent_tasks=100,
                max_concurrent_agents=50,
                max_monthly_model_calls=100000,
                max_storage_mb=50000,
                max_simulations=10,
                updated_at=datetime.now(UTC),
            )
            await self.repository.save_resource_quota(quota)

        # Transition company lifecycle to ACTIVE
        company.transition_lifecycle(CompanyLifecycle.ACTIVE)
        activated_company = await self.repository.save_company(company)

        self._publish_event(CompanyInitializedEvent(company_id=activated_company.id, template_id=template_id))
        return activated_company

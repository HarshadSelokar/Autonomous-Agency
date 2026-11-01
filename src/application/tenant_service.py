"""
Application Service for managing Multi-Tenant lifecycle, configuration, and isolation boundaries (Phase 32).
"""

import uuid
from typing import Any
from src.domain.tenant import Tenant, TenantConfiguration, TenantPlan, TenantStatus
from src.domain.exceptions import TenantNotFoundError, DuplicateTenantError
from src.infrastructure.repositories.tenant_repository import SQLAlchemyTenantRepository


class TenantService:
    def __init__(self, tenant_repo: SQLAlchemyTenantRepository | None = None) -> None:
        self.tenant_repo = tenant_repo

    async def create_tenant(
        self,
        name: str,
        slug: str,
        plan: str = "FREE",
        configuration: dict[str, Any] | None = None,
        tenant_id: str | None = None,
    ) -> Tenant:
        existing = await self.tenant_repo.get_by_slug(slug)
        if existing:
            raise DuplicateTenantError(slug)

        t_id = tenant_id or f"tenant-{uuid.uuid4().hex[:12]}"
        
        config_obj = TenantConfiguration()
        if configuration:
            config_obj = TenantConfiguration(
                max_users=configuration.get("max_users", 100),
                max_projects=configuration.get("max_projects", 50),
                max_workflows=configuration.get("max_workflows", 20),
                allowed_providers=configuration.get("allowed_providers", ["groq", "fake"]),
                custom_settings=configuration.get("custom_settings", {}),
            )

        tenant = Tenant(
            id=t_id,
            name=name,
            slug=slug,
            status=TenantStatus.ACTIVE,
            plan=TenantPlan(plan.upper()),
            configuration=config_obj,
        )
        return await self.tenant_repo.save(tenant)

    async def get_tenant(self, tenant_id: str) -> Tenant:
        tenant = await self.tenant_repo.get_by_id(tenant_id)
        if not tenant:
            raise TenantNotFoundError(tenant_id)
        return tenant

    async def get_tenant_by_slug(self, slug: str) -> Tenant:
        tenant = await self.tenant_repo.get_by_slug(slug)
        if not tenant:
            raise TenantNotFoundError(slug)
        return tenant

    async def list_tenants(self, limit: int = 100, offset: int = 0) -> list[Tenant]:
        return await self.tenant_repo.list_all(limit=limit, offset=offset)

    async def update_tenant_configuration(
        self, tenant_id: str, new_config: dict[str, Any]
    ) -> Tenant:
        tenant = await self.get_tenant(tenant_id)
        current_config = tenant.configuration
        updated_config = TenantConfiguration(
            max_users=new_config.get("max_users", current_config.max_users),
            max_projects=new_config.get("max_projects", current_config.max_projects),
            max_workflows=new_config.get("max_workflows", current_config.max_workflows),
            allowed_providers=new_config.get("allowed_providers", current_config.allowed_providers),
            custom_settings=new_config.get("custom_settings", current_config.custom_settings),
        )
        tenant.configuration = updated_config
        return await self.tenant_repo.save(tenant)

    async def update_tenant_plan(self, tenant_id: str, new_plan: str) -> Tenant:
        tenant = await self.get_tenant(tenant_id)
        tenant.plan = TenantPlan(new_plan.upper())
        return await self.tenant_repo.save(tenant)

    async def transition_tenant_status(self, tenant_id: str, target_status: str) -> Tenant:
        tenant = await self.get_tenant(tenant_id)
        tenant.transition_to(TenantStatus(target_status.upper()))
        return await self.tenant_repo.save(tenant)

    async def delete_tenant(self, tenant_id: str) -> bool:
        await self.get_tenant(tenant_id)
        return await self.tenant_repo.delete(tenant_id)

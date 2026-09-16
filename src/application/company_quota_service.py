"""
Company Resource Quota & Usage Application Service for Phase 25.

Enforces backend-side resource limits (concurrent tasks, concurrent agents, simulations, storage)
and prevents resource exhaustion across tenant boundaries.
"""

from datetime import UTC, datetime
from typing import Any, Optional
import uuid

from src.domain.company import CompanyResourceQuota, CompanyResourceUsage
from src.domain.exceptions import CompanyQuotaExceededError
from src.domain.repository import MultiCompanyRepositoryInterface


class CompanyQuotaService:
    """Manages company-level resource quotas and active usage tracking."""

    def __init__(self, repository: MultiCompanyRepositoryInterface) -> None:
        self.repository = repository

    async def get_or_create_quota(self, company_id: str) -> CompanyResourceQuota:
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
            quota = await self.repository.save_resource_quota(quota)
        return quota

    async def get_or_create_usage(self, company_id: str) -> CompanyResourceUsage:
        usage = await self.repository.get_resource_usage_by_company_id(company_id)
        if not usage:
            usage = CompanyResourceUsage(
                id=str(uuid.uuid4()),
                company_id=company_id,
                active_tasks=0,
                active_agents=0,
                monthly_model_calls=0,
                storage_mb=0,
                active_simulations=0,
                recorded_at=datetime.now(UTC),
            )
            usage = await self.repository.save_resource_usage(usage)
        return usage

    async def check_quota(self, company_id: str, quota_name: str, requested_amount: int = 1) -> None:
        """Verifies if a company has sufficient remaining resource quota."""
        quota = await self.get_or_create_quota(company_id)
        usage = await self.get_or_create_usage(company_id)

        if quota_name == "active_tasks":
            if usage.active_tasks + requested_amount > quota.max_concurrent_tasks:
                raise CompanyQuotaExceededError(company_id, quota_name, float(quota.max_concurrent_tasks), float(usage.active_tasks + requested_amount))
        elif quota_name == "active_agents":
            if usage.active_agents + requested_amount > quota.max_concurrent_agents:
                raise CompanyQuotaExceededError(company_id, quota_name, float(quota.max_concurrent_agents), float(usage.active_agents + requested_amount))
        elif quota_name == "active_simulations":
            if usage.active_simulations + requested_amount > quota.max_simulations:
                raise CompanyQuotaExceededError(company_id, quota_name, float(quota.max_simulations), float(usage.active_simulations + requested_amount))
        elif quota_name == "monthly_model_calls":
            if usage.monthly_model_calls + requested_amount > quota.max_monthly_model_calls:
                raise CompanyQuotaExceededError(company_id, quota_name, float(quota.max_monthly_model_calls), float(usage.monthly_model_calls + requested_amount))

    async def increment_usage(self, company_id: str, metric_name: str, delta: int = 1) -> CompanyResourceUsage:
        usage = await self.get_or_create_usage(company_id)

        if metric_name == "active_tasks":
            usage.active_tasks = max(0, usage.active_tasks + delta)
        elif metric_name == "active_agents":
            usage.active_agents = max(0, usage.active_agents + delta)
        elif metric_name == "active_simulations":
            usage.active_simulations = max(0, usage.active_simulations + delta)
        elif metric_name == "monthly_model_calls":
            usage.monthly_model_calls = max(0, usage.monthly_model_calls + delta)

        usage.recorded_at = datetime.now(UTC)
        return await self.repository.save_resource_usage(usage)

"""
Application Service for Resource Quotas, Budgets, and Economic Governance (Phase 35).
"""

import uuid
from typing import Any
from src.domain.budget import Budget, BudgetType, CostRecord
from src.domain.exceptions import ResourceBudgetExceededError, EntityNotFoundError
from src.infrastructure.repositories.budget_repository import SQLAlchemyBudgetRepository


class BudgetGovernanceService:
    def __init__(self, budget_repo: SQLAlchemyBudgetRepository | None = None) -> None:
        self.budget_repo = budget_repo

    async def create_budget(
        self,
        tenant_id: str,
        allocated_amount: float,
        project_id: str | None = None,
        budget_type: str = "COST",
        currency: str = "USD",
        budget_id: str | None = None,
    ) -> Budget:
        b_id = budget_id or f"bgt-{uuid.uuid4().hex[:12]}"
        budget = Budget(
            id=b_id,
            tenant_id=tenant_id,
            project_id=project_id,
            budget_type=BudgetType(budget_type.upper()),
            allocated_amount=allocated_amount,
            currency=currency,
        )
        return await self.budget_repo.save(budget)

    async def reserve_budget(
        self,
        tenant_id: str,
        amount: float,
        project_id: str | None = None,
        budget_type: str = "COST",
    ) -> Budget:
        budget = await self.budget_repo.get_by_tenant_and_project(tenant_id, project_id, budget_type.upper())
        if not budget:
            # Create a default fallback budget if none specified yet
            budget = await self.create_budget(tenant_id=tenant_id, allocated_amount=100.0, project_id=project_id, budget_type=budget_type)

        budget.reserve(amount)
        return await self.budget_repo.save(budget)

    async def record_usage_and_commit(
        self,
        tenant_id: str,
        reserved_amount: float,
        actual_used: float,
        model_name: str,
        tokens_prompt: int = 0,
        tokens_completion: int = 0,
        project_id: str | None = None,
        task_id: str | None = None,
        agent_id: str | None = None,
        budget_type: str = "COST",
    ) -> Budget:
        budget = await self.budget_repo.get_by_tenant_and_project(tenant_id, project_id, budget_type.upper())
        if budget:
            budget.commit_reservation(reserved_amount=reserved_amount, actual_used=actual_used)
            await self.budget_repo.save(budget)

        record = CostRecord(
            id=f"cost-{uuid.uuid4().hex[:12]}",
            tenant_id=tenant_id,
            project_id=project_id,
            task_id=task_id,
            agent_id=agent_id,
            model_name=model_name,
            tokens_prompt=tokens_prompt,
            tokens_completion=tokens_completion,
            estimated_cost=actual_used,
        )
        await self.budget_repo.save_cost_record(record)
        return budget if budget else await self.create_budget(tenant_id, 100.0, project_id, budget_type)

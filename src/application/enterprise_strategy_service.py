"""
Application service for Enterprise Objectives, Strategy Cascading, Portfolios, and Capacity Federation.
"""

from typing import Any, Dict, List, Optional

from src.domain.enterprise import (
    EnterpriseObjective,
    ObjectiveCascade,
    ObjectiveScope,
    EnterprisePortfolio,
    PortfolioItem,
    PortfolioCategory,
    PortfolioPriority,
    EnterpriseResourcePool,
    ResourceAllocation,
    EnterpriseCapacitySnapshot,
)
from src.domain.exceptions import ResourceAllocationConflictError
from src.domain.repository import EnterpriseRepositoryInterface


class EnterpriseStrategyService:

    def __init__(self, repository: EnterpriseRepositoryInterface) -> None:
        self.repo = repository

    async def create_enterprise_objective(
        self,
        enterprise_id: str,
        title: str,
        description: str,
        target_metric: str,
        target_value: float = 100.0,
        scope: ObjectiveScope = ObjectiveScope.ENTERPRISE,
        owner_node_id: Optional[str] = None,
    ) -> EnterpriseObjective:

        obj = EnterpriseObjective(
            enterprise_id=enterprise_id,
            title=title,
            description=description,
            target_metric=target_metric,
            target_value=target_value,
            current_value=0.0,
            scope=scope,
            owner_node_id=owner_node_id,
        )
        return await self.repo.save_objective(obj)

    async def cascade_objective(
        self,
        parent_objective_id: str,
        child_objective_id: str,
        child_node_id: str,
        contribution_weight: float = 1.0,
    ) -> ObjectiveCascade:

        parent = await self.repo.get_objective_by_id(parent_objective_id)
        child = await self.repo.get_objective_by_id(child_objective_id)
        if not parent or not child:
            raise ValueError("Parent or child objective not found for cascading.")

        cascade = ObjectiveCascade(
            parent_objective_id=parent_objective_id,
            child_objective_id=child_objective_id,
            child_node_id=child_node_id,
            contribution_weight=contribution_weight,
            alignment_status="ALIGNED",
        )
        return await self.repo.save_objective_cascade(cascade)

    async def create_portfolio(
        self,
        enterprise_id: str,
        name: str,
        description: str = "",
        total_budget_usd: float = 0.0,
    ) -> EnterprisePortfolio:

        portfolio = EnterprisePortfolio(
            enterprise_id=enterprise_id,
            name=name,
            description=description,
            total_budget_usd=total_budget_usd,
        )
        return await self.repo.save_portfolio(portfolio)

    async def add_portfolio_item(
        self,
        portfolio_id: str,
        name: str,
        category: PortfolioCategory,
        reference_id: str,
        priority: PortfolioPriority = PortfolioPriority.MEDIUM,
        allocated_budget_usd: float = 0.0,
        expected_roi: float = 0.20,
    ) -> PortfolioItem:

        portfolio = await self.repo.get_portfolio_by_id(portfolio_id)
        if not portfolio:
            raise ValueError(f"Enterprise portfolio '{portfolio_id}' not found.")

        item = PortfolioItem(
            portfolio_id=portfolio_id,
            name=name,
            category=category,
            reference_id=reference_id,
            priority=priority,
            allocated_budget_usd=allocated_budget_usd,
            expected_roi=expected_roi,
            health_score=1.0,
        )
        return await self.repo.save_portfolio_item(item)

    async def create_resource_pool(
        self,
        enterprise_id: str,
        name: str,
        resource_type: str = "COMPUTE",
        total_capacity: float = 1000.0,
        unit: str = "UNITS",
    ) -> EnterpriseResourcePool:

        pool = EnterpriseResourcePool(
            enterprise_id=enterprise_id,
            name=name,
            resource_type=resource_type,
            total_capacity=total_capacity,
            available_capacity=total_capacity,
            unit=unit,
        )
        return await self.repo.save_resource_pool(pool)

    async def allocate_resource(
        self,
        pool_id: str,
        consumer_node_id: str,
        allocated_amount: float,
    ) -> ResourceAllocation:

        pool = await self.repo.get_resource_pool_by_id(pool_id)
        if not pool:
            raise ValueError(f"Resource pool '{pool_id}' not found.")

        if pool.available_capacity < allocated_amount:
            raise ResourceAllocationConflictError(pool_id, requested=allocated_amount, available=pool.available_capacity)

        pool.available_capacity -= allocated_amount
        await self.repo.save_resource_pool(pool)

        allocation = ResourceAllocation(
            pool_id=pool_id,
            consumer_node_id=consumer_node_id,
            allocated_amount=allocated_amount,
            status="ALLOCATED",
        )
        return await self.repo.save_resource_allocation(allocation)

    async def get_capacity_snapshot(self, enterprise_id: str) -> EnterpriseCapacitySnapshot:
        pools = await self.repo.list_resource_pools_for_enterprise(enterprise_id)
        total_cap = sum(p.total_capacity for p in pools)
        avail_cap = sum(p.available_capacity for p in pools)
        used_pct = ((total_cap - avail_cap) / total_cap * 100.0) if total_cap > 0 else 0.0

        gap_identified = used_pct > 85.0

        return EnterpriseCapacitySnapshot(
            enterprise_id=enterprise_id,
            total_agent_execution_capacity=int(total_cap),
            used_agent_execution_capacity=int(total_cap - avail_cap),
            shared_service_utilization_pct=round(used_pct, 2),
            capacity_gap_identified=gap_identified,
        )

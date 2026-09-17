"""
Application service for Enterprise Multi-Dimensional Health Aggregation, Risks, and Opportunities.
"""

from typing import Any, Dict, List, Optional

from src.domain.enterprise import (
    EnterpriseHealthSnapshot,
    EnterpriseRisk,
    EnterpriseOpportunity,
)
from src.domain.repository import EnterpriseRepositoryInterface


class EnterpriseHealthAndIntelligenceService:

    def __init__(self, repository: EnterpriseRepositoryInterface) -> None:
        self.repo = repository

    async def aggregate_enterprise_health(self, enterprise_id: str) -> EnterpriseHealthSnapshot:
        objectives = await self.repo.list_objectives_for_enterprise(enterprise_id)
        pools = await self.repo.list_resource_pools_for_enterprise(enterprise_id)
        services = await self.repo.list_services_for_enterprise(enterprise_id)
        risks = await self.repo.list_risks_for_enterprise(enterprise_id)

        # Dimension scores
        if not objectives:
            obj_score = 0.95
        else:
            scores = []
            for o in objectives:
                tv = getattr(o, "target_value", 0) or 0
                cv = getattr(o, "current_value", 0) or 0
                scores.append(min(1.0, (cv / tv) if tv > 0 else 1.0))
            obj_score = sum(scores) / len(scores) if scores else 0.95

        if not pools:
            wf_score = 0.90
        else:
            p_scores = []
            for p in pools:
                tc = getattr(p, "total_capacity", 0) or 0
                ac = getattr(p, "available_capacity", 0) or 0
                p_scores.append(ac / tc if tc > 0 else 1.0)
            wf_score = sum(p_scores) / len(p_scores) if p_scores else 0.90

        fin_score = 0.95

        if not services:
            infra_score = 0.99
        else:
            s_scores = []
            for s in services:
                cu = getattr(s, "capacity_units", 0) or 0
                au = getattr(s, "available_units", 0) or 0
                s_scores.append(au / cu if cu > 0 else 1.0)
            infra_score = sum(s_scores) / len(s_scores) if s_scores else 0.99

        gov_score = 1.00 if not risks else max(0.5, 1.0 - (len([r for r in risks if getattr(r, "status", "") == "OPEN"]) * 0.05))


        overall = round((obj_score + wf_score + fin_score + infra_score + gov_score) / 5.0, 3)

        health = EnterpriseHealthSnapshot(
            enterprise_id=enterprise_id,
            objective_health_score=round(obj_score, 3),
            workforce_capacity_score=round(wf_score, 3),
            financial_health_score=round(fin_score, 3),
            infrastructure_health_score=round(infra_score, 3),
            governance_compliance_score=round(gov_score, 3),
            overall_health_score=overall,
            health_signals={
                "objectives_count": len(objectives),
                "resource_pools_count": len(pools),
                "shared_services_count": len(services),
                "open_risks_count": len([r for r in risks if r.status == "OPEN"]),
            },
        )
        return health

    async def record_enterprise_risk(
        self,
        enterprise_id: str,
        title: str,
        description: str,
        impact_usd: float = 500000.0,
        probability: float = 0.25,
        owner_node_id: Optional[str] = None,
    ) -> EnterpriseRisk:

        risk = EnterpriseRisk(
            enterprise_id=enterprise_id,
            title=title,
            description=description,
            impact_usd=impact_usd,
            probability=probability,
            owner_node_id=owner_node_id,
            status="OPEN",
        )
        return await self.repo.save_risk(risk)

    async def record_enterprise_opportunity(
        self,
        enterprise_id: str,
        title: str,
        description: str,
        potential_value_usd: float = 2000000.0,
        confidence: float = 0.80,
    ) -> EnterpriseOpportunity:

        opp = EnterpriseOpportunity(
            enterprise_id=enterprise_id,
            title=title,
            description=description,
            potential_value_usd=potential_value_usd,
            confidence=confidence,
            status="IDENTIFIED",
        )
        return await self.repo.save_opportunity(opp)

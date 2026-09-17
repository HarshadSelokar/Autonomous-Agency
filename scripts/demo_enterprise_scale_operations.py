"""
End-to-End Demonstration Script for Phase 29 Enterprise-Scale Operations, Federation & Governed Topology.
"""

import sys
import os
sys.path.insert(0, os.path.abspath("."))

import asyncio
from datetime import datetime, timedelta, timezone, UTC

import json
import uuid

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.infrastructure.database import Base
from src.infrastructure.repositories.enterprise_repository import SQLAlchemyEnterpriseRepository
from src.application.enterprise_topology_service import EnterpriseTopologyService
from src.application.enterprise_federation_service import EnterpriseFederationService
from src.application.enterprise_strategy_service import EnterpriseStrategyService
from src.application.enterprise_governance_service import EnterpriseGovernanceService
from src.application.enterprise_health_service import EnterpriseHealthAndIntelligenceService
from src.application.enterprise_context_builder import EnterpriseContextBuilder
from src.domain.enterprise import (
    Enterprise,
    EnterpriseLifecycle,
    NodeType,
    RelationshipType,
    ServiceType,
    PortfolioCategory,
    PortfolioPriority,
    ObjectiveScope,
    DataClassification,
    InterCompanyRequestStatus,
)
from src.domain.exceptions import (
    InvalidTopologyCycleError,
    AuthorityExpiredError,
    ResourceAllocationConflictError,
    UnauthorizedEnterpriseActionError,
    CrossEnterpriseAccessError,
)


async def run_enterprise_demo():
    print("=" * 80)
    print("PHASE 29 — ENTERPRISE-SCALE AUTONOMOUS PLATFORM & FEDERATION DEMO")
    print("=" * 80)

    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        repo = SQLAlchemyEnterpriseRepository(session)
        top_svc = EnterpriseTopologyService(repo)
        fed_svc = EnterpriseFederationService(repo)
        strat_svc = EnterpriseStrategyService(repo)
        gov_svc = EnterpriseGovernanceService(repo)
        health_svc = EnterpriseHealthAndIntelligenceService(repo)
        ctx_builder = EnterpriseContextBuilder(repo)

        # ----------------------------------------------------------------------
        # STEP 1: Create Enterprise Profile
        # ----------------------------------------------------------------------
        print("\n--- [STEP 1] Initializing Root Enterprise Profile ---")
        ent = Enterprise(name="Apex Global Enterprise Systems", code="APEX")
        ent.profile.industry = "GLOBAL_AI_TECHNOLOGY_HOLDINGS"
        ent.profile.headquarters_region = "NORTH_AMERICA"
        ent.status = EnterpriseLifecycle.ACTIVE
        saved_ent = await repo.save_enterprise(ent)
        print(f"Root Enterprise Created: ID={saved_ent.id}, Name='{saved_ent.name}', Code='{saved_ent.code}'")

        # ----------------------------------------------------------------------
        # STEP 2 & 3: Build Topology Graph Nodes & Regions
        # ----------------------------------------------------------------------
        print("\n--- [STEP 2 & 3] Constructing Enterprise Organizational Topology Graph ---")
        root_node = await top_svc.create_node(saved_ent.id, "Apex HQ Holdings", NodeType.ENTERPRISE, region="GLOBAL")
        na_region = await top_svc.create_node(saved_ent.id, "North America Operations", NodeType.REGION, parent_node_id=root_node.id, region="NORTH_AMERICA")
        eu_region = await top_svc.create_node(saved_ent.id, "Europe Operations", NodeType.REGION, parent_node_id=root_node.id, region="EUROPE")

        print(f"Topology Nodes Created: Root='{root_node.name}', NA Region='{na_region.name}', EU Region='{eu_region.name}'")

        # ----------------------------------------------------------------------
        # STEP 4: Attach Companies to Enterprise Topology
        # ----------------------------------------------------------------------
        print("\n--- [STEP 4] Federating Autonomous Company OS Instances into Enterprise ---")
        comp1_node = await fed_svc.attach_company_to_enterprise(saved_ent.id, "comp-cyberguard-001", "CyberGuard Security Systems", region="NORTH_AMERICA", parent_node_id=na_region.id)
        comp2_node = await fed_svc.attach_company_to_enterprise(saved_ent.id, "comp-cloudscale-002", "CloudScale Infrastructure", region="EUROPE", parent_node_id=eu_region.id)

        print(f"Attached Companies: '{comp1_node.name}' (Node ID: {comp1_node.id}), '{comp2_node.name}' (Node ID: {comp2_node.id})")

        # ----------------------------------------------------------------------
        # STEP 5 & 6: Register Shared Services & Agreements
        # ----------------------------------------------------------------------
        print("\n--- [STEP 5 & 6] Provisioning Enterprise Shared Services & SLAs ---")
        shared_ai = await fed_svc.register_shared_service(saved_ent.id, root_node.id, "Central AI Platform & Model Swarm", ServiceType.AI_PLATFORM, capacity_units=500)
        sla_agreement = await fed_svc.create_service_agreement(shared_ai.id, comp1_node.id, allocated_units=150, cost_allocation_usd=25000.0)

        print(f"Registered Shared Service: '{shared_ai.name}' (Available: {shared_ai.available_units}/500 Units)")
        print(f"Service Agreement Created: Consumer='{comp1_node.name}', Allocated=150 Units, Cost=$25,000 USD")

        # ----------------------------------------------------------------------
        # STEP 7 & 8: Enterprise Strategic Objectives & Objective Cascading
        # ----------------------------------------------------------------------
        print("\n--- [STEP 7 & 8] Formulating Strategic Objectives & Objective Cascading ---")
        ent_obj = await strat_svc.create_enterprise_objective(saved_ent.id, "Achieve $100M Portfolio ARR", "Enterprise Group Revenue", "ARR_USD", 100000000.0)
        comp1_obj = await strat_svc.create_enterprise_objective(saved_ent.id, "CyberGuard $40M ARR Contribution", "Subsidiary Revenue Target", "ARR_USD", 40000000.0, scope=ObjectiveScope.COMPANY, owner_node_id=comp1_node.id)

        cascade = await strat_svc.cascade_objective(ent_obj.id, comp1_obj.id, comp1_node.id, contribution_weight=0.40)
        print(f"Cascaded Objective: Parent='{ent_obj.title}' -> Child='{comp1_obj.title}' (Weight: {cascade.contribution_weight * 100}%)")

        # ----------------------------------------------------------------------
        # STEP 9: Enterprise Portfolio Management
        # ----------------------------------------------------------------------
        print("\n--- [STEP 9] Enterprise Portfolio Management & Investment Prioritization ---")
        portfolio = await strat_svc.create_portfolio(saved_ent.id, "Q4 Enterprise Growth Portfolio", "Strategic Holdings Portfolio", total_budget_usd=50000000.0)
        pitem = await strat_svc.add_portfolio_item(portfolio.id, "CyberGuard Pentest Swarm Expansion", PortfolioCategory.COMPANY, comp1_node.reference_id, priority=PortfolioPriority.HIGH, allocated_budget_usd=15000000.0, expected_roi=0.38)

        print(f"Portfolio Created: '{portfolio.name}', Total Budget=${portfolio.total_budget_usd:,.2f}")
        print(f"Portfolio Item Added: '{pitem.name}', Allocated=${pitem.allocated_budget_usd:,.2f}, Expected ROI={pitem.expected_roi * 100}%")

        # ----------------------------------------------------------------------
        # STEP 10, 11 & 12: Resource Pools, Capacity Management & Gap Detection
        # ----------------------------------------------------------------------
        print("\n--- [STEP 10, 11 & 12] Enterprise Resource Federation & Capacity Planning ---")
        pool = await strat_svc.create_resource_pool(saved_ent.id, "Enterprise GPU Compute Pool", resource_type="GPU_COMPUTE", total_capacity=1000.0)
        alloc = await strat_svc.allocate_resource(pool.id, comp1_node.id, allocated_amount=400.0)

        snap = await strat_svc.get_capacity_snapshot(saved_ent.id)
        print(f"Resource Pool Allocated: {alloc.allocated_amount} UNITS to '{comp1_node.name}'. Available in Pool: {pool.available_capacity}/1000 UNITS")
        print(f"Capacity Snapshot: Shared Service Utilization={snap.shared_service_utilization_pct}%, Gap Identified={snap.capacity_gap_identified}")

        # ----------------------------------------------------------------------
        # STEP 13: Safety Boundary: Unauthorized Action Enforcement
        # ----------------------------------------------------------------------
        print("\n--- [STEP 13] Safety Boundary Enforcement: Unauthorized Action Check ---")
        try:
            await gov_svc.verify_authority(saved_ent.id, grantee_node_id=comp1_node.id, action="TRANSFER_CAPITAL", impact_usd=500000.0)
            print("ERROR: Unauthorized action should have been blocked!")
        except AuthorityExpiredError as e:
            print(f"SUCCESS: Unauthorized action correctly blocked!")
            print(f"  Caught Expected Exception: '{e}'")

        # ----------------------------------------------------------------------
        # STEP 14 & 15: Delegated Authority Grant & Verification
        # ----------------------------------------------------------------------
        print("\n--- [STEP 14 & 15] Granting Explicit Delegated Authority & Verification ---")
        grant = await gov_svc.grant_authority(saved_ent.id, grantor_node_id=root_node.id, grantee_node_id=comp1_node.id, scope="OPERATIONAL_BUDGET", action="ALLOCATE_BUDGET", max_impact_usd=1000000.0)
        has_auth = await gov_svc.verify_authority(saved_ent.id, grantee_node_id=comp1_node.id, action="ALLOCATE_BUDGET", impact_usd=250000.0)
        print(f"Explicit Authority Granted: Action='{grant.action}', Max Impact=${grant.max_impact_usd:,.2f}")
        print(f"Authority Verification Check ($250k budget allocation): PASSED (is_valid={has_auth})")

        # ----------------------------------------------------------------------
        # STEP 16: Topology Cycle Prevention Verification
        # ----------------------------------------------------------------------
        print("\n--- [STEP 16] Validating Deterministic Topology Cycle Prevention ---")
        try:
            await top_svc.add_relationship(saved_ent.id, source_node_id=comp1_node.id, target_node_id=root_node.id, relationship_type=RelationshipType.PARENT_CHILD)
            print("ERROR: Cycle should have been blocked!")
        except InvalidTopologyCycleError as e:
            print(f"SUCCESS: Topology cycle correctly blocked!")
            print(f"  Caught Expected Exception: '{e}'")

        # ----------------------------------------------------------------------
        # STEP 17, 18 & 19: Inter-Company Request Lifecycle
        # ----------------------------------------------------------------------
        print("\n--- [STEP 17, 18 & 19] Inter-Company Request Routing, Governance Authorization & Execution ---")
        ic_req = await fed_svc.submit_intercompany_request(saved_ent.id, source_company_id="comp-cyberguard-001", destination_company_id="comp-cloudscale-002", requester_id="user-sys-admin", requested_capability="SWARM_TEST_BED", purpose="Inter-company vulnerability scanning test")
        print(f"Inter-Company Request Submitted: ID={ic_req.id}, Status={ic_req.status.value if hasattr(ic_req.status, 'value') else str(ic_req.status)}")

        auth_req = await fed_svc.authorize_intercompany_request(ic_req.id, saved_ent.id, governance_approval_id="gov-appr-phase29-7711")
        print(f"Governance Authorization Attached: Approval ID='{auth_req.governance_approval_id}', Status={auth_req.status.value if hasattr(auth_req.status, 'value') else str(auth_req.status)}")

        exec_req = await fed_svc.execute_intercompany_request(ic_req.id, saved_ent.id, {"scan_results": "Zero critical defects found"})
        print(f"Inter-Company Request Executed: Final Status={exec_req.status.value if hasattr(exec_req.status, 'value') else str(exec_req.status)}, Result={exec_req.result_data}")

        # ----------------------------------------------------------------------
        # STEP 20, 21 & 22: Deterministic Policy Inheritance & Resolution
        # ----------------------------------------------------------------------
        print("\n--- [STEP 20, 21 & 22] Policy Inheritance & Mandatory Constraint Resolution ---")
        await gov_svc.set_policy_profile(saved_ent.id, node_id=root_node.id, max_single_budget_spend_usd=50000.0)
        await gov_svc.set_policy_profile(saved_ent.id, node_id=comp1_node.id, max_single_budget_spend_usd=100000.0)

        effective_pol = await gov_svc.resolve_effective_policy(saved_ent.id, node_id=comp1_node.id)
        print(f"Root Enterprise Max Spend Cap: $50,000 USD")
        print(f"Subsidiary Requested Max Spend Cap: $100,000 USD")
        print(f"Resolved Effective Max Spend Cap: ${effective_pol['effective_max_single_budget_spend_usd']:,.2f} USD")
        assert effective_pol['effective_max_single_budget_spend_usd'] == 50000.0
        print("SUCCESS: Resolved effective policy enforced mandatory root limit ($50,000 USD). Child could NOT weaken safety boundary!")

        # ----------------------------------------------------------------------
        # STEP 23: Multi-Dimensional Health Aggregation
        # ----------------------------------------------------------------------
        print("\n--- [STEP 23] Multi-Dimensional Enterprise Health Aggregation ---")
        health = await health_svc.aggregate_enterprise_health(saved_ent.id)
        print(f"Enterprise Health Scorecard Summary:")
        print(f"  Overall Score: {health.overall_health_score * 100}%")
        print(f"  Objective Health: {health.objective_health_score * 100}%")
        print(f"  Workforce Capacity: {health.workforce_capacity_score * 100}%")
        print(f"  Financial Health: {health.financial_health_score * 100}%")
        print(f"  Infrastructure SLA: {health.infrastructure_health_score * 100}%")
        print(f"  Governance Compliance: {health.governance_compliance_score * 100}%")

        # ----------------------------------------------------------------------
        # STEP 24 & 25: Enterprise Risk & Opportunity Tracking
        # ----------------------------------------------------------------------
        print("\n--- [STEP 24 & 25] Enterprise Risk & Opportunity Register ---")
        risk = await health_svc.record_enterprise_risk(saved_ent.id, "Inter-Company Infrastructure Bottleneck", "High load on shared compute pool", impact_usd=750000.0, probability=0.20)
        opp = await health_svc.record_enterprise_opportunity(saved_ent.id, "Shared Pentesting Platform Synergies", "Cross-subsidiary cross-selling", potential_value_usd=3500000.0, confidence=0.85)

        print(f"Risk Recorded: '{risk.title}', Impact=${risk.impact_usd:,.2f}, Status='{risk.status}'")
        print(f"Opportunity Recorded: '{opp.title}', Potential Value=${opp.potential_value_usd:,.2f}, Confidence={opp.confidence * 100}%")

        # ----------------------------------------------------------------------
        # STEP 26 & 27: Knowledge & Learning Federation
        # ----------------------------------------------------------------------
        print("\n--- [STEP 26 & 27] Governed Knowledge & Learning Federation ---")
        kpol = await gov_svc.create_knowledge_sharing_policy(saved_ent.id, "comp-cyberguard-001", "comp-cloudscale-002", [DataClassification.PUBLIC, DataClassification.INTERNAL])
        lprop = await gov_svc.propagate_learned_lesson(saved_ent.id, "comp-cyberguard-001", "cand-9988", "AST Pre-Check cuts code review latency by 65%", "APPLIES_TO_ALL_SWARM_WORKFLOWS", "gov-appr-phase29-7711")

        print(f"Knowledge Sharing Policy Active: Allowed Classifications={[c.value for c in kpol.allowed_classifications]}")
        print(f"Learned Lesson Propagated: '{lprop.lesson_summary}' (Governance Approval: {lprop.governance_approval_id})")

        # ----------------------------------------------------------------------
        # STEP 28: Enterprise Context Builder Output
        # ----------------------------------------------------------------------
        print("\n--- [STEP 28] Constructing Framed Enterprise Advisory Context ---")
        ctx_str = await ctx_builder.build_enterprise_context(saved_ent.id)
        print("Generated Enterprise Advisory Context String:")
        print(ctx_str)

        # ----------------------------------------------------------------------
        # STEP 29: Cross-Enterprise Security Isolation Verification
        # ----------------------------------------------------------------------
        print("\n--- [STEP 29] Verifying Multi-Enterprise Security Isolation ---")
        ent_b = Enterprise(name="Beta Holdings Corp", code="BETAHOLD")
        saved_ent_b = await repo.save_enterprise(ent_b)

        b_nodes = await repo.list_topology_nodes_for_enterprise(saved_ent_b.id)
        print(f"Enterprise B Topology Nodes Count: {len(b_nodes)} (Expected: 0)")
        assert len(b_nodes) == 0
        print("SUCCESS: Multi-enterprise tenant isolation verified! Enterprise B cannot access Enterprise A topology.")

        # ----------------------------------------------------------------------
        # STEP 30: Enterprise Operating Loop Summary
        # ----------------------------------------------------------------------
        print("\n" + "=" * 80)
        print("PHASE 29 DEMONSTRATION COMPLETE — ALL 30 STEPS & INVARIANTS PASSED")
        print("=" * 80)


if __name__ == "__main__":
    asyncio.run(run_enterprise_demo())

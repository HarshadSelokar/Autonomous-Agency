"""
SQLAlchemy repository implementation for Phase 29 Enterprise OS.
"""

from datetime import datetime, timezone, UTC
import json
from typing import Any, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.enterprise import (
    Enterprise,
    EnterpriseProfile,
    EnterpriseLifecycle,
    EnterpriseOrganizationNode,
    NodeType,
    EnterpriseRelationship,
    RelationshipType,
    EnterpriseService,
    ServiceType,
    EnterpriseServiceAgreement,
    EnterprisePortfolio,
    PortfolioItem,
    PortfolioCategory,
    PortfolioPriority,
    EnterpriseObjective,
    ObjectiveCascade,
    ObjectiveScope,
    EnterprisePolicyProfile,
    AuthorityGrant,
    EnterpriseResourcePool,
    ResourceAllocation,
    InterCompanyRequest,
    InterCompanyRequestStatus,
    EnterpriseRisk,
    EnterpriseOpportunity,
    DataClassification,
)
from src.domain.repository import EnterpriseRepositoryInterface
from src.infrastructure.models.enterprise_model import (
    EnterpriseModel,
    EnterpriseOrganizationNodeModel,
    EnterpriseRelationshipModel,
    EnterpriseServiceModel,
    EnterpriseServiceAgreementModel,
    EnterprisePortfolioModel,
    EnterprisePortfolioItemModel,
    EnterpriseObjectiveModel,
    ObjectiveCascadeModel,
    EnterprisePolicyProfileModel,
    AuthorityGrantModel,
    EnterpriseResourcePoolModel,
    ResourceAllocationModel,
    InterCompanyRequestModel,
    EnterpriseRiskModel,
    EnterpriseOpportunityModel,
)


class SQLAlchemyEnterpriseRepository(EnterpriseRepositoryInterface):

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # 1. Enterprises
    async def save_enterprise(self, enterprise: Enterprise) -> Enterprise:
        stmt = select(EnterpriseModel).where(EnterpriseModel.id == enterprise.id)
        res = await self.session.execute(stmt)
        model = res.scalar_one_or_none()

        profile_data = {
            "industry": enterprise.profile.industry,
            "headquarters_region": enterprise.profile.headquarters_region,
            "operating_currency": enterprise.profile.operating_currency,
            "description": enterprise.profile.description,
            "metadata": enterprise.profile.metadata,
        }

        if not model:
            model = EnterpriseModel(
                id=enterprise.id,
                name=enterprise.name,
                code=enterprise.code,
                status=enterprise.status.value if hasattr(enterprise.status, "value") else str(enterprise.status),
                profile_json=json.dumps(profile_data),
                created_at=enterprise.created_at,
                updated_at=enterprise.updated_at,
            )
            self.session.add(model)
        else:
            model.name = enterprise.name
            model.code = enterprise.code
            model.status = enterprise.status.value if hasattr(enterprise.status, "value") else str(enterprise.status)
            model.profile_json = json.dumps(profile_data)
            model.updated_at = datetime.now(UTC)

        await self.session.commit()
        return enterprise

    async def get_enterprise_by_id(self, enterprise_id: str) -> Optional[Enterprise]:
        stmt = select(EnterpriseModel).where(EnterpriseModel.id == enterprise_id)
        res = await self.session.execute(stmt)
        model = res.scalar_one_or_none()
        if not model:
            return None

        p_data = json.loads(model.profile_json or "{}")
        profile = EnterpriseProfile(
            industry=p_data.get("industry", "GLOBAL_TECHNOLOGY_ENTERPRISE"),
            headquarters_region=p_data.get("headquarters_region", "NORTH_AMERICA"),
            operating_currency=p_data.get("operating_currency", "USD"),
            description=p_data.get("description", ""),
            metadata=p_data.get("metadata", {}),
        )
        return Enterprise(
            id=model.id,
            name=model.name,
            code=model.code,
            status=EnterpriseLifecycle(model.status),
            profile=profile,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    async def get_enterprise_by_code(self, code: str) -> Optional[Enterprise]:
        stmt = select(EnterpriseModel).where(EnterpriseModel.code == code)
        res = await self.session.execute(stmt)
        model = res.scalar_one_or_none()
        if not model:
            return None
        return await self.get_enterprise_by_id(model.id)

    async def list_enterprises(self) -> List[Enterprise]:
        stmt = select(EnterpriseModel)
        res = await self.session.execute(stmt)
        models = res.scalars().all()
        result = []
        for m in models:
            ent = await self.get_enterprise_by_id(m.id)
            if ent:
                result.append(ent)
        return result

    # 2. Topology Nodes
    async def save_topology_node(self, node: EnterpriseOrganizationNode) -> EnterpriseOrganizationNode:
        stmt = select(EnterpriseOrganizationNodeModel).where(EnterpriseOrganizationNodeModel.id == node.id)
        res = await self.session.execute(stmt)
        model = res.scalar_one_or_none()

        if not model:
            model = EnterpriseOrganizationNodeModel(
                id=node.id,
                enterprise_id=node.enterprise_id,
                name=node.name,
                node_type=node.node_type.value if hasattr(node.node_type, "value") else str(node.node_type),
                reference_id=node.reference_id,
                parent_node_id=node.parent_node_id,
                region=node.region,
                data_classification=node.data_classification.value if hasattr(node.data_classification, "value") else str(node.data_classification),
                metadata_json=json.dumps(node.metadata),
                created_at=node.created_at,
            )
            self.session.add(model)
        else:
            model.name = node.name
            model.node_type = node.node_type.value if hasattr(node.node_type, "value") else str(node.node_type)
            model.reference_id = node.reference_id
            model.parent_node_id = node.parent_node_id
            model.region = node.region
            model.data_classification = node.data_classification.value if hasattr(node.data_classification, "value") else str(node.data_classification)
            model.metadata_json = json.dumps(node.metadata)

        await self.session.commit()
        return node

    async def get_topology_node_by_id(self, node_id: str) -> Optional[EnterpriseOrganizationNode]:
        stmt = select(EnterpriseOrganizationNodeModel).where(EnterpriseOrganizationNodeModel.id == node_id)
        res = await self.session.execute(stmt)
        model = res.scalar_one_or_none()
        if not model:
            return None

        return EnterpriseOrganizationNode(
            id=model.id,
            enterprise_id=model.enterprise_id,
            name=model.name,
            node_type=NodeType(model.node_type),
            reference_id=model.reference_id,
            parent_node_id=model.parent_node_id,
            region=model.region,
            data_classification=DataClassification(model.data_classification),
            metadata=json.loads(model.metadata_json or "{}"),
            created_at=model.created_at,
        )

    async def list_topology_nodes_for_enterprise(self, enterprise_id: str) -> List[EnterpriseOrganizationNode]:
        stmt = select(EnterpriseOrganizationNodeModel).where(EnterpriseOrganizationNodeModel.enterprise_id == enterprise_id)
        res = await self.session.execute(stmt)
        models = res.scalars().all()
        return [
            EnterpriseOrganizationNode(
                id=m.id,
                enterprise_id=m.enterprise_id,
                name=m.name,
                node_type=NodeType(m.node_type),
                reference_id=m.reference_id,
                parent_node_id=m.parent_node_id,
                region=m.region,
                data_classification=DataClassification(m.data_classification),
                metadata=json.loads(m.metadata_json or "{}"),
                created_at=m.created_at,
            )
            for m in models
        ]

    # 3. Relationships
    async def save_relationship(self, relationship: EnterpriseRelationship) -> EnterpriseRelationship:
        model = EnterpriseRelationshipModel(
            id=relationship.id,
            enterprise_id=relationship.enterprise_id,
            source_node_id=relationship.source_node_id,
            target_node_id=relationship.target_node_id,
            relationship_type=relationship.relationship_type.value if hasattr(relationship.relationship_type, "value") else str(relationship.relationship_type),
            description=relationship.description,
            metadata_json=json.dumps(relationship.metadata),
            created_at=relationship.created_at,
        )
        self.session.add(model)
        await self.session.commit()
        return relationship

    async def list_relationships_for_enterprise(self, enterprise_id: str) -> List[EnterpriseRelationship]:
        stmt = select(EnterpriseRelationshipModel).where(EnterpriseRelationshipModel.enterprise_id == enterprise_id)
        res = await self.session.execute(stmt)
        models = res.scalars().all()
        return [
            EnterpriseRelationship(
                id=m.id,
                enterprise_id=m.enterprise_id,
                source_node_id=m.source_node_id,
                target_node_id=m.target_node_id,
                relationship_type=RelationshipType(m.relationship_type),
                description=m.description,
                metadata=json.loads(m.metadata_json or "{}"),
                created_at=m.created_at,
            )
            for m in models
        ]

    # 4. Shared Services
    async def save_service(self, service: EnterpriseService) -> EnterpriseService:
        stmt = select(EnterpriseServiceModel).where(EnterpriseServiceModel.id == service.id)
        res = await self.session.execute(stmt)
        model = res.scalar_one_or_none()

        if not model:
            model = EnterpriseServiceModel(
                id=service.id,
                enterprise_id=service.enterprise_id,
                owner_node_id=service.owner_node_id,
                name=service.name,
                service_type=service.service_type.value if hasattr(service.service_type, "value") else str(service.service_type),
                capacity_units=service.capacity_units,
                available_units=service.available_units,
                sla_description=service.sla_description,
                governance_required=service.governance_required,
                metadata_json=json.dumps(service.metadata),
                created_at=service.created_at,
            )
            self.session.add(model)
        else:
            model.name = service.name
            model.capacity_units = service.capacity_units
            model.available_units = service.available_units
            model.sla_description = service.sla_description
            model.governance_required = service.governance_required
            model.metadata_json = json.dumps(service.metadata)

        await self.session.commit()
        return service

    async def get_service_by_id(self, service_id: str) -> Optional[EnterpriseService]:
        stmt = select(EnterpriseServiceModel).where(EnterpriseServiceModel.id == service_id)
        res = await self.session.execute(stmt)
        model = res.scalar_one_or_none()
        if not model:
            return None

        return EnterpriseService(
            id=model.id,
            enterprise_id=model.enterprise_id,
            owner_node_id=model.owner_node_id,
            name=model.name,
            service_type=ServiceType(model.service_type),
            capacity_units=model.capacity_units,
            available_units=model.available_units,
            sla_description=model.sla_description,
            governance_required=model.governance_required,
            metadata=json.loads(model.metadata_json or "{}"),
            created_at=model.created_at,
        )

    async def list_services_for_enterprise(self, enterprise_id: str) -> List[EnterpriseService]:
        stmt = select(EnterpriseServiceModel).where(EnterpriseServiceModel.enterprise_id == enterprise_id)
        res = await self.session.execute(stmt)
        models = res.scalars().all()
        return [
            EnterpriseService(
                id=m.id,
                enterprise_id=m.enterprise_id,
                owner_node_id=m.owner_node_id,
                name=m.name,
                service_type=ServiceType(m.service_type),
                capacity_units=m.capacity_units,
                available_units=m.available_units,
                sla_description=m.sla_description,
                governance_required=m.governance_required,
                metadata=json.loads(m.metadata_json or "{}"),
                created_at=m.created_at,
            )
            for m in models
        ]

    async def save_service_agreement(self, agreement: EnterpriseServiceAgreement) -> EnterpriseServiceAgreement:
        model = EnterpriseServiceAgreementModel(
            id=agreement.id,
            service_id=agreement.service_id,
            consumer_node_id=agreement.consumer_node_id,
            allocated_units=agreement.allocated_units,
            cost_allocation_usd=agreement.cost_allocation_usd,
            status=agreement.status,
            created_at=agreement.created_at,
        )
        self.session.add(model)
        await self.session.commit()
        return agreement

    async def list_agreements_for_service(self, service_id: str) -> List[EnterpriseServiceAgreement]:
        stmt = select(EnterpriseServiceAgreementModel).where(EnterpriseServiceAgreementModel.service_id == service_id)
        res = await self.session.execute(stmt)
        models = res.scalars().all()
        return [
            EnterpriseServiceAgreement(
                id=m.id,
                service_id=m.service_id,
                consumer_node_id=m.consumer_node_id,
                allocated_units=m.allocated_units,
                cost_allocation_usd=m.cost_allocation_usd,
                status=m.status,
                created_at=m.created_at,
            )
            for m in models
        ]

    # 5. Portfolios
    async def save_portfolio(self, portfolio: EnterprisePortfolio) -> EnterprisePortfolio:
        stmt = select(EnterprisePortfolioModel).where(EnterprisePortfolioModel.id == portfolio.id)
        res = await self.session.execute(stmt)
        model = res.scalar_one_or_none()

        if not model:
            model = EnterprisePortfolioModel(
                id=portfolio.id,
                enterprise_id=portfolio.enterprise_id,
                name=portfolio.name,
                description=portfolio.description,
                total_budget_usd=portfolio.total_budget_usd,
                created_at=portfolio.created_at,
            )
            self.session.add(model)
        else:
            model.name = portfolio.name
            model.description = portfolio.description
            model.total_budget_usd = portfolio.total_budget_usd

        await self.session.commit()

        for item in portfolio.items:
            await self.save_portfolio_item(item)

        return portfolio

    async def get_portfolio_by_id(self, portfolio_id: str) -> Optional[EnterprisePortfolio]:
        stmt = select(EnterprisePortfolioModel).where(EnterprisePortfolioModel.id == portfolio_id)
        res = await self.session.execute(stmt)
        model = res.scalar_one_or_none()
        if not model:
            return None

        items = await self.list_items_for_portfolio(portfolio_id)
        return EnterprisePortfolio(
            id=model.id,
            enterprise_id=model.enterprise_id,
            name=model.name,
            description=model.description,
            total_budget_usd=model.total_budget_usd,
            items=items,
            created_at=model.created_at,
        )

    async def list_portfolios_for_enterprise(self, enterprise_id: str) -> List[EnterprisePortfolio]:
        stmt = select(EnterprisePortfolioModel).where(EnterprisePortfolioModel.enterprise_id == enterprise_id)
        res = await self.session.execute(stmt)
        models = res.scalars().all()
        result = []
        for m in models:
            items = await self.list_items_for_portfolio(m.id)
            result.append(
                EnterprisePortfolio(
                    id=m.id,
                    enterprise_id=m.enterprise_id,
                    name=m.name,
                    description=m.description,
                    total_budget_usd=m.total_budget_usd,
                    items=items,
                    created_at=m.created_at,
                )
            )
        return result

    async def save_portfolio_item(self, item: PortfolioItem) -> PortfolioItem:
        model = EnterprisePortfolioItemModel(
            id=item.id,
            portfolio_id=item.portfolio_id,
            name=item.name,
            category=item.category.value if hasattr(item.category, "value") else str(item.category),
            reference_id=item.reference_id,
            priority=item.priority.value if hasattr(item.priority, "value") else str(item.priority),
            allocated_budget_usd=item.allocated_budget_usd,
            expected_roi=item.expected_roi,
            health_score=item.health_score,
            created_at=item.created_at,
        )
        self.session.add(model)
        await self.session.commit()
        return item

    async def list_items_for_portfolio(self, portfolio_id: str) -> List[PortfolioItem]:
        stmt = select(EnterprisePortfolioItemModel).where(EnterprisePortfolioItemModel.portfolio_id == portfolio_id)
        res = await self.session.execute(stmt)
        models = res.scalars().all()
        return [
            PortfolioItem(
                id=m.id,
                portfolio_id=m.portfolio_id,
                name=m.name,
                category=PortfolioCategory(m.category),
                reference_id=m.reference_id,
                priority=PortfolioPriority(m.priority),
                allocated_budget_usd=m.allocated_budget_usd,
                expected_roi=m.expected_roi,
                health_score=m.health_score,
                created_at=m.created_at,
            )
            for m in models
        ]

    # 6. Objectives & Cascades
    async def save_objective(self, objective: EnterpriseObjective) -> EnterpriseObjective:
        stmt = select(EnterpriseObjectiveModel).where(EnterpriseObjectiveModel.id == objective.id)
        res = await self.session.execute(stmt)
        model = res.scalar_one_or_none()

        if not model:
            model = EnterpriseObjectiveModel(
                id=objective.id,
                enterprise_id=objective.enterprise_id,
                title=objective.title,
                description=objective.description,
                target_metric=objective.target_metric,
                target_value=objective.target_value,
                current_value=objective.current_value,
                scope=objective.scope.value if hasattr(objective.scope, "value") else str(objective.scope),
                owner_node_id=objective.owner_node_id,
                created_at=objective.created_at,
            )
            self.session.add(model)
        else:
            model.title = objective.title
            model.description = objective.description
            model.target_metric = objective.target_metric
            model.target_value = objective.target_value
            model.current_value = objective.current_value
            model.scope = objective.scope.value if hasattr(objective.scope, "value") else str(objective.scope)
            model.owner_node_id = objective.owner_node_id

        await self.session.commit()
        return objective

    async def get_objective_by_id(self, objective_id: str) -> Optional[EnterpriseObjective]:
        stmt = select(EnterpriseObjectiveModel).where(EnterpriseObjectiveModel.id == objective_id)
        res = await self.session.execute(stmt)
        model = res.scalar_one_or_none()
        if not model:
            return None

        return EnterpriseObjective(
            id=model.id,
            enterprise_id=model.enterprise_id,
            title=model.title,
            description=model.description,
            target_metric=model.target_metric,
            target_value=model.target_value,
            current_value=model.current_value,
            scope=ObjectiveScope(model.scope),
            owner_node_id=model.owner_node_id,
            created_at=model.created_at,
        )

    async def list_objectives_for_enterprise(self, enterprise_id: str) -> List[EnterpriseObjective]:
        stmt = select(EnterpriseObjectiveModel).where(EnterpriseObjectiveModel.enterprise_id == enterprise_id)
        res = await self.session.execute(stmt)
        models = res.scalars().all()
        return [
            EnterpriseObjective(
                id=m.id,
                enterprise_id=m.enterprise_id,
                title=m.title,
                description=m.description,
                target_metric=m.target_metric,
                target_value=m.target_value,
                current_value=m.current_value,
                scope=ObjectiveScope(m.scope),
                owner_node_id=m.owner_node_id,
                created_at=m.created_at,
            )
            for m in models
        ]

    async def save_objective_cascade(self, cascade: ObjectiveCascade) -> ObjectiveCascade:
        model = ObjectiveCascadeModel(
            id=cascade.id,
            parent_objective_id=cascade.parent_objective_id,
            child_objective_id=cascade.child_objective_id,
            child_node_id=cascade.child_node_id,
            contribution_weight=cascade.contribution_weight,
            alignment_status=cascade.alignment_status,
            created_at=cascade.created_at,
        )
        self.session.add(model)
        await self.session.commit()
        return cascade

    async def list_cascades_for_objective(self, objective_id: str) -> List[ObjectiveCascade]:
        stmt = select(ObjectiveCascadeModel).where(ObjectiveCascadeModel.parent_objective_id == objective_id)
        res = await self.session.execute(stmt)
        models = res.scalars().all()
        return [
            ObjectiveCascade(
                id=m.id,
                parent_objective_id=m.parent_objective_id,
                child_objective_id=m.child_objective_id,
                child_node_id=m.child_node_id,
                contribution_weight=m.contribution_weight,
                alignment_status=m.alignment_status,
                created_at=m.created_at,
            )
            for m in models
        ]

    # 7. Policy Profiles & Authority Grants
    async def save_policy_profile(self, profile: EnterprisePolicyProfile) -> EnterprisePolicyProfile:
        stmt = select(EnterprisePolicyProfileModel).where(EnterprisePolicyProfileModel.node_id == profile.node_id)
        res = await self.session.execute(stmt)
        model = res.scalar_one_or_none()

        if not model:
            model = EnterprisePolicyProfileModel(
                id=profile.id,
                enterprise_id=profile.enterprise_id,
                node_id=profile.node_id,
                mandatory_security_level=profile.mandatory_security_level,
                max_single_budget_spend_usd=profile.max_single_budget_spend_usd,
                prohibited_external_actions_json=json.dumps(profile.prohibited_external_actions),
                require_human_governance=profile.require_human_governance,
                metadata_json=json.dumps(profile.metadata),
                created_at=profile.created_at,
            )
            self.session.add(model)
        else:
            model.mandatory_security_level = profile.mandatory_security_level
            model.max_single_budget_spend_usd = profile.max_single_budget_spend_usd
            model.prohibited_external_actions_json = json.dumps(profile.prohibited_external_actions)
            model.require_human_governance = profile.require_human_governance
            model.metadata_json = json.dumps(profile.metadata)

        await self.session.commit()
        return profile

    async def get_policy_profile_by_node_id(self, node_id: str) -> Optional[EnterprisePolicyProfile]:
        stmt = select(EnterprisePolicyProfileModel).where(EnterprisePolicyProfileModel.node_id == node_id)
        res = await self.session.execute(stmt)
        model = res.scalar_one_or_none()
        if not model:
            return None

        return EnterprisePolicyProfile(
            id=model.id,
            enterprise_id=model.enterprise_id,
            node_id=model.node_id,
            mandatory_security_level=model.mandatory_security_level,
            max_single_budget_spend_usd=model.max_single_budget_spend_usd,
            prohibited_external_actions=json.loads(model.prohibited_external_actions_json or "[]"),
            require_human_governance=model.require_human_governance,
            metadata=json.loads(model.metadata_json or "{}"),
            created_at=model.created_at,
        )

    async def save_authority_grant(self, grant: AuthorityGrant) -> AuthorityGrant:
        model = AuthorityGrantModel(
            id=grant.id,
            enterprise_id=grant.enterprise_id,
            grantor_node_id=grant.grantor_node_id,
            grantee_node_id=grant.grantee_node_id,
            scope=grant.scope,
            action=grant.action,
            max_impact_usd=grant.max_impact_usd,
            expires_at=grant.expires_at,
            is_revoked=grant.is_revoked,
            created_at=grant.created_at,
        )
        self.session.add(model)
        await self.session.commit()
        return grant

    async def list_authority_grants_for_enterprise(self, enterprise_id: str) -> List[AuthorityGrant]:
        stmt = select(AuthorityGrantModel).where(AuthorityGrantModel.enterprise_id == enterprise_id)
        res = await self.session.execute(stmt)
        models = res.scalars().all()
        return [
            AuthorityGrant(
                id=m.id,
                enterprise_id=m.enterprise_id,
                grantor_node_id=m.grantor_node_id,
                grantee_node_id=m.grantee_node_id,
                scope=m.scope,
                action=m.action,
                max_impact_usd=m.max_impact_usd,
                expires_at=m.expires_at,
                is_revoked=m.is_revoked,
                created_at=m.created_at,
            )
            for m in models
        ]

    # 8. Resource Pools & Allocations
    async def save_resource_pool(self, pool: EnterpriseResourcePool) -> EnterpriseResourcePool:
        stmt = select(EnterpriseResourcePoolModel).where(EnterpriseResourcePoolModel.id == pool.id)
        res = await self.session.execute(stmt)
        model = res.scalar_one_or_none()

        if not model:
            model = EnterpriseResourcePoolModel(
                id=pool.id,
                enterprise_id=pool.enterprise_id,
                name=pool.name,
                resource_type=pool.resource_type,
                total_capacity=pool.total_capacity,
                available_capacity=pool.available_capacity,
                unit=pool.unit,
                created_at=pool.created_at,
            )
            self.session.add(model)
        else:
            model.name = pool.name
            model.total_capacity = pool.total_capacity
            model.available_capacity = pool.available_capacity
            model.unit = pool.unit

        await self.session.commit()
        return pool

    async def get_resource_pool_by_id(self, pool_id: str) -> Optional[EnterpriseResourcePool]:
        stmt = select(EnterpriseResourcePoolModel).where(EnterpriseResourcePoolModel.id == pool_id)
        res = await self.session.execute(stmt)
        model = res.scalar_one_or_none()
        if not model:
            return None

        return EnterpriseResourcePool(
            id=model.id,
            enterprise_id=model.enterprise_id,
            name=model.name,
            resource_type=model.resource_type,
            total_capacity=model.total_capacity,
            available_capacity=model.available_capacity,
            unit=model.unit,
            created_at=model.created_at,
        )

    async def list_resource_pools_for_enterprise(self, enterprise_id: str) -> List[EnterpriseResourcePool]:
        stmt = select(EnterpriseResourcePoolModel).where(EnterpriseResourcePoolModel.enterprise_id == enterprise_id)
        res = await self.session.execute(stmt)
        models = res.scalars().all()
        return [
            EnterpriseResourcePool(
                id=m.id,
                enterprise_id=m.enterprise_id,
                name=m.name,
                resource_type=m.resource_type,
                total_capacity=m.total_capacity,
                available_capacity=m.available_capacity,
                unit=m.unit,
                created_at=m.created_at,
            )
            for m in models
        ]

    async def save_resource_allocation(self, allocation: ResourceAllocation) -> ResourceAllocation:
        model = ResourceAllocationModel(
            id=allocation.id,
            pool_id=allocation.pool_id,
            consumer_node_id=allocation.consumer_node_id,
            allocated_amount=allocation.allocated_amount,
            status=allocation.status,
            created_at=allocation.created_at,
        )
        self.session.add(model)
        await self.session.commit()
        return allocation

    # 9. InterCompany Requests
    async def save_intercompany_request(self, request: InterCompanyRequest) -> InterCompanyRequest:
        stmt = select(InterCompanyRequestModel).where(InterCompanyRequestModel.id == request.id)
        res = await self.session.execute(stmt)
        model = res.scalar_one_or_none()

        if not model:
            model = InterCompanyRequestModel(
                id=request.id,
                enterprise_id=request.enterprise_id,
                source_company_id=request.source_company_id,
                destination_company_id=request.destination_company_id,
                requester_id=request.requester_id,
                requested_capability=request.requested_capability,
                purpose=request.purpose,
                status=request.status.value if hasattr(request.status, "value") else str(request.status),
                governance_approval_id=request.governance_approval_id,
                result_data_json=json.dumps(request.result_data) if request.result_data else None,
                created_at=request.created_at,
            )
            self.session.add(model)
        else:
            model.status = request.status.value if hasattr(request.status, "value") else str(request.status)
            model.governance_approval_id = request.governance_approval_id
            model.result_data_json = json.dumps(request.result_data) if request.result_data else None

        await self.session.commit()
        return request

    async def get_intercompany_request_by_id(self, request_id: str) -> Optional[InterCompanyRequest]:
        stmt = select(InterCompanyRequestModel).where(InterCompanyRequestModel.id == request_id)
        res = await self.session.execute(stmt)
        model = res.scalar_one_or_none()
        if not model:
            return None

        return InterCompanyRequest(
            id=model.id,
            enterprise_id=model.enterprise_id,
            source_company_id=model.source_company_id,
            destination_company_id=model.destination_company_id,
            requester_id=model.requester_id,
            requested_capability=model.requested_capability,
            purpose=model.purpose,
            status=InterCompanyRequestStatus(model.status),
            governance_approval_id=model.governance_approval_id,
            result_data=json.loads(model.result_data_json) if model.result_data_json else None,
            created_at=model.created_at,
        )

    async def list_intercompany_requests_for_enterprise(self, enterprise_id: str) -> List[InterCompanyRequest]:
        stmt = select(InterCompanyRequestModel).where(InterCompanyRequestModel.enterprise_id == enterprise_id)
        res = await self.session.execute(stmt)
        models = res.scalars().all()
        return [
            InterCompanyRequest(
                id=m.id,
                enterprise_id=m.enterprise_id,
                source_company_id=m.source_company_id,
                destination_company_id=m.destination_company_id,
                requester_id=m.requester_id,
                requested_capability=m.requested_capability,
                purpose=m.purpose,
                status=InterCompanyRequestStatus(m.status),
                governance_approval_id=m.governance_approval_id,
                result_data=json.loads(m.result_data_json) if m.result_data_json else None,
                created_at=m.created_at,
            )
            for m in models
        ]

    # 10. Risks & Opportunities
    async def save_risk(self, risk: EnterpriseRisk) -> EnterpriseRisk:
        model = EnterpriseRiskModel(
            id=risk.id,
            enterprise_id=risk.enterprise_id,
            title=risk.title,
            description=risk.description,
            impact_usd=risk.impact_usd,
            probability=risk.probability,
            owner_node_id=risk.owner_node_id,
            status=risk.status,
            created_at=risk.created_at,
        )
        self.session.add(model)
        await self.session.commit()
        return risk

    async def list_risks_for_enterprise(self, enterprise_id: str) -> List[EnterpriseRisk]:
        stmt = select(EnterpriseRiskModel).where(EnterpriseRiskModel.enterprise_id == enterprise_id)
        res = await self.session.execute(stmt)
        models = res.scalars().all()
        return [
            EnterpriseRisk(
                id=m.id,
                enterprise_id=m.enterprise_id,
                title=m.title,
                description=m.description,
                impact_usd=m.impact_usd,
                probability=m.probability,
                owner_node_id=m.owner_node_id,
                status=m.status,
                created_at=m.created_at,
            )
            for m in models
        ]

    async def save_opportunity(self, opportunity: EnterpriseOpportunity) -> EnterpriseOpportunity:
        model = EnterpriseOpportunityModel(
            id=opportunity.id,
            enterprise_id=opportunity.enterprise_id,
            title=opportunity.title,
            description=opportunity.description,
            potential_value_usd=opportunity.potential_value_usd,
            confidence=opportunity.confidence,
            status=opportunity.status,
            created_at=opportunity.created_at,
        )
        self.session.add(model)
        await self.session.commit()
        return opportunity

    async def list_opportunities_for_enterprise(self, enterprise_id: str) -> List[EnterpriseOpportunity]:
        stmt = select(EnterpriseOpportunityModel).where(EnterpriseOpportunityModel.enterprise_id == enterprise_id)
        res = await self.session.execute(stmt)
        models = res.scalars().all()
        return [
            EnterpriseOpportunity(
                id=m.id,
                enterprise_id=m.enterprise_id,
                title=m.title,
                description=m.description,
                potential_value_usd=m.potential_value_usd,
                confidence=m.confidence,
                status=m.status,
                created_at=m.created_at,
            )
            for m in models
        ]

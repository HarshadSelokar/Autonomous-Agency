"""
Application service for Company Federation, Shared Services, and Inter-Company Requests.
"""

from typing import Any, Dict, List, Optional

from src.domain.enterprise import (
    EnterpriseOrganizationNode,
    NodeType,
    EnterpriseService,
    ServiceType,
    EnterpriseServiceAgreement,
    InterCompanyRequest,
    InterCompanyRequestStatus,
)
from src.domain.exceptions import UnauthorizedEnterpriseActionError
from src.domain.repository import EnterpriseRepositoryInterface


class EnterpriseFederationService:

    def __init__(self, repository: EnterpriseRepositoryInterface) -> None:
        self.repo = repository

    async def attach_company_to_enterprise(
        self,
        enterprise_id: str,
        company_id: str,
        company_name: str,
        region: str = "GLOBAL",
        parent_node_id: Optional[str] = None,
    ) -> EnterpriseOrganizationNode:

        node = EnterpriseOrganizationNode(
            enterprise_id=enterprise_id,
            name=company_name,
            node_type=NodeType.COMPANY,
            reference_id=company_id,
            parent_node_id=parent_node_id,
            region=region,
        )
        return await self.repo.save_topology_node(node)

    async def register_shared_service(
        self,
        enterprise_id: str,
        owner_node_id: str,
        name: str,
        service_type: ServiceType,
        capacity_units: int = 100,
        sla_description: str = "Standard 99.9% Availability",
        governance_required: bool = True,
    ) -> EnterpriseService:

        service = EnterpriseService(
            enterprise_id=enterprise_id,
            owner_node_id=owner_node_id,
            name=name,
            service_type=service_type,
            capacity_units=capacity_units,
            available_units=capacity_units,
            sla_description=sla_description,
            governance_required=governance_required,
        )
        return await self.repo.save_service(service)

    async def create_service_agreement(
        self,
        service_id: str,
        consumer_node_id: str,
        allocated_units: int = 10,
        cost_allocation_usd: float = 0.0,
    ) -> EnterpriseServiceAgreement:

        service = await self.repo.get_service_by_id(service_id)
        if not service:
            raise ValueError(f"Enterprise service '{service_id}' not found.")

        if service.available_units < allocated_units:
            raise ValueError(f"Insufficient capacity in service '{service_id}': requested {allocated_units}, available {service.available_units}")

        service.available_units -= allocated_units
        await self.repo.save_service(service)

        agreement = EnterpriseServiceAgreement(
            service_id=service_id,
            consumer_node_id=consumer_node_id,
            allocated_units=allocated_units,
            cost_allocation_usd=cost_allocation_usd,
            status="ACTIVE",
        )
        return await self.repo.save_service_agreement(agreement)

    async def submit_intercompany_request(
        self,
        enterprise_id: str,
        source_company_id: str,
        destination_company_id: str,
        requester_id: str,
        requested_capability: str,
        purpose: str,
    ) -> InterCompanyRequest:

        req = InterCompanyRequest(
            enterprise_id=enterprise_id,
            source_company_id=source_company_id,
            destination_company_id=destination_company_id,
            requester_id=requester_id,
            requested_capability=requested_capability,
            purpose=purpose,
            status=InterCompanyRequestStatus.PENDING,
        )
        return await self.repo.save_intercompany_request(req)

    async def authorize_intercompany_request(
        self,
        request_id: str,
        enterprise_id: str,
        governance_approval_id: str,
    ) -> InterCompanyRequest:

        req = await self.repo.get_intercompany_request_by_id(request_id)
        if not req:
            raise ValueError(f"Inter-company request '{request_id}' not found.")

        if req.enterprise_id != enterprise_id:
            raise UnauthorizedEnterpriseActionError(enterprise_id, "AUTHORIZE_REQUEST", "Enterprise context mismatch.")

        req.status = InterCompanyRequestStatus.AUTHORIZED
        req.governance_approval_id = governance_approval_id
        return await self.repo.save_intercompany_request(req)

    async def execute_intercompany_request(
        self,
        request_id: str,
        enterprise_id: str,
        execution_result: Dict[str, Any],
    ) -> InterCompanyRequest:

        req = await self.repo.get_intercompany_request_by_id(request_id)
        if not req:
            raise ValueError(f"Inter-company request '{request_id}' not found.")

        if req.status != InterCompanyRequestStatus.AUTHORIZED:
            raise UnauthorizedEnterpriseActionError(
                enterprise_id, "EXECUTE_REQUEST", f"Request '{request_id}' must be AUTHORIZED prior to execution. Current status: {req.status}"
            )

        req.status = InterCompanyRequestStatus.COMPLETED
        req.result_data = execution_result
        return await self.repo.save_intercompany_request(req)

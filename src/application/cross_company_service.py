"""
Cross-Company Governance & Relationship Application Service for Phase 25.

Provides a dedicated governed boundary for explicit company-to-company relationships and data sharing.
Cross-company access is strictly denied by default.
"""

from datetime import UTC, datetime
from typing import Any, List, Optional
import uuid

from src.domain.company import (
    CompanyRelationship,
    CompanyDataShareRequest,
    RelationshipType,
    DataShareScope,
    DataShareStatus,
)
from src.domain.events import (
    CompanyRelationshipCreatedEvent,
    CompanyDataShareRequestedEvent,
    CompanyDataShareApprovedEvent,
)
from src.domain.exceptions import CrossCompanyAccessDeniedError
from src.domain.repository import MultiCompanyRepositoryInterface


class CrossCompanyService:
    """Manages governed cross-company relationships, data share requests, and isolation checks."""

    def __init__(self, repository: MultiCompanyRepositoryInterface, outbox_publisher: Optional[Any] = None) -> None:
        self.repository = repository
        self.outbox_publisher = outbox_publisher

    def _publish_event(self, event: Any) -> None:
        if self.outbox_publisher and hasattr(self.outbox_publisher, "publish"):
            self.outbox_publisher.publish(event)

    async def create_relationship(
        self,
        company_a_id: str,
        company_b_id: str,
        relationship_type: RelationshipType = RelationshipType.PARTNER,
    ) -> CompanyRelationship:
        if company_a_id == company_b_id:
            raise ValueError("Cannot establish a company relationship with oneself.")

        rel = CompanyRelationship(
            id=str(uuid.uuid4()),
            company_a_id=company_a_id,
            company_b_id=company_b_id,
            relationship_type=relationship_type,
            status="ACTIVE",
            created_at=datetime.now(UTC),
        )
        saved = await self.repository.save_relationship(rel)
        self._publish_event(
            CompanyRelationshipCreatedEvent(
                relationship_id=saved.id,
                company_a_id=company_a_id,
                company_b_id=company_b_id,
                relationship_type=relationship_type.value,
            )
        )
        return saved

    async def request_data_share(
        self,
        source_company_id: str,
        target_company_id: str,
        purpose: str,
        data_scope: DataShareScope = DataShareScope.READ_ONLY,
    ) -> CompanyDataShareRequest:
        # Verify active relationship exists
        relationships = await self.repository.list_relationships_for_company(source_company_id)
        has_rel = any(
            (r.company_a_id == target_company_id or r.company_b_id == target_company_id) and r.status == "ACTIVE"
            for r in relationships
        )
        if not has_rel:
            raise CrossCompanyAccessDeniedError(source_company_id, target_company_id, "No active company relationship exists.")

        req = CompanyDataShareRequest(
            id=str(uuid.uuid4()),
            source_company_id=source_company_id,
            target_company_id=target_company_id,
            data_scope=data_scope,
            purpose=purpose,
            status=DataShareStatus.REQUESTED,
            created_at=datetime.now(UTC),
        )
        saved = await self.repository.save_data_share_request(req)
        self._publish_event(
            CompanyDataShareRequestedEvent(
                share_request_id=saved.id,
                source_company_id=source_company_id,
                target_company_id=target_company_id,
                data_scope=data_scope.value,
            )
        )
        return saved

    async def approve_data_share(
        self,
        request_id: str,
        actor_id: str,
        governance_approval_id: str,
    ) -> CompanyDataShareRequest:
        req = await self.repository.get_data_share_request_by_id(request_id)
        if not req:
            raise ValueError(f"Data share request '{request_id}' not found.")

        if not governance_approval_id:
            raise CrossCompanyAccessDeniedError(req.source_company_id, req.target_company_id, "Data share approval requires explicit governance approval ID.")

        req.status = DataShareStatus.APPROVED
        req.governance_approval_id = governance_approval_id
        saved = await self.repository.save_data_share_request(req)

        self._publish_event(
            CompanyDataShareApprovedEvent(
                share_request_id=saved.id,
                approved_by=actor_id,
                governance_approval_id=governance_approval_id,
            )
        )
        return saved

    async def verify_cross_company_access(self, source_company_id: str, target_company_id: str) -> None:
        """Enforces governed cross-company data access permission."""
        if source_company_id == target_company_id:
            return  # Intra-company access allowed

        requests = await self.repository.list_data_share_requests_for_company(source_company_id)
        approved_req = next(
            (r for r in requests if r.target_company_id == target_company_id and r.status == DataShareStatus.APPROVED),
            None,
        )

        if not approved_req:
            raise CrossCompanyAccessDeniedError(source_company_id, target_company_id, "No approved data-share request found.")

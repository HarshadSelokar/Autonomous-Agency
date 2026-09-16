"""
Product Management Service for Phase 24.

Orchestrates products, versions, roadmaps, customer feedback ingestion,
insight validation, and requirement generation linked to the Task Engine.
"""

from datetime import UTC, datetime
from typing import Any, Dict, List, Optional
import uuid

from src.domain.gtm import (
    Product,
    ProductVersion,
    ProductRoadmap,
    ProductRequirement,
    ProductFeedback,
    ProductLifecycle,
    FeedbackCategory,
)
from src.domain.events import (
    FeedbackReceivedEvent,
    ProductRequirementCreatedEvent,
)
from src.domain.repository import GTMRepositoryInterface


class ProductManagementService:
    """Manages product roadmaps, feedback loops, and requirements."""

    def __init__(self, repository: GTMRepositoryInterface, outbox_publisher: Optional[Any] = None) -> None:
        self.repository = repository
        self.outbox_publisher = outbox_publisher

    def _publish_event(self, event: Any) -> None:
        if self.outbox_publisher and hasattr(self.outbox_publisher, "publish"):
            self.outbox_publisher.publish(event)

    async def create_product(
        self,
        name: str,
        code: str,
        description: str,
        owner_employee_id: str,
        base_price_cents: int = 0,
        currency: str = "USD",
        category: str = "SOFTWARE",
    ) -> Product:
        prod = Product(
            id=str(uuid.uuid4()),
            name=name,
            code=code,
            description=description,
            owner_employee_id=owner_employee_id,
            base_price_cents=base_price_cents,
            currency=currency,
            category=category,
            lifecycle=ProductLifecycle.ACTIVE,
            created_at=datetime.now(UTC),
        )
        return await self.repository.save_product(prod)

    async def record_customer_feedback(
        self,
        product_id: str,
        customer_id: str,
        summary: str,
        raw_content: str,
        category: FeedbackCategory = FeedbackCategory.FEATURE_REQUEST,
        importance_score: int = 5,
    ) -> ProductFeedback:
        fb = ProductFeedback(
            id=str(uuid.uuid4()),
            product_id=product_id,
            customer_id=customer_id,
            category=category,
            summary=summary,
            raw_content=raw_content,
            importance_score=importance_score,
            status="RECEIVED",
            created_at=datetime.now(UTC),
        )
        saved = await self.repository.save_product_feedback(fb)
        self._publish_event(
            FeedbackReceivedEvent(
                feedback_id=saved.id,
                customer_id=saved.customer_id,
                product_id=saved.product_id,
                category=saved.category.value,
            )
        )
        return saved

    async def synthesize_feedback_to_requirement(
        self,
        feedback_id: str,
        requirement_title: str,
        user_story: str,
        priority: str = "MEDIUM",
        assigned_task_id: Optional[str] = None,
    ) -> ProductRequirement:
        fb_list = await self.repository.list_product_feedback("DEFAULT") # Search broad or by feedback_id
        target_fb = next((f for f in fb_list if f.id == feedback_id), None)
        
        product_id = target_fb.product_id if target_fb else "DEFAULT_PROD"

        if target_fb:
            target_fb.validated_insight = f"Synthesized into requirement: '{requirement_title}'"
            target_fb.status = "PROCESSED"
            await self.repository.save_product_feedback(target_fb)

        req = ProductRequirement(
            id=str(uuid.uuid4()),
            product_id=product_id,
            title=requirement_title,
            user_story=user_story,
            priority=priority,
            source_feedback_id=feedback_id,
            task_id=assigned_task_id,
            status="APPROVED_FOR_DEV" if assigned_task_id else "PROPOSED",
            created_at=datetime.now(UTC),
        )
        saved = await self.repository.save_product_requirement(req)

        self._publish_event(
            ProductRequirementCreatedEvent(
                requirement_id=saved.id,
                product_id=saved.product_id,
                title=saved.title,
                source_feedback_id=saved.source_feedback_id,
            )
        )
        return saved

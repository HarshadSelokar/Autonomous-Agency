"""
SQLAlchemy ORM Models for Phase 12 Model Routing entities.
"""

from datetime import UTC, datetime
from typing import Any, Optional
from sqlalchemy import JSON, Boolean, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.database import Base


class ModelProfileModel(Base):
    __tablename__ = "model_profiles"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    provider_name: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    model_name: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    capabilities: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=list)
    context_window_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=128000)
    cost_per_1k_input_tokens: Mapped[float] = mapped_column(Float, nullable=False, default=0.001)
    cost_per_1k_output_tokens: Mapped[float] = mapped_column(Float, nullable=False, default=0.002)
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=200)
    quality_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.90)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)
    is_approved_for_production: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))


class ModelSelectionDecisionModel(Base):
    __tablename__ = "model_selection_decisions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    request_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    task_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    selected_model_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    selected_provider_name: Mapped[str] = mapped_column(String(64), nullable=False)
    strategy_used: Mapped[str] = mapped_column(String(64), nullable=False)
    candidate_model_ids: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=list)
    rejected_candidates: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    score_breakdown: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    is_fallback: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    rationale: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))


class ModelProviderHealthModel(Base):
    __tablename__ = "model_provider_health"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    provider_name: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    model_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    is_healthy: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)
    error_rate: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    latency_p95_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=250)
    rate_limit_reset_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_failure_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))

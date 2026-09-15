"""
Model Routing Domain Entities and Value Objects for Phase 12.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid


class ModelCapability(str, Enum):
    TEXT_GENERATION = "TEXT_GENERATION"
    STRUCTURED_OUTPUT = "STRUCTURED_OUTPUT"
    TOOL_CALLING = "TOOL_CALLING"
    CODE_GENERATION = "CODE_GENERATION"
    CODE_REVIEW = "CODE_REVIEW"
    LONG_CONTEXT = "LONG_CONTEXT"
    REASONING = "REASONING"
    VISION = "VISION"
    FAST_RESPONSE = "FAST_RESPONSE"
    LOW_COST = "LOW_COST"
    HIGH_RELIABILITY = "HIGH_RELIABILITY"


class RoutingStrategy(str, Enum):
    RULE_BASED = "RULE_BASED"
    CAPABILITY_BASED = "CAPABILITY_BASED"
    COST_AWARE = "COST_AWARE"
    LATENCY_AWARE = "LATENCY_AWARE"
    QUALITY_AWARE = "QUALITY_AWARE"
    HEALTH_AWARE = "HEALTH_AWARE"


@dataclass
class ModelProfile:
    """Represents a registered LLM model's capabilities and operational profile."""
    model_id: str
    provider_name: str                      # e.g., "groq", "fake", "openai"
    model_name: str                         # e.g., "llama-3.3-70b-versatile"
    capabilities: List[ModelCapability] = field(default_factory=list)
    context_window_tokens: int = 128000
    cost_per_1k_input_tokens: float = 0.001
    cost_per_1k_output_tokens: float = 0.002
    latency_ms: int = 200
    quality_score: float = 0.90             # 0.0 to 1.0
    is_active: bool = True
    is_approved_for_production: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def has_capability(self, cap: ModelCapability) -> bool:
        return cap in self.capabilities


@dataclass
class ModelSelectionRequest:
    """Structured request sent to ModelRouter to choose the best model."""
    request_id: str
    task_id: Optional[str] = None
    agent_id: Optional[str] = None
    employee_id: Optional[str] = None
    required_capabilities: List[ModelCapability] = field(default_factory=list)
    strategy: RoutingStrategy = RoutingStrategy.CAPABILITY_BASED
    max_budget_per_run: Optional[float] = None
    max_latency_ms: Optional[int] = None
    min_quality_score: float = 0.70
    governance_risk_level: str = "LOW"
    allowlist_models: Optional[List[str]] = None
    blocklist_models: Optional[List[str]] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class ModelSelectionDecision:
    """Explainable decision recorded by ModelRouter."""
    decision_id: str
    request_id: str
    task_id: Optional[str]
    selected_model_id: str
    selected_provider_name: str
    strategy_used: RoutingStrategy
    candidate_model_ids: List[str] = field(default_factory=list)
    rejected_candidates: Dict[str, str] = field(default_factory=dict) # model_id -> reason
    score_breakdown: Dict[str, float] = field(default_factory=dict)   # model_id -> score
    is_fallback: bool = False
    rationale: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class ModelProviderHealth:
    """Tracks operational health signals for a model provider."""
    provider_name: str
    model_id: str
    is_healthy: bool = True
    error_rate: float = 0.0
    latency_p95_ms: int = 250
    rate_limit_reset_at: Optional[datetime] = None
    last_failure_reason: Optional[str] = None
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

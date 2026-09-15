"""
Pydantic Schemas for Phase 12 Model Routing REST APIs.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ModelProfileCreateSchema(BaseModel):
    model_id: str
    provider_name: str
    model_name: str
    capabilities: List[str] = Field(default_factory=list)
    context_window_tokens: int = 128000
    cost_per_1k_input_tokens: float = 0.001
    cost_per_1k_output_tokens: float = 0.002
    latency_ms: int = 200
    quality_score: float = 0.90
    is_active: bool = True
    is_approved_for_production: bool = True


class ModelRouteRequestSchema(BaseModel):
    task_id: Optional[str] = None
    agent_id: Optional[str] = None
    required_capabilities: List[str] = Field(default_factory=list)
    strategy: str = "CAPABILITY_BASED"
    max_budget_per_run: Optional[float] = None
    max_latency_ms: Optional[int] = None
    min_quality_score: float = 0.70
    governance_risk_level: str = "LOW"
    allowlist_models: Optional[List[str]] = None
    blocklist_models: Optional[List[str]] = None


class ModelSelectionDecisionResponseSchema(BaseModel):
    decision_id: str
    request_id: str
    task_id: Optional[str] = None
    selected_model_id: str
    selected_provider_name: str
    strategy_used: str
    candidate_model_ids: List[str] = Field(default_factory=list)
    rejected_candidates: Dict[str, str] = Field(default_factory=dict)
    score_breakdown: Dict[str, float] = Field(default_factory=dict)
    is_fallback: bool
    rationale: str
    created_at: str


class ModelProviderHealthUpdateSchema(BaseModel):
    provider_name: str
    model_id: str
    is_healthy: bool = True
    error_rate: float = 0.0
    latency_p95_ms: int = 250
    last_failure_reason: Optional[str] = None

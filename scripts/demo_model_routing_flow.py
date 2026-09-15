"""
Phase 12 — Model Routing & Intelligent Model Selection End-to-End Demonstration Script.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import src.infrastructure.models  # noqa: F401
from src.application.model_router import ModelRouter
from src.domain.model_routing import (
    ModelCapability,
    ModelSelectionRequest,
    RoutingStrategy,
)
from src.infrastructure.database import Base
from src.infrastructure.repositories.model_routing_repository import ModelRoutingRepository


def run_demo():
    print("================================================================================")
    print("PHASE 12 — MODEL ROUTING & INTELLIGENT MODEL SELECTION DEMONSTRATION")
    print("================================================================ launch\n")

    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    repo = ModelRoutingRepository(session)
    router = ModelRouter(repository=repo)

    # --------------------------------------------------------------------------
    # SCENARIO 1: Registering Multi-Provider LLM Operational Profiles
    # --------------------------------------------------------------------------
    print("--- SCENARIO 1: Registering Multi-Provider LLM Operational Profiles ---")

    m1 = router.register_model_profile(
        model_id="llama-3.3-70b-versatile",
        provider_name="Groq",
        model_name="Llama 3.3 70B",
        capabilities=[ModelCapability.TEXT_GENERATION, ModelCapability.CODE_GENERATION, ModelCapability.REASONING],
        context_window_tokens=128000,
        cost_per_1k_input_tokens=0.00059,
        cost_per_1k_output_tokens=0.00079,
        latency_ms=250,
        quality_score=0.92,
    )
    print(f"[+] Registered Model '{m1.model_id}' (Provider: {m1.provider_name}, Quality: {m1.quality_score})")

    m2 = router.register_model_profile(
        model_id="llama-3.1-8b-instant",
        provider_name="Groq",
        model_name="Llama 3.1 8B Instant",
        capabilities=[ModelCapability.TEXT_GENERATION, ModelCapability.FAST_RESPONSE, ModelCapability.LOW_COST],
        context_window_tokens=128000,
        cost_per_1k_input_tokens=0.00005,
        cost_per_1k_output_tokens=0.00008,
        latency_ms=80,
        quality_score=0.75,
    )
    print(f"[+] Registered Model '{m2.model_id}' (Provider: {m2.provider_name}, Quality: {m2.quality_score})")

    m3 = router.register_model_profile(
        model_id="gpt-4o-fake-backup",
        provider_name="Fake",
        model_name="Fake GPT-4o Backup",
        capabilities=[ModelCapability.TEXT_GENERATION, ModelCapability.CODE_GENERATION, ModelCapability.REASONING, ModelCapability.VISION],
        context_window_tokens=128000,
        cost_per_1k_input_tokens=0.0025,
        cost_per_1k_output_tokens=0.0050,
        latency_ms=450,
        quality_score=0.96,
    )
    print(f"[+] Registered Model '{m3.model_id}' (Provider: {m3.provider_name}, Quality: {m3.quality_score})\n")

    # --------------------------------------------------------------------------
    # SCENARIO 2: Strategy-Based Intelligent Model Routing
    # --------------------------------------------------------------------------
    print("--- SCENARIO 2: Strategy-Based Intelligent Model Selection ---")

    # 1. Quality-Aware Routing for Code Review
    req_quality = ModelSelectionRequest(
        request_id="req-code-review-1",
        task_id="task-review-core-auth",
        required_capabilities=[ModelCapability.CODE_GENERATION, ModelCapability.REASONING],
        strategy=RoutingStrategy.QUALITY_AWARE,
    )
    decision_q = router.route_model(req_quality)
    print(f"[+] QUALITY_AWARE Strategy -> Selected Model: '{decision_q.selected_model_id}' (Provider: {decision_q.selected_provider_name})")
    print(f"    Rationale: {decision_q.rationale}")

    # 2. Cost-Aware Routing for High Volume Summarization
    req_cost = ModelSelectionRequest(
        request_id="req-summary-100",
        task_id="task-summarize-logs",
        required_capabilities=[ModelCapability.TEXT_GENERATION],
        strategy=RoutingStrategy.COST_AWARE,
    )
    decision_c = router.route_model(req_cost)
    print(f"[+] COST_AWARE Strategy -> Selected Model: '{decision_c.selected_model_id}' (Provider: {decision_c.selected_provider_name})")
    print(f"    Rationale: {decision_c.rationale}\n")

    # --------------------------------------------------------------------------
    # SCENARIO 3: Health Monitoring & Automatic Provider Outage Fallback
    # --------------------------------------------------------------------------
    print("--- SCENARIO 3: Provider Health Monitoring & Automatic Outage Fallback ---")
    print("[!] Simulating Provider Health Outage for 'llama-3.3-70b-versatile' on Groq...")
    router.update_provider_health(
        provider_name="Groq",
        model_id="llama-3.3-70b-versatile",
        is_healthy=False,
        error_rate=0.99,
        last_failure_reason="503 Service Unavailable / Rate Limit Exceeded",
    )

    req_fallback = ModelSelectionRequest(
        request_id="req-code-gen-fallback",
        task_id="task-implement-payment-gateway",
        required_capabilities=[ModelCapability.CODE_GENERATION, ModelCapability.REASONING],
        strategy=RoutingStrategy.QUALITY_AWARE,
    )
    decision_fb = router.route_model(req_fallback)
    print(f"[+] Model Selection During Outage -> Selected Model: '{decision_fb.selected_model_id}' (Provider: {decision_fb.selected_provider_name})")
    print(f"    Rejected Unhealthy Candidates: {decision_fb.rejected_candidates}")
    assert decision_fb.selected_model_id == "gpt-4o-fake-backup"
    print("[SUCCESS] Model Router automatically avoided unhealthy provider and routed request to healthy backup model!\n")

    print("================================================================================")
    print("ALL PHASE 12 MODEL ROUTING DEMONSTRATIONS COMPLETED SUCCESSFULLY!")
    print("================================================================================\n")


if __name__ == "__main__":
    run_demo()

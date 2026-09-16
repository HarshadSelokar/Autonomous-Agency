"""
Swarm Planner for Phase 22.
Generates deterministic swarm execution plans based on parent task requirements,
dependency graph, workforce capabilities, available agents, and governance budgets.
"""

from dataclasses import dataclass, field
from typing import Any
import uuid

from src.domain.exceptions import SwarmDepthExceededError, SwarmValidationError
from src.domain.swarm import CoordinationMode, Swarm, SwarmBudget, SwarmMember, SwarmMemberStatus, SwarmStatus


@dataclass
class SwarmMemberRequirement:
    role: str
    capability: str
    assigned_subtask_title: str
    required_model_capability: str = "general"


@dataclass
class SwarmExecutionPlan:
    swarm_id: str
    parent_task_id: str
    coordination_mode: CoordinationMode
    member_requirements: list[SwarmMemberRequirement] = field(default_factory=list)
    budget: SwarmBudget = field(default_factory=lambda: SwarmBudget(swarm_id=""))
    depth: int = 1
    max_concurrency: int = 5


class SwarmPlanner:
    def __init__(self, max_allowed_depth: int = 2) -> None:
        self.max_allowed_depth = max_allowed_depth

    def plan_swarm(
        self,
        parent_task_id: str,
        task_title: str,
        task_description: str,
        required_capabilities: list[str],
        depth: int = 1,
        requested_mode: CoordinationMode | None = None,
        custom_budget: dict[str, Any] | None = None,
    ) -> SwarmExecutionPlan:
        if depth > self.max_allowed_depth:
            raise SwarmDepthExceededError(
                f"Requested swarm depth {depth} exceeds maximum permitted depth {self.max_allowed_depth}."
            )

        # Determine coordination mode
        mode = requested_mode or self._infer_coordination_mode(task_title, task_description, required_capabilities)

        # Generate member requirements based on mode & capabilities
        requirements = self._build_member_requirements(mode, task_title, required_capabilities)

        # Construct resource budget
        swarm_id = f"sw_{uuid.uuid4().hex[:12]}"
        budget = SwarmBudget(swarm_id=swarm_id)
        if custom_budget:
            budget.max_execution_time_seconds = custom_budget.get("max_execution_time_seconds", budget.max_execution_time_seconds)
            budget.max_model_cost = custom_budget.get("max_model_cost", budget.max_model_cost)
            budget.max_tool_calls = custom_budget.get("max_tool_calls", budget.max_tool_calls)
            budget.max_tokens = custom_budget.get("max_tokens", budget.max_tokens)
            budget.max_retries = custom_budget.get("max_retries", budget.max_retries)

        return SwarmExecutionPlan(
            swarm_id=swarm_id,
            parent_task_id=parent_task_id,
            coordination_mode=mode,
            member_requirements=requirements,
            budget=budget,
            depth=depth,
            max_concurrency=min(len(requirements), 5) if requirements else 1,
        )

    def _infer_coordination_mode(self, title: str, description: str, capabilities: list[str]) -> CoordinationMode:
        title_desc = f"{title} {description}".lower()
        if "pipeline" in title_desc or "sequential" in title_desc:
            return CoordinationMode.PIPELINE
        elif "debate" in title_desc or "consensus" in title_desc:
            return CoordinationMode.DEBATE
        elif "map" in title_desc or "reduce" in title_desc or "batch" in title_desc:
            return CoordinationMode.MAP_REDUCE
        elif len(capabilities) > 1 or "feature" in title_desc or "investigate" in title_desc:
            return CoordinationMode.SPECIALIST
        else:
            return CoordinationMode.PARALLEL

    def _build_member_requirements(
        self, mode: CoordinationMode, title: str, capabilities: list[str]
    ) -> list[SwarmMemberRequirement]:
        reqs: list[SwarmMemberRequirement] = []
        caps = capabilities or ["general_problem_solving"]

        if mode == CoordinationMode.SPECIALIST:
            role_map = [
                ("Research Agent", "research", "Literature & requirements analysis"),
                ("Architect Agent", "architecture", "System architecture & design specification"),
                ("Backend Agent", "code_generation", "Core backend implementation"),
                ("QA Agent", "testing", "Automated test suite creation & verification"),
                ("Security Agent", "security_review", "Security boundary & permission review"),
                ("Reviewer Agent", "code_review", "Quality assurance code review"),
            ]
            for role, cap, subtask in role_map:
                reqs.append(SwarmMemberRequirement(role=role, capability=cap, assigned_subtask_title=f"{subtask} for '{title}'"))
        elif mode == CoordinationMode.PIPELINE:
            for idx, cap in enumerate(caps, 1):
                reqs.append(
                    SwarmMemberRequirement(
                        role=f"Pipeline Worker {idx}",
                        capability=cap,
                        assigned_subtask_title=f"Stage {idx} processing for '{title}'",
                    )
                )
        elif mode in (CoordinationMode.DEBATE, CoordinationMode.CONSENSUS):
            reqs.append(SwarmMemberRequirement(role="Proposer Agent", capability="reasoning", assigned_subtask_title=f"Initial proposal for '{title}'"))
            reqs.append(SwarmMemberRequirement(role="Critique Agent", capability="code_review", assigned_subtask_title=f"Critique & risk audit for '{title}'"))
            reqs.append(SwarmMemberRequirement(role="Synthesis Agent", capability="synthesis", assigned_subtask_title=f"Consensus synthesis for '{title}'"))
        else:
            # Parallel or Map-Reduce
            for idx, cap in enumerate(caps, 1):
                reqs.append(
                    SwarmMemberRequirement(
                        role=f"Parallel Specialist {idx}",
                        capability=cap,
                        assigned_subtask_title=f"Parallel subtask {idx} for '{title}'",
                    )
                )

        return reqs

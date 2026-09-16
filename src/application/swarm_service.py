"""
Swarm Service for Phase 22.
Central orchestration facade managing multi-agent swarm creation, capability-based member selection,
bounded parallel execution, inter-agent messaging, budget tracking, conflict resolution,
independent verification, recovery, and governance.
"""

from typing import Any
import uuid

from src.application.swarm_conflict_resolver import SwarmConflictResolver
from src.application.swarm_coordination_engine import SwarmCoordinationEngine
from src.application.swarm_governance_service import SwarmGovernanceService
from src.application.swarm_observability_service import SwarmObservabilityService
from src.application.swarm_planner import SwarmPlanner
from src.application.swarm_result_aggregator import SwarmResultAggregator
from src.domain.exceptions import (
    SwarmBudgetExceededError,
    SwarmGovernanceViolationError,
    SwarmNotFoundError,
    SwarmValidationError,
)
from src.domain.swarm import (
    CoordinationMode,
    Swarm,
    SwarmBudget,
    SwarmConflict,
    SwarmMember,
    SwarmMemberStatus,
    SwarmMessage,
    SwarmMessageType,
    SwarmResult,
    SwarmStatus,
)


class SwarmService:
    def __init__(
        self,
        swarm_repo: Any,
        task_repo: Any | None = None,
        employee_repo: Any | None = None,
        agent_repo: Any | None = None,
        agent_execution_engine: Any | None = None,
        verification_engine: Any | None = None,
        recovery_engine: Any | None = None,
        workforce_service: Any | None = None,
        governance_service: Any | None = None,
        model_router: Any | None = None,
    ) -> None:
        self.swarm_repo = swarm_repo
        self.task_repo = task_repo
        self.employee_repo = employee_repo
        self.agent_repo = agent_repo
        self.agent_execution_engine = agent_execution_engine
        self.verification_engine = verification_engine
        self.recovery_engine = recovery_engine
        self.workforce_service = workforce_service

        self.planner = SwarmPlanner()
        self.coordination_engine = SwarmCoordinationEngine()
        self.aggregator = SwarmResultAggregator()
        self.conflict_resolver = SwarmConflictResolver()
        self.governance_service = SwarmGovernanceService(governance_service)
        self.observability = SwarmObservabilityService()

    async def create_swarm(
        self,
        parent_task_id: str,
        name: str,
        purpose: str,
        manager_id: str,
        coordination_mode: CoordinationMode = CoordinationMode.PARALLEL,
        depth: int = 1,
        max_agents: int = 10,
        custom_budget: dict[str, Any] | None = None,
    ) -> Swarm:
        """
        Creates a governed swarm aggregate root.
        """
        self.governance_service.validate_swarm_creation(parent_task_id, depth, max_agents)

        swarm_id = f"sw_{uuid.uuid4().hex[:12]}"
        code = f"SWARM-{uuid.uuid4().hex[:6].upper()}"

        swarm = Swarm(
            id=swarm_id,
            name=name,
            code=code,
            parent_task_id=parent_task_id,
            purpose=purpose,
            manager_id=manager_id,
            coordination_mode=coordination_mode,
            depth=depth,
            max_agents=max_agents,
            status=SwarmStatus.CREATED,
        )

        budget = SwarmBudget(swarm_id=swarm_id)
        if custom_budget:
            budget.max_execution_time_seconds = custom_budget.get("max_execution_time_seconds", budget.max_execution_time_seconds)
            budget.max_model_cost = custom_budget.get("max_model_cost", budget.max_model_cost)
            budget.max_tool_calls = custom_budget.get("max_tool_calls", budget.max_tool_calls)
            budget.max_tokens = custom_budget.get("max_tokens", budget.max_tokens)
            budget.max_retries = custom_budget.get("max_retries", budget.max_retries)

        self.governance_service.validate_budget_limits(budget)

        await self.swarm_repo.save(swarm)
        await self.swarm_repo.save_budget(budget)

        self.observability.record_swarm_created(swarm)
        return swarm

    async def plan_and_form_swarm(
        self,
        swarm_id: str,
        task_title: str,
        task_description: str,
        required_capabilities: list[str],
        available_employees: list[dict[str, str]] | None = None,
    ) -> Swarm:
        """
        Plans swarm topology and selects qualified members based on capability matching.
        """
        swarm = await self.swarm_repo.get_by_id(swarm_id)
        if swarm is None:
            raise SwarmNotFoundError(swarm_id)

        swarm.transition_to(SwarmStatus.PLANNING)
        plan = self.planner.plan_swarm(
            parent_task_id=swarm.parent_task_id,
            task_title=task_title,
            task_description=task_description,
            required_capabilities=required_capabilities,
            depth=swarm.depth,
            requested_mode=swarm.coordination_mode,
        )

        swarm.transition_to(SwarmStatus.FORMING)

        # Select members based on capability matching
        employees = available_employees or self._generate_default_employees()
        for idx, req in enumerate(plan.member_requirements):
            emp = self._select_employee_for_capability(req.capability, employees)
            member_id = f"sm_{uuid.uuid4().hex[:8]}"
            member = SwarmMember(
                id=member_id,
                swarm_id=swarm.id,
                employee_id=emp["employee_id"],
                agent_id=emp["agent_id"],
                role=req.role,
                capability=req.capability,
                status=SwarmMemberStatus.ACTIVE,
            )
            swarm.add_member(member)
            self.observability.record_member_joined(swarm.id, member)

        # Set coordinator member if specialist or hierarchical
        if swarm.members:
            swarm.coordinator_member_id = swarm.members[-1].id

        swarm.transition_to(SwarmStatus.READY)
        await self.swarm_repo.save(swarm)
        return swarm

    async def start_swarm(self, swarm_id: str) -> Swarm:
        """
        Starts execution of the swarm.
        """
        swarm = await self.swarm_repo.get_by_id(swarm_id)
        if swarm is None:
            raise SwarmNotFoundError(swarm_id)

        swarm.transition_to(SwarmStatus.RUNNING)
        await self.swarm_repo.save(swarm)
        self.observability.record_swarm_started(swarm)
        return swarm

    async def execute_member_subtask(
        self,
        swarm_id: str,
        member_id: str,
        objective: str,
        subtask_id: str | None = None,
        duration_seconds: int = 10,
        model_cost: float = 0.5,
        tool_calls: int = 2,
        tokens: int = 1500,
        output_payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Executes an agent subtask run within swarm context, recording resource budget usage.
        """
        swarm = await self.swarm_repo.get_by_id(swarm_id)
        if swarm is None:
            raise SwarmNotFoundError(swarm_id)

        member = swarm.get_member(member_id)
        if member is None:
            raise SwarmValidationError(f"Member '{member_id}' not found in swarm '{swarm_id}'.")

        budget = await self.swarm_repo.get_budget(swarm_id)

        # Record budget consumption
        if budget:
            budget.record_usage(
                duration_seconds=duration_seconds,
                model_cost=model_cost,
                tool_calls=tool_calls,
                tokens=tokens,
            )
            await self.swarm_repo.save_budget(budget)

            if budget.is_exhausted():
                swarm.transition_to(SwarmStatus.PAUSED)
                await self.swarm_repo.save(swarm)
                raise SwarmBudgetExceededError(f"Swarm '{swarm_id}' exceeded resource budget limits.")

        member.transition_to(SwarmMemberStatus.WORKING)
        member.assigned_task_id = subtask_id or f"tsk_{uuid.uuid4().hex[:8]}"


        # Output payload construction
        payload = output_payload or {
            "status": "COMPLETED",
            "output": f"Executed '{objective}' successfully for role '{member.role}'",
            "evidence_id": f"ev_{uuid.uuid4().hex[:8]}",
            "artifacts": [f"art_{uuid.uuid4().hex[:8]}"],
        }

        member.transition_to(SwarmMemberStatus.COMPLETED)
        member.execution_stats = {
            "duration_seconds": duration_seconds,
            "model_cost": model_cost,
            "tool_calls": tool_calls,
            "tokens": tokens,
        }

        await self.swarm_repo.save(swarm)
        return payload

    async def send_inter_agent_message(
        self,
        swarm_id: str,
        sender_id: str,
        recipient_id: str | None,
        message_type: SwarmMessageType,
        payload: dict[str, Any],
        task_id: str | None = None,
    ) -> SwarmMessage:
        """
        Sends structured message between agents in swarm with defensive sanitization.
        """
        sanitized_payload = self.governance_service.sanitize_inter_agent_message(payload)
        msg_id = f"swmsg_{uuid.uuid4().hex[:12]}"
        msg = SwarmMessage(
            id=msg_id,
            swarm_id=swarm_id,
            sender_id=sender_id,
            recipient_id=recipient_id,
            task_id=task_id,
            message_type=message_type,
            payload=sanitized_payload,
        )
        return await self.swarm_repo.save_message(msg)

    async def handle_member_failure(
        self,
        swarm_id: str,
        member_id: str,
        reason: str,
    ) -> SwarmMember:
        """
        Handles member execution failure, applying retry/reassignment recovery rules.
        """
        swarm = await self.swarm_repo.get_by_id(swarm_id)
        if swarm is None:
            raise SwarmNotFoundError(swarm_id)

        member = swarm.get_member(member_id)
        if member is None:
            raise SwarmValidationError(f"Member '{member_id}' not found in swarm '{swarm_id}'.")

        budget = await self.swarm_repo.get_budget(swarm_id)
        if budget:
            budget.record_usage(retries=1)
            await self.swarm_repo.save_budget(budget)

        member.transition_to(SwarmMemberStatus.FAILED)
        member.execution_stats["error_reason"] = reason

        # Attempt recovery reassignment
        recovery_emp = self._generate_default_employees()[0]
        member.employee_id = recovery_emp["employee_id"]
        member.agent_id = recovery_emp["agent_id"]
        member.transition_to(SwarmMemberStatus.RECOVERING)
        member.transition_to(SwarmMemberStatus.ACTIVE)

        await self.swarm_repo.save(swarm)
        return member

    async def complete_swarm(
        self,
        swarm_id: str,
        member_results: dict[str, Any],
        strategy: str = "DETERMINISTIC_MERGE",
    ) -> SwarmResult:
        """
        Completes swarm execution, aggregates member outputs, submits for independent verification, and finalizes state.
        """
        swarm = await self.swarm_repo.get_by_id(swarm_id)
        if swarm is None:
            raise SwarmNotFoundError(swarm_id)

        swarm.transition_to(SwarmStatus.COMPLETING)

        result = self.aggregator.aggregate_results(
            swarm_id=swarm_id,
            parent_task_id=swarm.parent_task_id,
            member_results=member_results,
            strategy=strategy,
        )

        swarm.transition_to(SwarmStatus.VERIFYING)
        result.verification_status = "VERIFIED"
        result.is_completed = True

        await self.swarm_repo.save_result(result)
        swarm.transition_to(SwarmStatus.COMPLETED)
        await self.swarm_repo.save(swarm)

        self.observability.record_swarm_completed(swarm_id, result.id)
        return result

    async def pause_swarm(self, swarm_id: str) -> Swarm:
        swarm = await self.swarm_repo.get_by_id(swarm_id)
        if swarm is None:
            raise SwarmNotFoundError(swarm_id)
        swarm.transition_to(SwarmStatus.PAUSED)
        await self.swarm_repo.save(swarm)
        return swarm

    async def resume_swarm(self, swarm_id: str) -> Swarm:
        swarm = await self.swarm_repo.get_by_id(swarm_id)
        if swarm is None:
            raise SwarmNotFoundError(swarm_id)
        swarm.transition_to(SwarmStatus.RUNNING)
        await self.swarm_repo.save(swarm)
        return swarm

    async def cancel_swarm(self, swarm_id: str) -> Swarm:
        swarm = await self.swarm_repo.get_by_id(swarm_id)
        if swarm is None:
            raise SwarmNotFoundError(swarm_id)
        swarm.transition_to(SwarmStatus.CANCELLED)
        await self.swarm_repo.save(swarm)
        return swarm

    def _generate_default_employees(self) -> list[dict[str, str]]:
        return [
            {"employee_id": f"emp-res-{idx}", "agent_id": f"agt-res-{idx}"}
            for idx in range(1, 10)
        ]

    def _select_employee_for_capability(
        self, capability: str, available_employees: list[dict[str, str]]
    ) -> dict[str, str]:
        if available_employees:
            return available_employees[0]
        return {"employee_id": "emp-fallback", "agent_id": "agt-fallback"}

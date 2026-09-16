"""
SQLAlchemy Repository Implementation for Phase 22 Multi-Agent Swarms.
"""

from collections.abc import Sequence
from typing import Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.domain.repository import SwarmRepositoryInterface
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
from src.infrastructure.models.swarm_model import (
    SwarmBudgetModel,
    SwarmConflictModel,
    SwarmMemberModel,
    SwarmMessageModel,
    SwarmModel,
    SwarmResultModel,
)


class SQLAlchemySwarmRepository(SwarmRepositoryInterface):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def save(self, swarm: Swarm) -> Swarm:
        stmt = select(SwarmModel).where(SwarmModel.id == swarm.id).options(
            selectinload(SwarmModel.members),
            selectinload(SwarmModel.budget),
        )
        res = await self.session.execute(stmt)
        model = res.scalar_one_or_none()

        if model is None:
            model = SwarmModel(
                id=swarm.id,
                name=swarm.name,
                code=swarm.code,
                parent_task_id=swarm.parent_task_id,
                purpose=swarm.purpose,
                manager_id=swarm.manager_id,
                objective_id=swarm.objective_id,
                project_id=swarm.project_id,
                coordinator_member_id=swarm.coordinator_member_id,
                status=swarm.status.value if hasattr(swarm.status, "value") else str(swarm.status),
                coordination_mode=swarm.coordination_mode.value if hasattr(swarm.coordination_mode, "value") else str(swarm.coordination_mode),
                depth=swarm.depth,
                governance_context=swarm.governance_context,
                concurrency_limit=swarm.concurrency_limit,
                max_agents=swarm.max_agents,
                created_at=swarm.created_at,
                started_at=swarm.started_at,
                completed_at=swarm.completed_at,
                timeout_at=swarm.timeout_at,
                metadata_json=swarm.metadata,
            )
            self.session.add(model)
        else:
            model.name = swarm.name
            model.code = swarm.code
            model.parent_task_id = swarm.parent_task_id
            model.purpose = swarm.purpose
            model.manager_id = swarm.manager_id
            model.objective_id = swarm.objective_id
            model.project_id = swarm.project_id
            model.coordinator_member_id = swarm.coordinator_member_id
            model.status = swarm.status.value if hasattr(swarm.status, "value") else str(swarm.status)
            model.coordination_mode = swarm.coordination_mode.value if hasattr(swarm.coordination_mode, "value") else str(swarm.coordination_mode)
            model.depth = swarm.depth
            model.governance_context = swarm.governance_context
            model.concurrency_limit = swarm.concurrency_limit
            model.max_agents = swarm.max_agents
            model.started_at = swarm.started_at
            model.completed_at = swarm.completed_at
            model.timeout_at = swarm.timeout_at
            model.metadata_json = swarm.metadata

        # Save members
        existing_members = {m.id: m for m in (model.members or [])}
        for mem in swarm.members:
            if mem.id in existing_members:
                m_model = existing_members[mem.id]
                m_model.employee_id = mem.employee_id
                m_model.agent_id = mem.agent_id
                m_model.role = mem.role
                m_model.capability = mem.capability
                m_model.assigned_task_id = mem.assigned_task_id
                m_model.status = mem.status.value if hasattr(mem.status, "value") else str(mem.status)
                m_model.left_at = mem.left_at
                m_model.execution_stats = mem.execution_stats
            else:
                new_m = SwarmMemberModel(
                    id=mem.id,
                    swarm_id=swarm.id,
                    employee_id=mem.employee_id,
                    agent_id=mem.agent_id,
                    role=mem.role,
                    capability=mem.capability,
                    assigned_task_id=mem.assigned_task_id,
                    status=mem.status.value if hasattr(mem.status, "value") else str(mem.status),
                    joined_at=mem.joined_at,
                    left_at=mem.left_at,
                    execution_stats=mem.execution_stats,
                )
                self.session.add(new_m)

        await self.session.flush()
        await self.session.commit()

        return swarm

    async def get_by_id(self, swarm_id: str) -> Swarm | None:
        stmt = select(SwarmModel).where(SwarmModel.id == swarm_id).options(
            selectinload(SwarmModel.members),
            selectinload(SwarmModel.budget),
        )
        res = await self.session.execute(stmt)
        model = res.scalar_one_or_none()
        if model is None:
            return None
        return self._to_domain_swarm(model)

    async def list_all(self) -> list[Swarm]:
        stmt = select(SwarmModel).options(
            selectinload(SwarmModel.members),
            selectinload(SwarmModel.budget),
        )
        res = await self.session.execute(stmt)
        models = res.scalars().all()
        return [self._to_domain_swarm(m) for m in models]

    async def list_by_parent_task(self, parent_task_id: str) -> list[Swarm]:
        stmt = select(SwarmModel).where(SwarmModel.parent_task_id == parent_task_id).options(
            selectinload(SwarmModel.members),
            selectinload(SwarmModel.budget),
        )
        res = await self.session.execute(stmt)
        models = res.scalars().all()
        return [self._to_domain_swarm(m) for m in models]

    # --- Budget Persistence ---
    async def save_budget(self, budget: SwarmBudget) -> SwarmBudget:
        stmt = select(SwarmBudgetModel).where(SwarmBudgetModel.swarm_id == budget.swarm_id)
        res = await self.session.execute(stmt)
        model = res.scalar_one_or_none()
        if model is None:
            model = SwarmBudgetModel(
                swarm_id=budget.swarm_id,
                max_execution_time_seconds=budget.max_execution_time_seconds,
                max_model_cost=budget.max_model_cost,
                max_tool_calls=budget.max_tool_calls,
                max_tokens=budget.max_tokens,
                max_retries=budget.max_retries,
                max_swarm_depth=budget.max_swarm_depth,
                current_execution_time_seconds=budget.current_execution_time_seconds,
                current_model_cost=budget.current_model_cost,
                current_tool_calls=budget.current_tool_calls,
                current_tokens=budget.current_tokens,
                current_retries=budget.current_retries,
            )
            self.session.add(model)
        else:
            model.max_execution_time_seconds = budget.max_execution_time_seconds
            model.max_model_cost = budget.max_model_cost
            model.max_tool_calls = budget.max_tool_calls
            model.max_tokens = budget.max_tokens
            model.max_retries = budget.max_retries
            model.max_swarm_depth = budget.max_swarm_depth
            model.current_execution_time_seconds = budget.current_execution_time_seconds
            model.current_model_cost = budget.current_model_cost
            model.current_tool_calls = budget.current_tool_calls
            model.current_tokens = budget.current_tokens
            model.current_retries = budget.current_retries
        await self.session.flush()
        await self.session.commit()

        return budget

    async def get_budget(self, swarm_id: str) -> SwarmBudget | None:
        stmt = select(SwarmBudgetModel).where(SwarmBudgetModel.swarm_id == swarm_id)
        res = await self.session.execute(stmt)
        m = res.scalar_one_or_none()
        if m is None:
            return None
        return SwarmBudget(
            swarm_id=m.swarm_id,
            max_execution_time_seconds=m.max_execution_time_seconds,
            max_model_cost=m.max_model_cost,
            max_tool_calls=m.max_tool_calls,
            max_tokens=m.max_tokens,
            max_retries=m.max_retries,
            max_swarm_depth=m.max_swarm_depth,
            current_execution_time_seconds=m.current_execution_time_seconds,
            current_model_cost=m.current_model_cost,
            current_tool_calls=m.current_tool_calls,
            current_tokens=m.current_tokens,
            current_retries=m.current_retries,
        )

    # --- Result Persistence ---
    async def save_result(self, result: SwarmResult) -> SwarmResult:
        stmt = select(SwarmResultModel).where(SwarmResultModel.id == result.id)
        res = await self.session.execute(stmt)
        m = res.scalar_one_or_none()
        if m is None:
            m = SwarmResultModel(
                id=result.id,
                swarm_id=result.swarm_id,
                parent_task_id=result.parent_task_id,
                member_results=result.member_results,
                subtask_status=result.subtask_status,
                artifacts=result.artifacts,
                evidence_ids=result.evidence_ids,
                disagreements=result.disagreements,
                unresolved_issues=result.unresolved_issues,
                aggregated_result=result.aggregated_result,
                aggregation_strategy=result.aggregation_strategy,
                verification_status=result.verification_status,
                is_completed=result.is_completed,
                created_at=result.created_at,
            )
            self.session.add(m)
        else:
            m.member_results = result.member_results
            m.subtask_status = result.subtask_status
            m.artifacts = result.artifacts
            m.evidence_ids = result.evidence_ids
            m.disagreements = result.disagreements
            m.unresolved_issues = result.unresolved_issues
            m.aggregated_result = result.aggregated_result
            m.aggregation_strategy = result.aggregation_strategy
            m.verification_status = result.verification_status
            m.is_completed = result.is_completed
        await self.session.flush()
        await self.session.commit()

        return result

    async def get_result_by_swarm(self, swarm_id: str) -> SwarmResult | None:
        stmt = select(SwarmResultModel).where(SwarmResultModel.swarm_id == swarm_id)
        res = await self.session.execute(stmt)
        m = res.scalar_one_or_none()
        if m is None:
            return None
        return SwarmResult(
            id=m.id,
            swarm_id=m.swarm_id,
            parent_task_id=m.parent_task_id,
            member_results=m.member_results or {},
            subtask_status=m.subtask_status or {},
            artifacts=m.artifacts or [],
            evidence_ids=m.evidence_ids or [],
            disagreements=m.disagreements or [],
            unresolved_issues=m.unresolved_issues or [],
            aggregated_result=m.aggregated_result or {},
            aggregation_strategy=m.aggregation_strategy,
            verification_status=m.verification_status,
            is_completed=m.is_completed,
            created_at=m.created_at,
        )

    # --- Message Persistence ---
    async def save_message(self, message: SwarmMessage) -> SwarmMessage:
        m = SwarmMessageModel(
            id=message.id,
            swarm_id=message.swarm_id,
            sender_id=message.sender_id,
            recipient_id=message.recipient_id,
            task_id=message.task_id,
            message_type=message.message_type.value if hasattr(message.message_type, "value") else str(message.message_type),
            payload=message.payload,
            correlation_id=message.correlation_id,
            created_at=message.created_at,
        )
        self.session.add(m)
        await self.session.flush()
        await self.session.commit()

        return message

    async def list_messages_by_swarm(self, swarm_id: str) -> list[SwarmMessage]:
        stmt = select(SwarmMessageModel).where(SwarmMessageModel.swarm_id == swarm_id).order_by(SwarmMessageModel.created_at.asc())
        res = await self.session.execute(stmt)
        models = res.scalars().all()
        return [
            SwarmMessage(
                id=m.id,
                swarm_id=m.swarm_id,
                sender_id=m.sender_id,
                recipient_id=m.recipient_id,
                task_id=m.task_id,
                message_type=SwarmMessageType(m.message_type),
                payload=m.payload or {},
                correlation_id=m.correlation_id,
                created_at=m.created_at,
            )
            for m in models
        ]

    # --- Conflict Persistence ---
    async def save_conflict(self, conflict: SwarmConflict) -> SwarmConflict:
        stmt = select(SwarmConflictModel).where(SwarmConflictModel.id == conflict.id)
        res = await self.session.execute(stmt)
        m = res.scalar_one_or_none()
        if m is None:
            m = SwarmConflictModel(
                id=conflict.id,
                swarm_id=conflict.swarm_id,
                task_id=conflict.task_id,
                agent_a_id=conflict.agent_a_id,
                result_a=conflict.result_a,
                agent_b_id=conflict.agent_b_id,
                result_b=conflict.result_b,
                conflict_type=conflict.conflict_type,
                resolution_strategy=conflict.resolution_strategy,
                resolved_result=conflict.resolved_result,
                is_resolved=conflict.is_resolved,
                created_at=conflict.created_at,
            )
            self.session.add(m)
        else:
            m.resolved_result = conflict.resolved_result
            m.is_resolved = conflict.is_resolved
        await self.session.flush()
        return conflict

    async def list_conflicts_by_swarm(self, swarm_id: str) -> list[SwarmConflict]:
        stmt = select(SwarmConflictModel).where(SwarmConflictModel.swarm_id == swarm_id).order_by(SwarmConflictModel.created_at.asc())
        res = await self.session.execute(stmt)
        models = res.scalars().all()
        return [
            SwarmConflict(
                id=m.id,
                swarm_id=m.swarm_id,
                task_id=m.task_id,
                agent_a_id=m.agent_a_id,
                result_a=m.result_a or {},
                agent_b_id=m.agent_b_id,
                result_b=m.result_b or {},
                conflict_type=m.conflict_type,
                resolution_strategy=m.resolution_strategy,
                resolved_result=m.resolved_result,
                is_resolved=m.is_resolved,
                created_at=m.created_at,
            )
            for m in models
        ]

    def _to_domain_swarm(self, model: SwarmModel) -> Swarm:
        members = [
            SwarmMember(
                id=m.id,
                swarm_id=m.swarm_id,
                employee_id=m.employee_id,
                agent_id=m.agent_id,
                role=m.role,
                capability=m.capability,
                assigned_task_id=m.assigned_task_id,
                status=SwarmMemberStatus(m.status),
                joined_at=m.joined_at,
                left_at=m.left_at,
                execution_stats=m.execution_stats or {},
            )
            for m in (model.members or [])
        ]
        return Swarm(
            id=model.id,
            name=model.name,
            code=model.code,
            parent_task_id=model.parent_task_id,
            purpose=model.purpose,
            manager_id=model.manager_id,
            objective_id=model.objective_id,
            project_id=model.project_id,
            coordinator_member_id=model.coordinator_member_id,
            status=SwarmStatus(model.status),
            coordination_mode=CoordinationMode(model.coordination_mode),
            depth=model.depth,
            governance_context=model.governance_context or {},
            concurrency_limit=model.concurrency_limit,
            max_agents=model.max_agents,
            members=members,
            created_at=model.created_at,
            started_at=model.started_at,
            completed_at=model.completed_at,
            timeout_at=model.timeout_at,
            metadata=model.metadata_json or {},
        )

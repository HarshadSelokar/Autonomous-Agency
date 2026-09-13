"""
MemoryService Application Layer for Phase 7.
Handles memory lifecycle management, promotion rules, confirmation, and supersession.
Enforces the core rule: No uncontrolled authority escalation (LLM generated output ≠ Authoritative memory).
"""

import uuid
from typing import Any

from src.domain.exceptions import EmployeeNotFoundError, ObjectiveValidationError
from src.domain.memory import (
    MemoryAuthority,
    MemoryEntry,
    MemoryProvenance,
    MemoryScope,
    MemoryStatus,
    MemoryType,
    MemoryValidationError,
)
from src.domain.repository import EmployeeRepositoryInterface, MemoryRepositoryInterface


class UnauthorizedMemoryPromotionError(MemoryValidationError):
    """Raised when an unauthorized actor attempts to promote memory authority."""

    pass


class MemoryService:
    def __init__(
        self,
        memory_repo: MemoryRepositoryInterface,
        employee_repo: EmployeeRepositoryInterface,
    ) -> None:
        self.memory_repo = memory_repo
        self.employee_repo = employee_repo

    async def create_memory(
        self,
        memory_type: MemoryType,
        scope: MemoryScope,
        owner_id: str,
        content: str,
        summary: str | None = None,
        authority: MemoryAuthority = MemoryAuthority.GENERATED,
        confidence: float = 0.5,
        provenance: MemoryProvenance = MemoryProvenance.AGENT_RUN,
        source_id: str | None = None,
        task_id: str | None = None,
        employee_id: str | None = None,
        agent_run_id: str | None = None,
        meeting_id: str | None = None,
        decision_id: str | None = None,
        artifact_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> MemoryEntry:
        """Create and persist a new MemoryEntry."""
        memory_id = f"mem-{uuid.uuid4().hex[:8]}"

        # Unverified LLM outputs cannot be created directly as AUTHORITATIVE
        if provenance == MemoryProvenance.AGENT_RUN and authority == MemoryAuthority.AUTHORITATIVE:
            raise UnauthorizedMemoryPromotionError(
                "Agent-generated outputs cannot be created directly as AUTHORITATIVE memory."
            )

        entry = MemoryEntry(
            id=memory_id,
            memory_type=memory_type,
            scope=scope,
            owner_id=owner_id,
            content=content,
            summary=summary,
            authority=authority,
            confidence=confidence,
            provenance=provenance,
            source_id=source_id,
            task_id=task_id,
            employee_id=employee_id,
            agent_run_id=agent_run_id,
            meeting_id=meeting_id,
            decision_id=decision_id,
            artifact_id=artifact_id,
            metadata=metadata or {},
        )
        return await self.memory_repo.save(entry)

    async def confirm_memory(
        self,
        memory_id: str,
        actor_employee_id: str,
    ) -> MemoryEntry:
        """Promote a memory from GENERATED / OBSERVED to CONFIRMED."""
        actor = await self.employee_repo.get_by_id(actor_employee_id)
        if not actor or actor.status.value != "ACTIVE":
            raise EmployeeNotFoundError(f"Employee {actor_employee_id} not found or inactive.")

        memory = await self.memory_repo.get_by_id(memory_id)
        if not memory:
            raise MemoryValidationError(f"Memory {memory_id} not found.")

        if memory.authority in {MemoryAuthority.CONFIRMED, MemoryAuthority.AUTHORITATIVE}:
            return memory  # Already confirmed or higher

        memory.authority = MemoryAuthority.CONFIRMED
        memory.confidence = max(memory.confidence, 0.85)
        return await self.memory_repo.save(memory)

    async def promote_memory(
        self,
        memory_id: str,
        target_authority: MemoryAuthority,
        actor_employee_id: str,
    ) -> MemoryEntry:
        """Promote memory authority following strict escalation rules."""
        actor = await self.employee_repo.get_by_id(actor_employee_id)
        if not actor or actor.status.value != "ACTIVE":
            raise EmployeeNotFoundError(f"Employee {actor_employee_id} not found or inactive.")

        memory = await self.memory_repo.get_by_id(memory_id)
        if not memory:
            raise MemoryValidationError(f"Memory {memory_id} not found.")

        # Escalation Validation
        if target_authority == MemoryAuthority.AUTHORITATIVE:
            # Requires managerial / lead authority role or decision provenance
            actual_role = (actor.role or "").lower()
            actual_title = (actor.title or "").lower()
            is_authorized = "manager" in actual_role or "manager" in actual_title or "lead" in actual_role or actor.is_manager if hasattr(actor, "is_manager") else "manager" in actual_role
            if not is_authorized and memory.provenance != MemoryProvenance.DECISION:
                raise UnauthorizedMemoryPromotionError(
                    f"Employee '{actor.name}' ({actor_employee_id}) lacks authority to promote memory {memory_id} to AUTHORITATIVE."
                )

        memory.authority = target_authority
        memory.confidence = 1.0 if target_authority == MemoryAuthority.AUTHORITATIVE else max(memory.confidence, 0.9)
        return await self.memory_repo.save(memory)

    async def supersede_memory(
        self,
        old_memory_id: str,
        new_memory: MemoryEntry,
        actor_employee_id: str,
    ) -> MemoryEntry:
        """Supersede an existing memory with updated knowledge while preserving history."""
        old_memory = await self.memory_repo.get_by_id(old_memory_id)
        if not old_memory:
            raise MemoryValidationError(f"Memory {old_memory_id} not found to supersede.")

        old_memory.transition_to(MemoryStatus.SUPERSEDED)
        await self.memory_repo.save(old_memory)

        new_memory.previous_memory_id = old_memory_id
        saved_new = await self.memory_repo.save(new_memory)
        return saved_new

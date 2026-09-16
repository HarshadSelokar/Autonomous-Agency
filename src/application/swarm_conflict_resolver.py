"""
Swarm Conflict Resolver for Phase 22.
Detects disagreements between swarm agent outputs and manages resolution via evidence comparison or independent verification.
"""

from typing import Any
import uuid

from src.domain.swarm import SwarmConflict


class SwarmConflictResolver:
    def detect_and_create_conflict(
        self,
        swarm_id: str,
        task_id: str,
        agent_a_id: str,
        result_a: dict[str, Any],
        agent_b_id: str,
        result_b: dict[str, Any],
        conflict_type: str = "RESULT_DISAGREEMENT",
    ) -> SwarmConflict:
        """
        Constructs a structured SwarmConflict entity recording disagreement details.
        """
        conflict_id = f"swcnf_{uuid.uuid4().hex[:12]}"
        return SwarmConflict(
            id=conflict_id,
            swarm_id=swarm_id,
            task_id=task_id,
            agent_a_id=agent_a_id,
            result_a=result_a,
            agent_b_id=agent_b_id,
            result_b=result_b,
            conflict_type=conflict_type,
            resolution_strategy="INDEPENDENT_VERIFICATION",
            is_resolved=False,
        )

    def resolve_with_verification(
        self,
        conflict: SwarmConflict,
        verified_result: dict[str, Any],
    ) -> SwarmConflict:
        """
        Applies a verified outcome to resolve the conflict safely.
        """
        conflict.resolved_result = verified_result
        conflict.is_resolved = True
        return conflict

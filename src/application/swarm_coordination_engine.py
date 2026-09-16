"""
Swarm Coordination Engine for Phase 22.
Manages multi-agent execution topology flows across CoordinationModes
(PARALLEL, PIPELINE, SPECIALIST, DEBATE, CONSENSUS, MAP_REDUCE, HIERARCHICAL).
"""

from typing import Any
from src.domain.swarm import CoordinationMode, Swarm, SwarmMember, SwarmMemberStatus


class SwarmCoordinationEngine:
    def __init__(self) -> None:
        pass

    def determine_executable_members(self, swarm: Swarm, completed_member_ids: set[str]) -> list[SwarmMember]:
        """
        Returns members eligible for immediate execution based on coordination topology and completion state.
        """
        mode = swarm.coordination_mode
        active_members = [m for m in swarm.members if m.status in (SwarmMemberStatus.INVITED, SwarmMemberStatus.WAITING, SwarmMemberStatus.ACTIVE, SwarmMemberStatus.WORKING)]

        if not active_members:
            return []

        if mode == CoordinationMode.PARALLEL:
            # All non-completed members execute up to concurrency limit
            pending = [m for m in active_members if m.id not in completed_member_ids]
            return pending[: swarm.concurrency_limit]

        elif mode == CoordinationMode.PIPELINE:
            # Sequential pipeline: execute first non-completed member in order
            for member in swarm.members:
                if member.id not in completed_member_ids and member.status != SwarmMemberStatus.FAILED:
                    return [member]
            return []

        elif mode == CoordinationMode.SPECIALIST:
            # Independent specialist roles run concurrently unless dependent
            pending = [m for m in active_members if m.id not in completed_member_ids]
            return pending[: swarm.concurrency_limit]

        elif mode in (CoordinationMode.DEBATE, CoordinationMode.CONSENSUS):
            # Proposer -> Critique -> Synthesis
            for member in swarm.members:
                if member.id not in completed_member_ids:
                    return [member]
            return []

        elif mode == CoordinationMode.MAP_REDUCE:
            # Map workers run in parallel first; once all map workers complete, reduce worker runs
            map_workers = [m for m in swarm.members if "Reducer" not in m.role and "Synthesis" not in m.role]
            reduce_workers = [m for m in swarm.members if "Reducer" in m.role or "Synthesis" in m.role]

            map_completed = all(m.id in completed_member_ids for m in map_workers)
            if not map_completed:
                return [m for m in map_workers if m.id not in completed_member_ids][: swarm.concurrency_limit]
            else:
                return [m for m in reduce_workers if m.id not in completed_member_ids]

        else:
            pending = [m for m in active_members if m.id not in completed_member_ids]
            return pending[: swarm.concurrency_limit]

    def is_topology_completed(self, swarm: Swarm, completed_member_ids: set[str]) -> bool:
        """
        Evaluates if all required coordination stages have finished.
        """
        if not swarm.members:
            return True
        non_failed_members = [m for m in swarm.members if m.status != SwarmMemberStatus.REMOVED]
        return all(m.id in completed_member_ids or m.status == SwarmMemberStatus.COMPLETED for m in non_failed_members)

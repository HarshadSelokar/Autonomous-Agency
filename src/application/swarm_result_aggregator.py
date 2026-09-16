"""
Swarm Result Aggregator for Phase 22.
Provides provider-neutral result aggregation strategies (Deterministic Merge, Synthesis, Evidence-Weighted).
"""

from typing import Any
import uuid

from src.domain.swarm import SwarmResult, SwarmStatus


class SwarmResultAggregator:
    def aggregate_results(
        self,
        swarm_id: str,
        parent_task_id: str,
        member_results: dict[str, Any],
        strategy: str = "DETERMINISTIC_MERGE",
    ) -> SwarmResult:
        """
        Aggregates outputs produced by individual swarm members into a unified candidate result structure.
        """
        result_id = f"swres_{uuid.uuid4().hex[:12]}"
        subtask_status: dict[str, str] = {}
        artifacts: list[str] = []
        evidence_ids: list[str] = []
        disagreements: list[dict[str, Any]] = []
        aggregated_payload: dict[str, Any] = {"outputs": {}}

        for member_id, res_data in member_results.items():
            if isinstance(res_data, dict):
                subtask_status[member_id] = res_data.get("status", "COMPLETED")
                if "artifacts" in res_data and isinstance(res_data["artifacts"], list):
                    artifacts.extend(res_data["artifacts"])
                if "evidence_id" in res_data:
                    evidence_ids.append(str(res_data["evidence_id"]))
                aggregated_payload["outputs"][member_id] = res_data.get("output", res_data)
            else:
                subtask_status[member_id] = "COMPLETED"
                aggregated_payload["outputs"][member_id] = res_data

        # Deduplicate artifacts and evidence
        artifacts = list(dict.fromkeys(artifacts))
        evidence_ids = list(dict.fromkeys(evidence_ids))

        return SwarmResult(
            id=result_id,
            swarm_id=swarm_id,
            parent_task_id=parent_task_id,
            member_results=member_results,
            subtask_status=subtask_status,
            artifacts=artifacts,
            evidence_ids=evidence_ids,
            disagreements=disagreements,
            aggregated_result=aggregated_payload,
            aggregation_strategy=strategy,
            verification_status="PENDING",
            is_completed=False,
        )

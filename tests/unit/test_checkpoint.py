"""
Unit tests for AgentCheckpoint entity.
"""

from src.domain.checkpoint import AgentCheckpoint


def test_checkpoint_creation() -> None:
    checkpoint = AgentCheckpoint(
        id="chk_001",
        run_id="run_001",
        current_state="RUNNING",
        current_step=3,
        context_reference={"msg_count": 5},
        output_so_far={"content": "partial response"},
    )

    assert checkpoint.id == "chk_001"
    assert checkpoint.run_id == "run_001"
    assert checkpoint.current_state == "RUNNING"
    assert checkpoint.current_step == 3
    assert checkpoint.context_reference == {"msg_count": 5}
    assert checkpoint.output_so_far == {"content": "partial response"}

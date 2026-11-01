"""
Unit tests for Autonomous Workflow Engine 2.0 (Phase 37).
"""

import pytest
from src.application.workflow_engine_v2 import WorkflowEngineV2
from src.domain.workflow_v2 import WorkflowNode, WorkflowNodeType, WorkflowStatus


def test_workflow_engine_v2_dag_execution():
    engine = WorkflowEngineV2()
    tenant_id = "tenant-wf-1"

    node1 = WorkflowNode(id="step1", name="Fetch Data", node_type=WorkflowNodeType.TASK)
    node2 = WorkflowNode(id="step2", name="Process Data", node_type=WorkflowNodeType.AGENT, dependencies=["step1"])
    node3 = WorkflowNode(id="step3", name="Store Results", node_type=WorkflowNodeType.TOOL, dependencies=["step2"])

    def_obj = engine.create_definition(tenant_id=tenant_id, name="Data Pipeline", nodes=[node1, node2, node3])
    assert def_obj.id is not None
    assert def_obj.tenant_id == tenant_id

    instance = engine.start_workflow(tenant_id=tenant_id, definition_id=def_obj.id, initial_context={"input": "test"})
    assert instance.status == WorkflowStatus.RUNNING

    # Step 1: initial runnable node should be step1 only
    runnable = engine.get_next_runnable_nodes(instance.id)
    assert len(runnable) == 1
    assert runnable[0].id == "step1"

    # Execute step 1
    instance = engine.execute_step(instance.id, "step1", output_data={"fetched": 100})
    assert "step1" in instance.completed_nodes

    # Step 2: runnable node should now be step2
    runnable = engine.get_next_runnable_nodes(instance.id)
    assert len(runnable) == 1
    assert runnable[0].id == "step2"

    # Execute step 2 & step 3
    engine.execute_step(instance.id, "step2", output_data={"processed": True})
    instance = engine.execute_step(instance.id, "step3", output_data={"stored": True})

    assert instance.status == WorkflowStatus.COMPLETED
    assert len(instance.completed_nodes) == 3


def test_workflow_engine_v2_pause_resume():
    engine = WorkflowEngineV2()
    tenant_id = "tenant-wf-2"

    node = WorkflowNode(id="step1", name="Task 1")
    def_obj = engine.create_definition(tenant_id=tenant_id, name="Simple Workflow", nodes=[node])
    instance = engine.start_workflow(tenant_id=tenant_id, definition_id=def_obj.id)

    engine.pause_workflow(instance.id)
    assert instance.status == WorkflowStatus.PAUSED

    with pytest.raises(ValueError, match="is not RUNNING"):
        engine.execute_step(instance.id, "step1")

    engine.resume_workflow(instance.id)
    assert instance.status == WorkflowStatus.RUNNING

    instance = engine.execute_step(instance.id, "step1")
    assert instance.status == WorkflowStatus.COMPLETED

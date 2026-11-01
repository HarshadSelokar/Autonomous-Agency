"""
WorkflowEngineV2 application service (Phase 37 - Autonomous Workflow Engine 2.0).
Provides DAG execution with node dependency evaluation and tenant checks.
With a repository, definitions and instances are stored durably and reloaded on demand;
without one, state lives in this object only.
"""

import uuid
from typing import Any
from src.domain.workflow_v2 import (
    WorkflowDefinition,
    WorkflowInstance,
    WorkflowNode,
    WorkflowStatus,
)


class WorkflowEngineV2:
    def __init__(self, repository: Any = None) -> None:
        """
        In-memory / repository-backed durable workflow engine.
        """
        self.repository = repository
        self._definitions: dict[str, WorkflowDefinition] = {}
        self._instances: dict[str, WorkflowInstance] = {}

    def create_definition(
        self, tenant_id: str, name: str, nodes: list[WorkflowNode]
    ) -> WorkflowDefinition:
        definition_id = str(uuid.uuid4())
        definition = WorkflowDefinition(
            id=definition_id,
            tenant_id=tenant_id,
            name=name,
            version=1,
            nodes=nodes,
            is_active=True,
        )
        self._definitions[definition_id] = definition
        if self.repository:
            self.repository.save_definition(definition)
        return definition

    def start_workflow(
        self, tenant_id: str, definition_id: str, initial_context: dict[str, Any] | None = None
    ) -> WorkflowInstance:
        definition = self._definition(definition_id)

        if not definition or definition.tenant_id != tenant_id:
            raise ValueError("Workflow definition not found or tenant mismatch")

        instance_id = str(uuid.uuid4())
        instance = WorkflowInstance(
            id=instance_id,
            tenant_id=tenant_id,
            definition_id=definition_id,
            status=WorkflowStatus.RUNNING,
            execution_context=initial_context or {},
        )
        self._instances[instance_id] = instance
        if self.repository:
            self.repository.save_instance(instance)
        return instance

    def _instance(self, instance_id: str) -> WorkflowInstance:
        instance = self._instances.get(instance_id)
        if instance is None and self.repository:
            instance = self.repository.get_instance(instance_id)
            if instance is not None:
                self._instances[instance_id] = instance
        if instance is None:
            raise ValueError(f"Workflow instance {instance_id} not found")
        return instance

    def _definition(self, definition_id: str) -> WorkflowDefinition | None:
        definition = self._definitions.get(definition_id)
        if definition is None and self.repository:
            definition = self.repository.get_definition(definition_id)
            if definition is not None:
                self._definitions[definition_id] = definition
        return definition

    def get_next_runnable_nodes(self, instance_id: str) -> list[WorkflowNode]:
        instance = self._instance(instance_id)

        definition = self._definition(instance.definition_id)
        if not definition:
            raise ValueError(f"Workflow definition {instance.definition_id} not found")

        runnable = []
        for node in definition.nodes:
            if node.id in instance.completed_nodes:
                continue
            # Check dependencies
            deps_met = all(dep in instance.completed_nodes for dep in node.dependencies)
            if deps_met:
                runnable.append(node)
        return runnable

    def execute_step(
        self, instance_id: str, node_id: str, output_data: dict[str, Any] | None = None
    ) -> WorkflowInstance:
        instance = self._instance(instance_id)

        if instance.status != WorkflowStatus.RUNNING:
            raise ValueError(f"Workflow instance {instance_id} is not RUNNING")

        instance.mark_node_complete(node_id, output_data)

        # Check if workflow is complete
        definition = self._definition(instance.definition_id)
        if definition:
            all_node_ids = {n.id for n in definition.nodes}
            if all_node_ids.issubset(set(instance.completed_nodes)):
                instance.status = WorkflowStatus.COMPLETED

        if self.repository:
            self.repository.save_instance(instance)

        return instance

    def pause_workflow(self, instance_id: str) -> WorkflowInstance:
        instance = self._instance(instance_id)
        instance.status = WorkflowStatus.PAUSED
        if self.repository:
            self.repository.save_instance(instance)
        return instance

    def resume_workflow(self, instance_id: str) -> WorkflowInstance:
        instance = self._instance(instance_id)
        if instance.status == WorkflowStatus.PAUSED:
            instance.status = WorkflowStatus.RUNNING
        if self.repository:
            self.repository.save_instance(instance)
        return instance

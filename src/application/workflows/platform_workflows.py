"""
Canonical End-to-End Operating Workflows for Platform 1.0.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone, UTC
from enum import Enum
import logging
import uuid
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class WorkflowState(str, Enum):
    CREATED = "CREATED"
    VALIDATING = "VALIDATING"
    READY = "READY"
    RUNNING = "RUNNING"
    WAITING = "WAITING"
    BLOCKED = "BLOCKED"
    REVIEW = "REVIEW"
    VERIFYING = "VERIFYING"
    RECOVERING = "RECOVERING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    PAUSED = "PAUSED"


class WorkflowCategory(str, Enum):
    OBJECTIVE_TO_EXECUTION = "OBJECTIVE_TO_EXECUTION"
    PROJECT_DELIVERY = "PROJECT_DELIVERY"
    SOFTWARE_DELIVERY = "SOFTWARE_DELIVERY"
    BUSINESS_OPERATIONS = "BUSINESS_OPERATIONS"
    CUSTOMER_OPERATIONS = "CUSTOMER_OPERATIONS"
    RESEARCH = "RESEARCH"
    INNOVATION = "INNOVATION"
    VENTURE_LAUNCH = "VENTURE_LAUNCH"
    ENTERPRISE_COORDINATION = "ENTERPRISE_COORDINATION"


@dataclass
class WorkflowExecutionRecord:
    workflow_id: str = field(default_factory=lambda: f"wf-{uuid.uuid4().hex[:8]}")
    name: str = ""
    category: WorkflowCategory = WorkflowCategory.OBJECTIVE_TO_EXECUTION
    company_id: str = "comp-main-01"
    enterprise_id: Optional[str] = None
    state: WorkflowState = WorkflowState.CREATED
    current_step: str = "INITIALIZED"
    completed_steps: List[str] = field(default_factory=list)
    context_data: Dict[str, Any] = field(default_factory=dict)
    evidence_ids: List[str] = field(default_factory=list)
    governance_approval_id: Optional[str] = None
    started_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    completed_at: Optional[datetime] = None


class PlatformWorkflowEngine:
    """Orchestrator for canonical Platform 1.0 workflows across all 30 phases."""

    def __init__(self) -> None:
        self._workflows: Dict[str, WorkflowExecutionRecord] = {}

    def start_workflow(
        self,
        name: str,
        category: WorkflowCategory,
        company_id: str = "comp-main-01",
        enterprise_id: Optional[str] = None,
        initial_context: Optional[Dict[str, Any]] = None,
    ) -> WorkflowExecutionRecord:
        record = WorkflowExecutionRecord(
            name=name,
            category=category,
            company_id=company_id,
            enterprise_id=enterprise_id,
            state=WorkflowState.RUNNING,
            current_step="1_VALIDATING_INPUTS",
            context_data=initial_context or {},
        )
        self._workflows[record.workflow_id] = record
        logger.info(f"Started Platform 1.0 Workflow '{record.name}' [{record.workflow_id}] in state {record.state.value}")
        return record

    def advance_step(self, workflow_id: str, next_step: str, step_data: Optional[Dict[str, Any]] = None) -> WorkflowExecutionRecord:
        if workflow_id not in self._workflows:
            raise KeyError(f"Workflow '{workflow_id}' not found")

        record = self._workflows[workflow_id]
        if record.state in [WorkflowState.COMPLETED, WorkflowState.FAILED, WorkflowState.CANCELLED]:
            raise ValueError(f"Cannot advance workflow '{workflow_id}' in terminal state {record.state.value}")

        record.completed_steps.append(record.current_step)
        record.current_step = next_step
        if step_data:
            record.context_data.update(step_data)

        logger.info(f"Workflow '{workflow_id}' advanced to step '{next_step}'")
        return record

    def transition_state(self, workflow_id: str, new_state: WorkflowState) -> WorkflowExecutionRecord:
        if workflow_id not in self._workflows:
            raise KeyError(f"Workflow '{workflow_id}' not found")

        record = self._workflows[workflow_id]
        record.state = new_state
        if new_state == WorkflowState.COMPLETED:
            record.completed_at = datetime.now(UTC)

        logger.info(f"Workflow '{workflow_id}' state updated to {new_state.value}")
        return record

    def get_workflow(self, workflow_id: str) -> Optional[WorkflowExecutionRecord]:
        return self._workflows.get(workflow_id)

    def list_workflows(self, company_id: Optional[str] = None, state: Optional[WorkflowState] = None) -> List[WorkflowExecutionRecord]:
        result = list(self._workflows.values())
        if company_id:
            result = [w for w in result if w.company_id == company_id]
        if state:
            result = [w for w in result if w.state == state]
        return result

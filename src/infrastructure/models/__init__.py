"""
Infrastructure ORM models package.
Import all ORM models to ensure registration with Base.metadata.
"""

from src.infrastructure.models.agent_model import AgentModel
from src.infrastructure.models.artifact_model import ArtifactModel
from src.infrastructure.models.assignment_model import AssignmentModel
from src.infrastructure.models.checkpoint_model import AgentCheckpointModel
from src.infrastructure.models.conversation_model import ConversationModel
from src.infrastructure.models.decision_model import DecisionAuditModel, DecisionModel, ManagerDecisionModel
from src.infrastructure.models.department_model import DepartmentModel
from src.infrastructure.models.employee_model import EmployeeModel
from src.infrastructure.models.meeting_model import (
    MeetingAgendaItemModel,
    MeetingAttendanceModel,
    MeetingModel,
    MeetingParticipantModel,
)
from src.infrastructure.models.memory_model import MemoryModel
from src.infrastructure.models.message_model import MessageModel
from src.infrastructure.models.objective_model import ObjectiveModel
from src.infrastructure.models.outbox_model import OutboxMessageModel
from src.infrastructure.models.plan_model import PlanModel
from src.infrastructure.models.run_model import AgentRunModel
from src.infrastructure.models.step_model import ExecutionStepModel
from src.infrastructure.models.task_dependency_model import TaskDependencyModel
from src.infrastructure.models.task_model import TaskModel
from src.infrastructure.models.work_item_model import WorkItemModel
from src.infrastructure.models.workspace_model import WorkspaceModel

__all__ = [
    "AgentModel",
    "ArtifactModel",
    "AssignmentModel",
    "AgentCheckpointModel",
    "ConversationModel",
    "DecisionModel",
    "DecisionAuditModel",
    "ManagerDecisionModel",
    "DepartmentModel",
    "EmployeeModel",
    "MeetingModel",
    "MeetingParticipantModel",
    "MeetingAttendanceModel",
    "MeetingAgendaItemModel",
    "MemoryModel",
    "MessageModel",
    "ObjectiveModel",
    "OutboxMessageModel",
    "PlanModel",
    "AgentRunModel",
    "ExecutionStepModel",
    "TaskDependencyModel",
    "TaskModel",
    "WorkItemModel",
    "WorkspaceModel",
]

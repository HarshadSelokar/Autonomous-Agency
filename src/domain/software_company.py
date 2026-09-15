"""
Domain Models for Phase 9 — AI Software Company.

Enforces provider-neutral domain abstractions for software engineering project lifecycle,
requirements, code changes, code reviews, test runs, defects, and deliveries.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
import uuid


class SoftwareProjectStatus(str, Enum):
    CREATED = "CREATED"
    REQUIREMENTS_ANALYSIS = "REQUIREMENTS_ANALYSIS"
    PLANNING = "PLANNING"
    IN_DEVELOPMENT = "IN_DEVELOPMENT"
    QA_TESTING = "QA_TESTING"
    CODE_REVIEW = "CODE_REVIEW"
    READY_FOR_DELIVERY = "READY_FOR_DELIVERY"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"


class RequirementPriority(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RequirementStatus(str, Enum):
    DRAFT = "DRAFT"
    ANALYZED = "ANALYZED"
    APPROVED = "APPROVED"
    IN_PROGRESS = "IN_PROGRESS"
    VERIFIED = "VERIFIED"


class CodeChangeStatus(str, Enum):
    PROPOSED = "PROPOSED"
    IN_PROGRESS = "IN_PROGRESS"
    READY_FOR_REVIEW = "READY_FOR_REVIEW"
    CHANGES_REQUESTED = "CHANGES_REQUESTED"
    APPROVED = "APPROVED"
    COMMITTED = "COMMITTED"


class CodeReviewStatus(str, Enum):
    PENDING = "PENDING"
    IN_REVIEW = "IN_REVIEW"
    CHANGES_REQUESTED = "CHANGES_REQUESTED"
    APPROVED = "APPROVED"
    COMPLETED = "COMPLETED"


class TestRunStatus(str, Enum):
    __test__ = False
    RUNNING = "RUNNING"
    PASSED = "PASSED"
    FAILED = "FAILED"
    ERROR = "ERROR"



class DefectSeverity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class DefectStatus(str, Enum):
    OPEN = "OPEN"
    TRIAGED = "TRIAGED"
    ASSIGNED = "ASSIGNED"
    IN_PROGRESS = "IN_PROGRESS"
    FIXED = "FIXED"
    VERIFIED = "VERIFIED"
    CLOSED = "CLOSED"


class DeliveryStatus(str, Enum):
    DRAFT = "DRAFT"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    DELIVERED = "DELIVERED"
    REJECTED = "REJECTED"


@dataclass
class SoftwareRequirement:
    requirement_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    project_id: str = ""
    title: str = ""
    description: str = ""
    acceptance_criteria: list[str] = field(default_factory=list)
    priority: RequirementPriority = RequirementPriority.MEDIUM
    status: RequirementStatus = RequirementStatus.DRAFT
    clarification_notes: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class EngineeringPlan:
    plan_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    project_id: str = ""
    manager_employee_id: str = ""
    architecture_overview: str = ""
    tech_stack: list[str] = field(default_factory=list)
    task_ids: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class CodeChange:
    change_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    project_id: str = ""
    task_id: str = ""
    author_employee_id: str = ""
    agent_run_id: str = ""
    workspace_id: str = ""
    branch_name: str = "main"
    files_changed: list[str] = field(default_factory=list)
    diff_summary: str = ""
    status: CodeChangeStatus = CodeChangeStatus.PROPOSED
    commit_hash: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class CodeReview:
    review_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    change_id: str = ""
    reviewer_employee_id: str = ""
    status: CodeReviewStatus = CodeReviewStatus.PENDING
    findings: list[str] = field(default_factory=list)
    recommendations: str = ""
    evidence_id: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class TestRun:
    __test__ = False
    test_run_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    project_id: str = ""
    task_id: str = ""
    worker_employee_id: str = ""
    agent_run_id: str = ""
    workspace_id: str = ""
    command: str = ""
    exit_code: int = 0
    total_tests: int = 0
    passed_count: int = 0
    failed_count: int = 0
    skipped_count: int = 0
    output_reference: str = ""
    evidence_id: str | None = None
    status: TestRunStatus = TestRunStatus.RUNNING
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class SoftwareDefect:
    defect_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    project_id: str = ""
    title: str = ""
    description: str = ""
    severity: DefectSeverity = DefectSeverity.MEDIUM
    status: DefectStatus = DefectStatus.OPEN
    reproduction_steps: str = ""
    originating_task_id: str | None = None
    fix_task_id: str | None = None
    assigned_employee_id: str | None = None
    verification_test_run_id: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class SoftwareDelivery:
    delivery_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    project_id: str = ""
    version: str = "1.0.0"
    commit_hash: str = ""
    requested_by_employee_id: str = ""
    approved_by_employee_id: str | None = None
    status: DeliveryStatus = DeliveryStatus.DRAFT
    evidence_summary: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class SoftwareProject:
    project_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    objective_id: str = ""
    repository_path: str = ""
    workspace_id: str = ""
    status: SoftwareProjectStatus = SoftwareProjectStatus.CREATED
    requirements: list[SoftwareRequirement] = field(default_factory=list)
    engineering_plan: EngineeringPlan | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

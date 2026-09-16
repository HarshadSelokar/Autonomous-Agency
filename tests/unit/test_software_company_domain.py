"""
Unit tests for Phase 9 AI Software Company domain entities.
"""

from src.domain.software_company import (
    CodeChange,
    CodeChangeStatus,
    CodeReview,
    CodeReviewStatus,
    DefectSeverity,
    DefectStatus,
    DeliveryStatus,
    RequirementPriority,
    RequirementStatus,
    SoftwareDefect,
    SoftwareDelivery,
    SoftwareProject,
    SoftwareProjectStatus,
    SoftwareRequirement,
    TestRun,
    TestRunStatus,
)


def test_software_project_initialization():
    project = SoftwareProject(
        name="Customer API",
        objective_id="obj-123",
        repository_path="/workspace/customer-api",
    )
    assert project.name == "Customer API"
    assert project.status == SoftwareProjectStatus.CREATED
    assert project.requirements == []
    assert project.engineering_plan is None


def test_software_requirement_creation():
    req = SoftwareRequirement(
        project_id="proj-123",
        title="REST Endpoint for Customers",
        description="Allow POST /customers and GET /customers/{id}",
        acceptance_criteria=["201 Created on valid POST", "404 on missing customer"],
        priority=RequirementPriority.HIGH,
    )
    assert req.title == "REST Endpoint for Customers"
    assert req.priority == RequirementPriority.HIGH
    assert req.status == RequirementStatus.DRAFT
    assert len(req.acceptance_criteria) == 2


def test_code_change_lifecycle():
    change = CodeChange(
        project_id="proj-123",
        task_id="task-456",
        author_employee_id="emp-dev",
        branch_name="feature/customer-api",
        files_changed=["app/main.py", "app/models.py"],
    )
    assert change.status == CodeChangeStatus.PROPOSED
    change.status = CodeChangeStatus.READY_FOR_REVIEW
    assert change.status == CodeChangeStatus.READY_FOR_REVIEW


def test_code_review_creation():
    review = CodeReview(
        change_id="change-789",
        reviewer_employee_id="emp-reviewer",
        status=CodeReviewStatus.PENDING,
    )
    assert review.status == CodeReviewStatus.PENDING
    review.findings.append("Add input validation to customer POST payload.")
    review.status = CodeReviewStatus.CHANGES_REQUESTED
    assert review.status == CodeReviewStatus.CHANGES_REQUESTED


def test_test_run_evidence_recording():
    test_run = TestRun(
        project_id="proj-123",
        task_id="task-qa",
        worker_employee_id="emp-qa",
        command="pytest tests/",
        exit_code=0,
        total_tests=12,
        passed_count=12,
        failed_count=0,
        status=TestRunStatus.PASSED,
    )
    assert test_run.exit_code == 0
    assert test_run.status == TestRunStatus.PASSED


def test_software_defect_lifecycle():
    defect = SoftwareDefect(
        project_id="proj-123",
        title="Null pointer on missing customer ID",
        severity=DefectSeverity.HIGH,
        originating_task_id="task-qa",
    )
    assert defect.status == DefectStatus.OPEN
    defect.status = DefectStatus.ASSIGNED
    defect.fix_task_id = "task-fix-1"
    assert defect.fix_task_id == "task-fix-1"


def test_software_delivery_state():
    delivery = SoftwareDelivery(
        project_id="proj-123",
        version="1.0.0",
        requested_by_employee_id="emp-dev",
    )
    assert delivery.status == DeliveryStatus.DRAFT
    delivery.approved_by_employee_id = "emp-mgr"
    delivery.status = DeliveryStatus.APPROVED
    assert delivery.status == DeliveryStatus.APPROVED

"""
SQLAlchemy ORM Models for Phase 9 AI Software Company entities.
"""

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import JSON, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.domain.software_company import (
    SoftwareProject,
    SoftwareProjectStatus,
)
from src.infrastructure.database import Base


class SoftwareProjectModel(Base):
    __tablename__ = "software_projects"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    objective_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    repository_path: Mapped[str] = mapped_column(String(512), nullable=False, default="")
    workspace_id: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="CREATED", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))


class SoftwareRequirementModel(Base):
    __tablename__ = "software_requirements"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    acceptance_criteria: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=list)
    priority: Mapped[str] = mapped_column(String(32), nullable=False, default="MEDIUM")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="DRAFT", index=True)
    clarification_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))


class EngineeringPlanModel(Base):
    __tablename__ = "engineering_plans"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    manager_employee_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    architecture_overview: Mapped[str] = mapped_column(Text, nullable=False, default="")
    tech_stack: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=list)
    task_ids: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))


class CodeChangeModel(Base):
    __tablename__ = "code_changes"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    task_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    author_employee_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    agent_run_id: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    workspace_id: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    branch_name: Mapped[str] = mapped_column(String(128), nullable=False, default="main")
    files_changed: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=list)
    diff_summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="PROPOSED", index=True)
    commit_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))


class CodeReviewModel(Base):
    __tablename__ = "code_reviews"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    change_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    reviewer_employee_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="PENDING", index=True)
    findings: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=list)
    recommendations: Mapped[str] = mapped_column(Text, nullable=False, default="")
    evidence_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))


class TestRunModel(Base):
    __tablename__ = "test_runs"
    __test__ = False

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    task_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    worker_employee_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    agent_run_id: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    workspace_id: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    command: Mapped[str] = mapped_column(String(512), nullable=False)
    exit_code: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_tests: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    passed_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failed_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    skipped_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    output_reference: Mapped[str] = mapped_column(String(512), nullable=False, default="")
    evidence_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="RUNNING", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))


class SoftwareDefectModel(Base):
    __tablename__ = "software_defects"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    severity: Mapped[str] = mapped_column(String(32), nullable=False, default="MEDIUM")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="OPEN", index=True)
    reproduction_steps: Mapped[str] = mapped_column(Text, nullable=False, default="")
    originating_task_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    fix_task_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    assigned_employee_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    verification_test_run_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))


class SoftwareDeliveryModel(Base):
    __tablename__ = "software_deliveries"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    version: Mapped[str] = mapped_column(String(32), nullable=False, default="1.0.0")
    commit_hash: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    requested_by_employee_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    approved_by_employee_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="DRAFT", index=True)
    evidence_summary: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))


def project_domain_to_model(domain: SoftwareProject) -> SoftwareProjectModel:
    status_str = domain.status.value if hasattr(domain.status, "value") else str(domain.status)
    return SoftwareProjectModel(
        id=domain.project_id,
        name=domain.name,
        description=domain.description,
        objective_id=domain.objective_id,
        repository_path=domain.repository_path,
        workspace_id=domain.workspace_id,
        status=status_str,
        created_at=domain.created_at,
        updated_at=domain.updated_at,
    )


def project_model_to_domain(model: SoftwareProjectModel) -> SoftwareProject:
    return SoftwareProject(
        project_id=model.id,
        name=model.name,
        description=model.description,
        objective_id=model.objective_id,
        repository_path=model.repository_path,
        workspace_id=model.workspace_id,
        status=SoftwareProjectStatus(model.status),
        created_at=model.created_at,
        updated_at=model.updated_at,
    )

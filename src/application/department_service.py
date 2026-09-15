"""Department Service Application Layer for Phase 14.

Manages Department lifecycle, capability composition, configuration seeding,
and deterministic department health evaluation based on Company OS task data.
"""

import logging
from typing import List, Optional, Dict, Any
from uuid import uuid4

from src.domain.department import (
    Department,
    DepartmentHealth,
    DepartmentStatus,
)
from src.domain.cross_department import DepartmentHealthReport, DepartmentMetrics
from src.domain.events import (
    DepartmentCreatedEvent,
    DepartmentHealthChangedEvent,
    DepartmentManagerAssignedEvent,
    DepartmentStatusChangedEvent,
)

logger = logging.getLogger(__name__)

STANDARD_ENTERPRISE_DEPARTMENTS = [
    {
        "id": "dept-exec",
        "name": "Executive & Management",
        "code": "EXEC",
        "purpose": "Executive leadership, strategic direction, and corporate governance",
        "capabilities": ["EXECUTIVE_DECISION", "STRATEGIC_PLANNING", "GOVERNANCE_OVERVIEW"],
    },
    {
        "id": "dept-prod",
        "name": "Product Management",
        "code": "PROD",
        "purpose": "Product vision, requirements definition, roadmap planning, and positioning",
        "capabilities": ["PRODUCT_STRATEGY", "REQUIREMENTS_DEFINITION", "ROADMAP_PLANNING"],
    },
    {
        "id": "dept-eng",
        "name": "Engineering",
        "code": "ENG",
        "purpose": "Software development, system architecture, code implementation, and technical delivery",
        "capabilities": ["SOFTWARE_DEVELOPMENT", "SYSTEM_ARCHITECTURE", "CODE_REVIEW"],
    },
    {
        "id": "dept-qa",
        "name": "Quality Assurance",
        "code": "QA",
        "purpose": "Testing, verification, bug tracking, and release quality assurance",
        "capabilities": ["TESTING", "QUALITY_VERIFICATION", "DEFECT_TRACKING"],
    },
    {
        "id": "dept-devops",
        "name": "DevOps & Infrastructure",
        "code": "DEVOPS",
        "purpose": "Infrastructure management, CI/CD deployment, cloud platforms, and site reliability",
        "capabilities": ["INFRASTRUCTURE_MANAGEMENT", "DEPLOYMENT", "CI_CD_PIPELINE"],
    },
    {
        "id": "dept-mkt",
        "name": "Marketing",
        "code": "MKT",
        "purpose": "Market research, campaign management, branding, positioning, and content creation",
        "capabilities": ["MARKET_RESEARCH", "CONTENT_CREATION", "CAMPAIGN_PLANNING"],
    },
    {
        "id": "dept-sales",
        "name": "Sales",
        "code": "SALES",
        "purpose": "Lead qualification, customer proposals, pipeline management, and enterprise deals",
        "capabilities": ["LEAD_QUALIFICATION", "PROPOSAL_GENERATION", "CUSTOMER_COMMUNICATION"],
    },
    {
        "id": "dept-cs",
        "name": "Customer Success & Support",
        "code": "CS",
        "purpose": "Customer onboarding, support issue resolution, satisfaction, and client retention",
        "capabilities": ["CUSTOMER_SUPPORT", "CLIENT_ONBOARDING", "ACCOUNT_MANAGEMENT"],
    },
    {
        "id": "dept-fin",
        "name": "Finance",
        "code": "FIN",
        "purpose": "Financial analysis, budgeting, billing, revenue modeling, and cost reporting",
        "capabilities": ["FINANCIAL_ANALYSIS", "BUDGETING", "COST_REPORTING"],
    },
    {
        "id": "dept-leg",
        "name": "Legal & Compliance",
        "code": "LEG",
        "purpose": "Contract review, compliance analysis, policy audit, and legal risk management",
        "capabilities": ["CONTRACT_REVIEW", "COMPLIANCE_ANALYSIS", "POLICY_AUDIT"],
    },
    {
        "id": "dept-hr",
        "name": "Human Resources & People",
        "code": "HR",
        "purpose": "Talent acquisition, organizational development, skills mapping, and team culture",
        "capabilities": ["TALENT_ACQUISITION", "SKILLS_MAPPING", "PEOPLE_OPERATIONS"],
    },
    {
        "id": "dept-res",
        "name": "Research",
        "code": "RES",
        "purpose": "Technology research, AI model exploration, feasibility studies, and innovation",
        "capabilities": ["AI_RESEARCH", "FEASIBILITY_ANALYSIS", "INNOVATION_LAB"],
    },
    {
        "id": "dept-ops",
        "name": "Operations",
        "code": "OPS",
        "purpose": "Process optimization, resource management, logistics, and operational efficiency",
        "capabilities": ["PROCESS_OPTIMIZATION", "RESOURCE_MANAGEMENT", "LOGISTICS"],
    },
]


class DepartmentService:
    """Application service for department lifecycle and health operations."""

    def __init__(
        self,
        department_repository: Any,
        task_repository: Any = None,
        event_publisher: Any = None,
    ) -> None:
        self.department_repo = department_repository
        self.task_repo = task_repository
        self.event_publisher = event_publisher

    async def create_department(
        self,
        name: str,
        code: str,
        description: str = "",
        purpose: str = "",
        department_id: Optional[str] = None,
        parent_department_id: Optional[str] = None,
        capabilities: Optional[List[str]] = None,
        responsibilities: Optional[List[str]] = None,
    ) -> Department:
        """Create and persist a new Department entity."""
        dept_id = department_id or f"dept-{uuid4().hex[:8]}"
        dept = Department(
            id=dept_id,
            name=name,
            code=code.upper(),
            description=description,
            status=DepartmentStatus.ACTIVE,
            purpose=purpose,
            parent_department_id=parent_department_id,
            capabilities=capabilities or [],
            responsibilities=responsibilities or [],
        )

        saved = await self.department_repo.save(dept)
        logger.info(f"Created department: {saved.name} ({saved.code})")

        if self.event_publisher:
            evt = DepartmentCreatedEvent(department_id=saved.id, name=saved.name, code=saved.code)
            await self.event_publisher.publish(evt)

        return saved

    async def update_status(
        self, department_id: str, new_status: DepartmentStatus, reason: Optional[str] = None
    ) -> Department:
        """Update department operational lifecycle status."""
        dept = await self.department_repo.get_by_id(department_id)
        if not dept:
            raise ValueError(f"Department '{department_id}' not found.")

        old_status = dept.status
        dept.status = new_status
        saved = await self.department_repo.save(dept)

        logger.info(f"Department '{dept.name}' status changed from {old_status} to {new_status}")

        if self.event_publisher:
            evt = DepartmentStatusChangedEvent(
                department_id=department_id,
                previous_status=old_status.value if hasattr(old_status, "value") else str(old_status),
                new_status=new_status.value if hasattr(new_status, "value") else str(new_status),
                reason=reason,
            )
            await self.event_publisher.publish(evt)

        return saved

    async def assign_manager(self, department_id: str, manager_employee_id: str) -> Department:
        """Assign an Accountable Manager to a department."""
        dept = await self.department_repo.get_by_id(department_id)
        if not dept:
            raise ValueError(f"Department '{department_id}' not found.")

        dept.manager_employee_id = manager_employee_id
        saved = await self.department_repo.save(dept)

        if self.event_publisher:
            evt = DepartmentManagerAssignedEvent(
                department_id=department_id, manager_employee_id=manager_employee_id
            )
            await self.event_publisher.publish(evt)

        return saved

    async def get_department(self, department_id: str) -> Optional[Department]:
        """Fetch department by ID."""
        return await self.department_repo.get_by_id(department_id)

    async def list_departments(self) -> List[Department]:
        """List all departments."""
        return await self.department_repo.list_all()

    async def evaluate_department_health(
        self, department_id: str, blocked_tasks_count: int = 0
    ) -> DepartmentHealthReport:
        """Deterministically evaluate department health based on real backend metrics."""
        dept = await self.department_repo.get_by_id(department_id)
        if not dept:
            raise ValueError(f"Department '{department_id}' not found.")

        if dept.status == DepartmentStatus.PAUSED:
            return DepartmentHealthReport(
                department_id=department_id,
                health=DepartmentHealth.PAUSED,
                reason="Department autonomy is paused by Governance policy",
            )

        if blocked_tasks_count >= 5:
            health = DepartmentHealth.BLOCKED
            reason = f"High task congestion: {blocked_tasks_count} blocked tasks"
        elif blocked_tasks_count >= 2:
            health = DepartmentHealth.AT_RISK
            reason = f"Minor task congestion: {blocked_tasks_count} blocked tasks"
        else:
            health = DepartmentHealth.HEALTHY
            reason = "Department operating within normal parameters"

        metrics = DepartmentMetrics(
            department_id=department_id,
            blocked_tasks=blocked_tasks_count,
        )

        return DepartmentHealthReport(
            department_id=department_id,
            health=health,
            reason=reason,
            downstream_blocked_count=blocked_tasks_count,
            metrics=metrics,
        )

    async def bootstrap_enterprise_departments(self) -> List[Department]:
        """Configuration-driven initialization seeding standard enterprise departments."""
        created = []
        for defn in STANDARD_ENTERPRISE_DEPARTMENTS:
            existing = await self.department_repo.get_by_id(defn["id"])
            if not existing:
                dept = await self.create_department(
                    department_id=defn["id"],
                    name=defn["name"],
                    code=defn["code"],
                    purpose=defn["purpose"],
                    capabilities=defn["capabilities"],
                )
                created.append(dept)
            else:
                created.append(existing)
        return created

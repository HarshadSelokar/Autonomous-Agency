"""Configuration loader for enterprise departments.

Provides configuration-driven definitions and seeding for enterprise operating functions.
"""

from typing import Dict, List, Any
from src.domain.department import Department, DepartmentCapability, DepartmentStatus


ENTERPRISE_DEPARTMENT_DEFINITIONS: List[Dict[str, Any]] = [
    {
        "id": "dept-exec",
        "name": "Executive / Management",
        "code": "EXEC",
        "description": "Corporate strategy, capital allocation, and executive management",
        "purpose": "Define strategic direction and oversee company execution",
        "responsibilities": ["strategic planning", "capital allocation", "executive governance"],
        "capabilities": [DepartmentCapability.OPERATIONS_PLANNING.value, DepartmentCapability.BUDGETING.value],
    },
    {
        "id": "dept-prod",
        "name": "Product",
        "code": "PROD",
        "description": "Product strategy, roadmap, requirements, and user research",
        "purpose": "Define product vision and requirements for engineering execution",
        "responsibilities": ["product roadmap", "requirements definition", "user feedback analysis"],
        "capabilities": [DepartmentCapability.MARKETING_RESEARCH.value, DepartmentCapability.ARCHITECTURE.value],
    },
    {
        "id": "dept-eng",
        "name": "Engineering",
        "code": "ENG",
        "description": "Software development, architecture, code review, and technical delivery",
        "purpose": "Build and maintain software systems and core platform infrastructure",
        "responsibilities": ["software development", "system architecture", "code review"],
        "capabilities": [
            DepartmentCapability.SOFTWARE_DEVELOPMENT.value,
            DepartmentCapability.ARCHITECTURE.value,
            DepartmentCapability.CODE_REVIEW.value,
        ],
    },
    {
        "id": "dept-qa",
        "name": "Quality Assurance",
        "code": "QA",
        "description": "Test automation, software verification, quality control, and defect tracking",
        "purpose": "Verify software quality and prevent defective deliverables",
        "responsibilities": ["test automation", "verification runs", "defect reporting"],
        "capabilities": [DepartmentCapability.TESTING.value, DepartmentCapability.CODE_REVIEW.value],
    },
    {
        "id": "dept-devops",
        "name": "DevOps & Infrastructure",
        "code": "DEVOPS",
        "description": "CI/CD pipelines, cloud infrastructure, reliability engineering, and monitoring",
        "purpose": "Deploy and maintain production infrastructure and continuous delivery pipelines",
        "responsibilities": ["deployment management", "infrastructure provisioning", "system monitoring"],
        "capabilities": [DepartmentCapability.SOFTWARE_DEVELOPMENT.value, DepartmentCapability.TESTING.value],
    },
    {
        "id": "dept-mktg",
        "name": "Marketing",
        "code": "MKTG",
        "description": "Market research, content creation, campaign management, and positioning",
        "purpose": "Drive product positioning, brand awareness, and marketing campaigns",
        "responsibilities": ["market research", "content creation", "launch campaigns"],
        "capabilities": [DepartmentCapability.MARKETING_RESEARCH.value, DepartmentCapability.CONTENT_CREATION.value, DepartmentCapability.CAMPAIGN_PLANNING.value],
    },
    {
        "id": "dept-sales",
        "name": "Sales",
        "code": "SALES",
        "description": "Lead qualification, customer proposals, pipeline management, and enterprise sales",
        "purpose": "Qualify enterprise leads and generate sales proposals",
        "responsibilities": ["lead qualification", "proposal generation", "customer communication"],
        "capabilities": [DepartmentCapability.LEAD_QUALIFICATION.value, DepartmentCapability.PROPOSAL_GENERATION.value],
    },
    {
        "id": "dept-cs",
        "name": "Customer Success & Support",
        "code": "CS",
        "description": "Customer onboarding, support ticket resolution, and customer retention",
        "purpose": "Support active customers and resolve operational support requests",
        "responsibilities": ["customer support", "user onboarding", "issue resolution"],
        "capabilities": [DepartmentCapability.CUSTOMER_SUPPORT.value],
    },
    {
        "id": "dept-fin",
        "name": "Finance",
        "code": "FIN",
        "description": "Budgeting, financial analysis, invoicing, and fiscal reporting",
        "purpose": "Manage financial planning, budgeting, and fiscal analysis",
        "responsibilities": ["budgeting", "financial analysis", "expense tracking"],
        "capabilities": [DepartmentCapability.FINANCIAL_ANALYSIS.value, DepartmentCapability.BUDGETING.value],
    },
    {
        "id": "dept-legal",
        "name": "Legal & Compliance",
        "code": "LEGAL",
        "description": "Contract review, policy compliance, risk analysis, and legal oversight",
        "purpose": "Ensure legal compliance and review external enterprise commitments",
        "responsibilities": ["contract review", "compliance auditing", "risk analysis"],
        "capabilities": [DepartmentCapability.CONTRACT_REVIEW.value, DepartmentCapability.COMPLIANCE_ANALYSIS.value],
    },
    {
        "id": "dept-hr",
        "name": "HR & People",
        "code": "HR",
        "description": "Workforce planning, talent management, onboarding, and organizational culture",
        "purpose": "Oversee workforce structure, roles, and employee framework coordination",
        "responsibilities": ["workforce planning", "employee onboarding", "role management"],
        "capabilities": [DepartmentCapability.HR_MANAGEMENT.value],
    },
    {
        "id": "dept-ops",
        "name": "Operations",
        "code": "OPS",
        "description": "Business process optimization, operational logistics, and SLA tracking",
        "purpose": "Optimize business operations and track cross-department SLAs",
        "responsibilities": ["process optimization", "SLA monitoring", "logistics tracking"],
        "capabilities": [DepartmentCapability.OPERATIONS_PLANNING.value],
    },
    {
        "id": "dept-res",
        "name": "Research & AI Development",
        "code": "RES",
        "description": "Applied AI research, algorithm evaluation, and emerging technology benchmarking",
        "purpose": "Conduct advanced AI research and benchmark emerging technologies",
        "responsibilities": ["AI research", "algorithm benchmark", "technical prototyping"],
        "capabilities": [DepartmentCapability.SOFTWARE_DEVELOPMENT.value, DepartmentCapability.ARCHITECTURE.value],
    },
]


class DepartmentConfigLoader:
    """Loads configuration-driven enterprise department definitions."""

    @staticmethod
    def load_default_departments() -> List[Department]:
        """Instantiate pure domain Department entities for all enterprise functions."""
        departments: List[Department] = []
        for defn in ENTERPRISE_DEPARTMENT_DEFINITIONS:
            dept = Department(
                id=defn["id"],
                name=defn["name"],
                code=defn["code"],
                description=defn["description"],
                purpose=defn["purpose"],
                status=DepartmentStatus.ACTIVE,
                responsibilities=defn["responsibilities"],
                capabilities=defn["capabilities"],
            )
            departments.append(dept)
        return departments

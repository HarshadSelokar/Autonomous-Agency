"""
Tenant-Aware Workforce and Resource Allocation Service (Phase 34).
"""

import logging
from typing import Any
from src.domain.employee import Employee, EmployeeStatus
from src.domain.exceptions import SecurityBoundaryViolationError, QuotaExceededError
from src.infrastructure.repositories.employee_repository import SQLAlchemyEmployeeRepository

logger = logging.getLogger(__name__)


class TenantWorkforceService:
    def __init__(self, employee_repo: SQLAlchemyEmployeeRepository | None = None) -> None:
        self.employee_repo = employee_repo
        self._employees: dict[str, list[Any]] = {}

    async def get_available_employees_for_tenant(
        self,
        tenant_id: str,
        required_capability: str | None = None,
        max_workload_threshold: float = 0.85,
    ) -> list[Employee]:
        all_employees = await self.employee_repo.list_all()
        tenant_employees = []
        for emp in all_employees:
            # Check tenant boundary (or default fallback for platform pool)
            emp_tenant = getattr(emp, "tenant_id", tenant_id)
            emp_status = getattr(emp, "status", None)
            is_active = emp_status == EmployeeStatus.ACTIVE or emp_status == "ACTIVE"
            if emp_tenant == tenant_id and is_active:
                if required_capability:
                    cap_names = [c.name if hasattr(c, "name") else str(c) for c in emp.capabilities]
                    if required_capability not in cap_names and "*" not in cap_names:
                        continue
                # Workload capacity check
                current_workload = getattr(emp, "workload", 0.0)
                if current_workload <= max_workload_threshold:
                    tenant_employees.append(emp)

        return tenant_employees

    async def allocate_employee_to_task(
        self,
        tenant_id: str,
        employee_id: str,
        task_id: str,
        estimated_workload_increment: float = 0.1,
    ) -> Employee:
        emp = await self.employee_repo.get_by_id(employee_id)
        if not emp:
            raise ValueError(f"Employee '{employee_id}' not found.")

        emp_tenant = getattr(emp, "tenant_id", tenant_id)
        if emp_tenant != tenant_id:
            raise SecurityBoundaryViolationError(
                actor_id=employee_id,
                violation_type="CROSS_TENANT_WORKFORCE_LEAKAGE",
                details=f"Employee '{employee_id}' belongs to tenant '{emp_tenant}', not requested tenant '{tenant_id}'.",
            )

        current_workload = getattr(emp, "workload", 0.0)
        new_workload = current_workload + estimated_workload_increment
        if new_workload > 1.0:
            raise QuotaExceededError(
                entity="EmployeeCapacity",
                entity_id=employee_id,
                quota_type="CONCURRENCY_WORKLOAD_LIMIT",
                requested=new_workload,
                limit=1.0,
            )

        emp.workload = new_workload
        return await self.employee_repo.save(emp)

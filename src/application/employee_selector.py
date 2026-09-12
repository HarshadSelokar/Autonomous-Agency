"""
EmployeeSelector Service.
Filtering and matching service to select eligible employees for work items based on capabilities.
"""

from src.domain.employee import Employee


class EmployeeSelector:
    def find_eligible_employees(
        self,
        employees: list[Employee],
        required_capabilities: list[str],
        require_all: bool = True,
    ) -> list[Employee]:
        """
        Identify eligible employees for work assignment.

        Criteria:
        1. Employee must be ACTIVE (emp.is_executable() == True).
        2. Employee must possess the required capabilities/skills.
        """
        eligible: list[Employee] = []

        for emp in employees:
            if not emp.is_executable():
                continue

            if not required_capabilities:
                eligible.append(emp)
                continue

            matches = [emp.possesses_capability(cap) for cap in required_capabilities]
            is_all_match = require_all and all(matches)
            is_any_match = (not require_all) and any(matches)
            if is_all_match or is_any_match:
                eligible.append(emp)

        return eligible

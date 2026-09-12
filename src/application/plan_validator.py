"""
PlanValidator Service.
Deterministically validates LLM-proposed plans against system invariants before persistence.
"""

from src.domain.exceptions import PlanValidationError
from src.domain.plan import Plan


class PlanValidator:
    def validate_proposed_plan(self, plan: Plan) -> None:
        """
        Validate an LLM-proposed Plan against strict backend business rules.
        Raises PlanValidationError if any invariant is violated.
        """
        if not plan.id:
            raise PlanValidationError("Proposed plan must have a non-empty ID.")
        if not plan.objective_id:
            raise PlanValidationError("Proposed plan must reference an objective_id.")
        if not plan.manager_id:
            raise PlanValidationError("Proposed plan must reference a manager_id.")
        if not plan.work_items:
            raise PlanValidationError("Proposed plan must contain at least one work item.")

        seen_ids: set[str] = set()
        seen_titles: set[str] = set()

        for wi in plan.work_items:
            if not wi.id:
                raise PlanValidationError("Work item in proposed plan has empty ID.")
            if wi.id in seen_ids:
                raise PlanValidationError(f"Duplicate work item ID '{wi.id}' detected in plan.")
            seen_ids.add(wi.id)

            title_lower = wi.title.strip().lower()
            if not title_lower:
                raise PlanValidationError(f"Work item '{wi.id}' has empty title.")
            if title_lower in seen_titles:
                raise PlanValidationError(
                    f"Duplicate work item title '{wi.title}' detected in proposed plan."
                )
            seen_titles.add(title_lower)

            if not wi.description.strip():
                raise PlanValidationError(
                    f"Work item '{wi.title}' ({wi.id}) must have a non-empty description."
                )
            if not wi.required_capabilities:
                raise PlanValidationError(
                    f"Work item '{wi.title}' ({wi.id}) must specify at least "
                    "one required capability."
                )

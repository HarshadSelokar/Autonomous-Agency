"""
Tenant Context Middleware and FastAPI Dependency for Phase 25.

Extracts and validates X-Company-ID, X-Environment-ID, and X-Simulation-ID headers,
instantiating a validated CompanyContext for every incoming API request.
"""

from typing import Optional
from fastapi import Header, HTTPException, Request, status

from src.domain.company import CompanyContext, CompanyRole, ExecutionEnvironment


async def get_company_context(
    x_company_id: Optional[str] = Header(None, alias="X-Company-ID"),
    x_environment_id: Optional[str] = Header("PRODUCTION", alias="X-Environment-ID"),
    x_simulation_id: Optional[str] = Header(None, alias="X-Simulation-ID"),
    x_user_id: Optional[str] = Header("SYSTEM", alias="X-User-ID"),
    x_user_role: Optional[str] = Header("ADMIN", alias="X-User-Role"),
) -> CompanyContext:
    """
    FastAPI dependency extracting and validating company tenant context.
    """
    company_id = x_company_id or "default-company"

    # Validate execution environment
    try:
        env = ExecutionEnvironment(x_environment_id.upper() if x_environment_id else "PRODUCTION")
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid execution environment '{x_environment_id}'. Must be PRODUCTION, STAGING, SANDBOX, or SIMULATION.",
        )

    # Validate role
    try:
        role = CompanyRole(x_user_role.upper() if x_user_role else "ADMIN")
    except ValueError:
        role = CompanyRole.ADMIN

    # If environment is SIMULATION, simulation_id must be provided or defaults
    if env == ExecutionEnvironment.SIMULATION and not x_simulation_id:
        x_simulation_id = "sim-default"

    return CompanyContext(
        company_id=company_id,
        user_id=x_user_id or "SYSTEM",
        role=role,
        environment=env,
        simulation_id=x_simulation_id,
    )

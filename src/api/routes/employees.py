"""
FastAPI Router for Employee Framework endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.schemas.employee_schemas import (
    CreateEmployeeRequest,
    EmployeeResponse,
    ExecuteEmployeeWorkRequest,
    UpdateEmployeeRequest,
    UpdateEmployeeStatusRequest,
)
from src.api.schemas.run_schemas import RunResponse
from src.application.employee_service import EmployeeService
from src.application.execution_engine import AgentExecutionEngine
from src.domain.employee import Employee, EmployeeStatus
from src.domain.exceptions import EmployeeNotFoundError, EmployeeValidationError
from src.infrastructure.database import get_db_session
from src.infrastructure.repositories.agent_repository import SQLAlchemyAgentRepository
from src.infrastructure.repositories.checkpoint_repository import SQLAlchemyCheckpointRepository
from src.infrastructure.repositories.department_repository import SQLAlchemyDepartmentRepository
from src.infrastructure.repositories.employee_repository import SQLAlchemyEmployeeRepository
from src.infrastructure.repositories.run_repository import SQLAlchemyAgentRunRepository
from src.infrastructure.repositories.step_repository import SQLAlchemyExecutionStepRepository

router = APIRouter(prefix="/employees", tags=["Employees"])


def get_employee_service(session: AsyncSession = Depends(get_db_session)) -> EmployeeService:
    emp_repo = SQLAlchemyEmployeeRepository(session)
    agent_repo = SQLAlchemyAgentRepository(session)
    dept_repo = SQLAlchemyDepartmentRepository(session)
    run_repo = SQLAlchemyAgentRunRepository(session)
    step_repo = SQLAlchemyExecutionStepRepository(session)
    checkpoint_repo = SQLAlchemyCheckpointRepository(session)

    execution_engine = AgentExecutionEngine(
        agent_repo=agent_repo,
        run_repo=run_repo,
        step_repo=step_repo,
        checkpoint_repo=checkpoint_repo,
    )

    return EmployeeService(
        employee_repo=emp_repo,
        agent_repo=agent_repo,
        execution_engine=execution_engine,
        department_repo=dept_repo,
    )


@router.post("", response_model=EmployeeResponse, status_code=status.HTTP_201_CREATED)
async def create_employee(
    req: CreateEmployeeRequest,
    service: EmployeeService = Depends(get_employee_service),
) -> EmployeeResponse:
    employee = Employee(
        id=req.id,
        employee_code=req.employee_code,
        name=req.name,
        title=req.title,
        role=req.role,
        agent_id=req.agent_id,
        department_id=req.department_id,
        manager_id=req.manager_id,
        status=EmployeeStatus.INACTIVE,
        responsibilities=req.responsibilities,
        skills=[s.to_domain() for s in req.skills],
        capabilities=[c.to_domain() for c in req.capabilities],
        metadata=req.metadata,
    )

    try:
        created = await service.create_employee(employee)
        return EmployeeResponse.from_domain(created)
    except EmployeeValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.get("/{employee_id}", response_model=EmployeeResponse)
async def get_employee(
    employee_id: str,
    service: EmployeeService = Depends(get_employee_service),
) -> EmployeeResponse:
    try:
        emp = await service.get_employee(employee_id)
        return EmployeeResponse.from_domain(emp)
    except EmployeeNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.get("", response_model=list[EmployeeResponse])
async def list_employees(
    service: EmployeeService = Depends(get_employee_service),
) -> list[EmployeeResponse]:
    employees = await service.list_employees()
    return [EmployeeResponse.from_domain(e) for e in employees]


@router.patch("/{employee_id}", response_model=EmployeeResponse)
async def update_employee(
    employee_id: str,
    req: UpdateEmployeeRequest,
    service: EmployeeService = Depends(get_employee_service),
) -> EmployeeResponse:
    try:
        emp = await service.get_employee(employee_id)
        if req.manager_id is not None:
            emp = await service.update_manager(employee_id, req.manager_id)
        if req.department_id is not None:
            emp = await service.update_department(employee_id, req.department_id)
        return EmployeeResponse.from_domain(emp)
    except EmployeeNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except EmployeeValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.post("/{employee_id}/status", response_model=EmployeeResponse)
async def change_employee_status(
    employee_id: str,
    req: UpdateEmployeeStatusRequest,
    service: EmployeeService = Depends(get_employee_service),
) -> EmployeeResponse:
    try:
        emp = await service.change_status(employee_id, req.status)
        return EmployeeResponse.from_domain(emp)
    except EmployeeNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except EmployeeValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        ) from e


@router.post(
    "/{employee_id}/runs",
    response_model=RunResponse,
    status_code=status.HTTP_201_CREATED,
)
async def execute_employee_work(
    employee_id: str,
    req: ExecuteEmployeeWorkRequest,
    service: EmployeeService = Depends(get_employee_service),
) -> RunResponse:
    try:
        run = await service.execute_work(
            employee_id=employee_id,
            objective=req.objective,
            task_id=req.task_id,
            response_schema=req.response_schema,
        )
        return RunResponse.from_domain(run)
    except EmployeeNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except EmployeeValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

"""
SQLAlchemy implementation of ExecutionStepRepositoryInterface.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.repository import ExecutionStepRepositoryInterface
from src.domain.step import ExecutionStep
from src.infrastructure.models.step_model import (
    ExecutionStepModel,
    step_domain_to_model,
    step_model_to_domain,
)


class SQLAlchemyExecutionStepRepository(ExecutionStepRepositoryInterface):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def save(self, step: ExecutionStep) -> ExecutionStep:
        """Save or update an ExecutionStep entity."""
        model = await self.session.get(ExecutionStepModel, step.id)
        if model is None:
            model = step_domain_to_model(step)
            self.session.add(model)
        else:
            updated_model = step_domain_to_model(step)
            model.status = updated_model.status
            model.input_data_json = updated_model.input_data_json
            model.output_data_json = updated_model.output_data_json
            model.error_message = updated_model.error_message
            model.completed_at = updated_model.completed_at
            model.metadata_json = updated_model.metadata_json

        await self.session.flush()
        return step_model_to_domain(model)

    async def list_by_run_id(self, run_id: str) -> list[ExecutionStep]:
        """List all ExecutionSteps for a specific run in order of step_number."""
        stmt = (
            select(ExecutionStepModel)
            .where(ExecutionStepModel.run_id == run_id)
            .order_by(ExecutionStepModel.step_number.asc())
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [step_model_to_domain(m) for m in models]

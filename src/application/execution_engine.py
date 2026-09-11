"""
Agent Execution Engine.
Orchestrates the entire lifecycle execution flow of an Agent run:
Load Agent -> Validate -> Create Run -> Build Context -> Resolve Provider ->
Execute Model -> Validate Output -> Persist Steps & Result -> Update States.
"""

import uuid
from typing import Any

from src.application.context import ContextBuilder
from src.application.provider_registry import ModelProviderRegistry, default_provider_registry
from src.application.structured_output import StructuredOutputValidator
from src.domain.agent import AgentState
from src.domain.exceptions import AgentNotFoundError, AgentValidationError
from src.domain.model_provider import ModelRequest
from src.domain.repository import (
    AgentRepositoryInterface,
    AgentRunRepositoryInterface,
    ExecutionStepRepositoryInterface,
)
from src.domain.run import AgentRun, RunStatus
from src.domain.step import ExecutionStep, StepType


class AgentExecutionEngine:
    def __init__(
        self,
        agent_repo: AgentRepositoryInterface,
        run_repo: AgentRunRepositoryInterface,
        step_repo: ExecutionStepRepositoryInterface,
        provider_registry: ModelProviderRegistry | None = None,
        context_builder: ContextBuilder | None = None,
        output_validator: StructuredOutputValidator | None = None,
    ) -> None:
        self.agent_repo = agent_repo
        self.run_repo = run_repo
        self.step_repo = step_repo
        self.provider_registry = provider_registry or default_provider_registry
        self.context_builder = context_builder or ContextBuilder()
        self.output_validator = output_validator or StructuredOutputValidator()

    async def execute_run(
        self,
        agent_id: str,
        objective: str,
        task_id: str | None = None,
        response_schema: dict[str, Any] | None = None,
        extra_context_items: list[Any] | None = None,
    ) -> AgentRun:
        """
        Execute a complete AgentRun pipeline for the specified agent and objective.
        """
        # 1. Load Agent
        agent = await self.agent_repo.get_by_id(agent_id)
        if agent is None:
            raise AgentNotFoundError(agent_id)

        # 2. Validate Agent State
        if not agent.can_transition_to(AgentState.READY):
            raise AgentValidationError(
                f"Agent '{agent_id}' is in state '{agent.current_state.value}' "
                "and cannot start a run."
            )

        # Transition Agent: IDLE -> READY -> RUNNING
        agent.transition_to(AgentState.READY)
        agent.current_task_id = task_id
        agent.transition_to(AgentState.RUNNING)
        await self.agent_repo.save(agent)

        # 3. Create AgentRun
        run_id = f"run_{uuid.uuid4().hex[:12]}"
        run = AgentRun(
            id=run_id,
            agent_id=agent.id,
            objective=objective,
            provider=agent.model_configuration.provider,
            model=agent.model_configuration.model,
            status=RunStatus.CREATED,
        )

        run.transition_to(RunStatus.INITIALIZING)
        await self.run_repo.save(run)

        step_counter = 1

        try:
            # STEP 1: Initialize
            step_init = ExecutionStep(
                id=f"step_{run_id}_1",
                run_id=run_id,
                step_number=step_counter,
                step_type=StepType.INITIALIZE,
                input_data={"agent_id": agent.id, "objective": objective},
            )
            await self.step_repo.save(step_init)

            run.transition_to(RunStatus.RUNNING)
            await self.run_repo.save(run)

            step_init.mark_completed({"initialized": True})
            await self.step_repo.save(step_init)

            # STEP 2: Build Context
            step_counter += 1
            step_context = ExecutionStep(
                id=f"step_{run_id}_{step_counter}",
                run_id=run_id,
                step_number=step_counter,
                step_type=StepType.BUILD_CONTEXT,
                input_data={"objective": objective},
            )
            await self.step_repo.save(step_context)

            execution_context = await self.context_builder.build(
                agent=agent,
                objective=objective,
                task_id=task_id,
                extra_items=extra_context_items,
                response_schema=response_schema,
            )
            chat_messages = execution_context.to_chat_messages()

            step_context.mark_completed({"message_count": len(chat_messages)})
            await self.step_repo.save(step_context)

            # STEP 3: Resolve Model Provider & Execute Model Call
            step_counter += 1
            step_model = ExecutionStep(
                id=f"step_{run_id}_{step_counter}",
                run_id=run_id,
                step_number=step_counter,
                step_type=StepType.MODEL_CALL,
                input_data={
                    "provider": agent.model_configuration.provider,
                    "model": agent.model_configuration.model,
                },
            )
            await self.step_repo.save(step_model)

            provider = self.provider_registry.get(agent.model_configuration.provider)
            model_request = ModelRequest(
                model=agent.model_configuration.model,
                messages=chat_messages,
                temperature=agent.model_configuration.temperature,
                max_tokens=agent.model_configuration.max_tokens,
                top_p=agent.model_configuration.top_p,
                response_schema=response_schema,
            )

            model_response = await provider.generate(model_request)

            # Update run usage with normalized usage data
            run.usage = {
                "input_tokens": model_response.usage.input_tokens,
                "output_tokens": model_response.usage.output_tokens,
                "total_tokens": model_response.usage.total_tokens,
            }
            await self.run_repo.save(run)

            step_model.mark_completed(
                {
                    "request_id": model_response.request_id,
                    "finish_reason": model_response.finish_reason,
                    "usage": run.usage,
                }
            )
            await self.step_repo.save(step_model)

            # STEP 4: Validate Response
            step_counter += 1
            step_val = ExecutionStep(
                id=f"step_{run_id}_{step_counter}",
                run_id=run_id,
                step_number=step_counter,
                step_type=StepType.VALIDATE_RESPONSE,
                input_data={"content_length": len(model_response.content)},
            )
            await self.step_repo.save(step_val)

            validated_output = self.output_validator.validate(
                content=model_response.content,
                expected_schema=response_schema,
                preparsed_output=model_response.structured_output,
            )

            step_val.mark_completed({"valid": True, "keys": list(validated_output.keys())})
            await self.step_repo.save(step_val)

            # STEP 5: Finalize
            step_counter += 1
            step_finalize = ExecutionStep(
                id=f"step_{run_id}_{step_counter}",
                run_id=run_id,
                step_number=step_counter,
                step_type=StepType.FINALIZE,
                input_data={"status": "completing"},
            )
            await self.step_repo.save(step_finalize)

            run.result = {
                "content": model_response.content,
                "structured_output": model_response.structured_output,
            }
            run.transition_to(RunStatus.COMPLETED)
            await self.run_repo.save(run)

            step_finalize.mark_completed({"status": "completed"})
            await self.step_repo.save(step_finalize)

            # Update Agent state: RUNNING -> COMPLETED -> READY
            agent.transition_to(AgentState.COMPLETED)
            agent.transition_to(AgentState.READY)
            agent.current_task_id = None
            await self.agent_repo.save(agent)

            return run

        except Exception as exc:
            # Handle engine failure gracefully
            failure_reason = str(exc)
            run.transition_to(RunStatus.FAILED, failure_reason=failure_reason)
            await self.run_repo.save(run)

            agent.transition_to(AgentState.FAILED)
            agent.transition_to(AgentState.READY)
            agent.current_task_id = None
            await self.agent_repo.save(agent)

            raise exc

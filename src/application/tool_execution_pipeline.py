"""
ToolExecutionPipeline Application Layer for Phase 8.
Orchestrates the complete 12-stage tool execution pipeline:
REQUEST -> RESOLVE -> VALIDATE -> AUTHORIZE -> POLICY -> APPROVAL -> PROVIDER -> SANDBOX -> ADAPTER -> RESULT -> EVIDENCE -> AUDIT.
"""

import time
import uuid
from typing import Any

from src.application.secrets_broker import SecretsBroker
from src.application.tool_approval_service import ToolApprovalService
from src.application.tool_policy_engine import PolicyDecision, ToolPolicyEngine
from src.application.tool_registry import ToolRegistry
from src.application.tool_resolver import ToolResolver
from src.application.workspace_authorization_service import WorkspaceAuthorizationService
from src.application.event_dispatcher import EventDispatcher
from src.domain.repository import EmployeeRepositoryInterface
from src.domain.tool import (
    ApprovalStatus,
    PermissionMode,
    ToolCapability,
    ToolCategory,
    ToolDefinition,
    ToolEvidence,
    ToolExecution,
    ToolExecutionStatus,
    ToolRequest,
    ToolResult,
    ToolValidationError,
)
from src.infrastructure.tools.executors.artifact_tool_executor import ArtifactToolExecutor
from src.infrastructure.tools.executors.base import ToolExecutorInterface
from src.infrastructure.tools.executors.browser_tool_executor import BrowserToolExecutor
from src.infrastructure.tools.executors.communication_tool_executor import CommunicationToolExecutor
from src.infrastructure.tools.executors.file_tool_executor import FileToolExecutor
from src.infrastructure.tools.executors.http_tool_executor import HTTPToolExecutor
from src.infrastructure.tools.executors.mcp_tool_adapter import MCPToolAdapter
from src.infrastructure.tools.executors.task_tool_executor import TaskToolExecutor


class ToolExecutionPipeline:
    def __init__(
        self,
        registry: ToolRegistry,
        resolver: ToolResolver | None = None,
        policy_engine: ToolPolicyEngine | None = None,
        approval_service: ToolApprovalService | None = None,
        workspace_auth_service: WorkspaceAuthorizationService | None = None,
        employee_repo: EmployeeRepositoryInterface | None = None,
        secrets_broker: SecretsBroker | None = None,
        event_dispatcher: EventDispatcher | None = None,
        execution_repo: Any | None = None,
        evidence_repo: Any | None = None,
    ) -> None:
        self.registry = registry
        self.resolver = resolver or ToolResolver(registry)
        self.policy_engine = policy_engine or ToolPolicyEngine()
        self.approval_service = approval_service or ToolApprovalService()
        self.workspace_auth_service = workspace_auth_service
        self.employee_repo = employee_repo
        self.secrets_broker = secrets_broker
        self.event_dispatcher = event_dispatcher
        self.execution_repo = execution_repo
        self.evidence_repo = evidence_repo

        # Initialize Default Adapters
        self.executors: dict[ToolCategory, ToolExecutorInterface] = {
            ToolCategory.FILESYSTEM: FileToolExecutor(),
            ToolCategory.ARTIFACT: ArtifactToolExecutor(),
            ToolCategory.TASK: TaskToolExecutor(),
            ToolCategory.COMMUNICATION: CommunicationToolExecutor(),
            ToolCategory.HTTP: HTTPToolExecutor(),
            ToolCategory.BROWSER: BrowserToolExecutor(),
            ToolCategory.INTEGRATION: MCPToolAdapter(),
        }

    async def execute_tool_request(
        self,
        request: ToolRequest,
        pre_approved_approval_id: str | None = None,
    ) -> ToolResult:
        """Execute the 12-stage tool pipeline for a ToolRequest."""
        # 1. STAGE 1: REQUEST
        exec_id = f"exec-{uuid.uuid4().hex[:8]}"
        execution = ToolExecution(
            id=exec_id,
            request_id=request.id,
            tool_id=request.tool_id,
            tool_version=request.tool_version,
            capability=request.requested_capability,
            actor_employee_id=request.employee_id,
            agent_id=request.agent_id,
            agent_run_id=request.agent_run_id,
            task_id=request.task_id,
            workspace_id=request.workspace_id,
            status=ToolExecutionStatus.REQUESTED,
        )

        # 2. STAGE 2: RESOLVE & 3. VALIDATE
        execution.transition_to(ToolExecutionStatus.VALIDATING)
        res_result = self.resolver.resolve(request)

        if not res_result.is_allowed and not res_result.requires_approval:
            execution.transition_to(ToolExecutionStatus.DENIED, failure_reason=res_result.rejection_reason)
            await self._save_execution(execution)
            return ToolResult(
                execution_id=exec_id,
                status=ToolExecutionStatus.DENIED,
                error_message=res_result.rejection_reason,
            )

        tool = res_result.tool
        if not tool:
            execution.transition_to(ToolExecutionStatus.DENIED, failure_reason="Tool resolution failed.")
            await self._save_execution(execution)
            return ToolResult(
                execution_id=exec_id,
                status=ToolExecutionStatus.DENIED,
                error_message="Tool resolution failed.",
            )

        # 4. STAGE 4: AUTHORIZE & WORKSPACE ISOLATION
        if request.workspace_id and self.workspace_auth_service:
            try:
                await self.workspace_auth_service.validate_task_workspace_access(
                    workspace_id=request.workspace_id,
                    current_task_id=request.task_id or "",
                    actor_employee_id=request.employee_id,
                )
            except Exception as auth_err:
                execution.transition_to(ToolExecutionStatus.DENIED, failure_reason=str(auth_err))
                await self._save_execution(execution)
                return ToolResult(
                    execution_id=exec_id,
                    status=ToolExecutionStatus.DENIED,
                    error_message=f"Workspace authorization failed: {auth_err}",
                )

        # 5. STAGE 5: POLICY EVALUATION
        actor_emp = None
        if self.employee_repo:
            actor_emp = await self.employee_repo.get_by_id(request.employee_id)

        policy_decision = self.policy_engine.evaluate(tool, request, actor_employee=actor_emp)

        if policy_decision == PolicyDecision.DENY:
            execution.transition_to(ToolExecutionStatus.DENIED, failure_reason="Denied by ToolPolicyEngine.")
            await self._save_execution(execution)
            return ToolResult(
                execution_id=exec_id,
                status=ToolExecutionStatus.DENIED,
                error_message="Denied by organizational tool policy engine.",
            )

        # 6. STAGE 6: APPROVAL WORKFLOW
        requires_approval = (res_result.requires_approval or policy_decision == PolicyDecision.REQUIRE_APPROVAL)
        if requires_approval and not pre_approved_approval_id:
            execution.transition_to(ToolExecutionStatus.PENDING_APPROVAL)
            approval = await self.approval_service.create_approval_request(execution, request.employee_id)
            execution.approval_id = approval.id
            await self._save_execution(execution)

            return ToolResult(
                execution_id=exec_id,
                status=ToolExecutionStatus.PENDING_APPROVAL,
                output={"approval_id": approval.id, "status": "PENDING_APPROVAL"},
                error_message="Tool execution pending managerial approval.",
            )

        if pre_approved_approval_id:
            approval = await self.approval_service._get_approval(pre_approved_approval_id)
            if not approval or approval.status != ApprovalStatus.APPROVED:
                execution.transition_to(ToolExecutionStatus.DENIED, failure_reason="Pre-approval invalid or not approved.")
                await self._save_execution(execution)
                return ToolResult(
                    execution_id=exec_id,
                    status=ToolExecutionStatus.DENIED,
                    error_message="Approval verification failed.",
                )
            execution.approval_id = approval.id

        # 7. STAGE 7: APPROVED -> STAGE 8 & 9: EXECUTION PROVIDER & SANDBOX
        execution.transition_to(ToolExecutionStatus.APPROVED)
        execution.transition_to(ToolExecutionStatus.EXECUTING)
        await self._save_execution(execution)

        executor = self.executors.get(tool.category, self.executors[ToolCategory.INTEGRATION])

        result = await executor.execute(request, tool, secrets_broker=self.secrets_broker)

        # 10. STAGE 10: RESULT & STAGE 11: EVIDENCE
        if result.status == ToolExecutionStatus.SUCCEEDED:
            execution.transition_to(ToolExecutionStatus.SUCCEEDED)
        else:
            execution.transition_to(ToolExecutionStatus.FAILED, failure_reason=result.error_message)

        execution.execution_time_ms = result.execution_time_ms
        await self._save_execution(execution)

        # Create ToolEvidence
        evidence_id = f"evid-{uuid.uuid4().hex[:8]}"
        evidence = ToolEvidence(
            id=evidence_id,
            execution_id=exec_id,
            tool_id=tool.id,
            capability=request.requested_capability,
            actor_employee_id=request.employee_id,
            agent_id=request.agent_id,
            agent_run_id=request.agent_run_id,
            task_id=request.task_id,
            workspace_id=request.workspace_id,
            status=execution.status,
            approval_id=execution.approval_id,
        )
        await self._save_evidence(evidence)
        result.evidence_id = evidence_id

        # 12. STAGE 12: AUDIT / REDACTION
        if self.secrets_broker:
            result.output = self.secrets_broker.redact(result.output)
            if result.error_message:
                result.error_message = self.secrets_broker.redact(result.error_message)

        return result

    async def _save_execution(self, execution: ToolExecution) -> None:
        if self.execution_repo:
            await self.execution_repo.save(execution)

    async def _save_evidence(self, evidence: ToolEvidence) -> None:
        if self.evidence_repo:
            await self.evidence_repo.save(evidence)

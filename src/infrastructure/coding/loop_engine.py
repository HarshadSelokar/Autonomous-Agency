"""
Loop engine: runs a task with our own agent loop and coding tools against a model provider.
"""

from collections.abc import Callable

from src.application.agent_engine import AgentTask
from src.application.agent_loop import AgentLoop, AgentLoopResult, EventSink
from src.infrastructure.coding.command_runner import CommandRunner
from src.infrastructure.coding.toolbox import ALL_TOOLS, READ_ONLY_TOOLS, CodingToolbox
from src.infrastructure.coding.workspace import ProjectWorkspace
from src.infrastructure.config import settings


class LoopEngine:
    def __init__(self, agent_loop: AgentLoop | None = None, runner: CommandRunner | None = None) -> None:
        self.agent_loop = agent_loop or AgentLoop(max_steps=settings.STUDIO_MAX_AGENT_STEPS)
        self.runner = runner or CommandRunner()

    async def run(
        self,
        task: AgentTask,
        *,
        provider: str,
        model: str,
        on_event: EventSink | None = None,
        should_cancel: Callable[[], bool] | None = None,
    ) -> AgentLoopResult:
        toolbox = CodingToolbox(
            ProjectWorkspace(task.workspace_root),
            self.runner,
            allowed_tools=READ_ONLY_TOOLS if task.read_only else ALL_TOOLS,
        )
        return await self.agent_loop.run(
            provider=provider,
            model=model,
            system_prompt=task.system_prompt,
            user_prompt=task.user_prompt,
            toolbox=toolbox,
            on_event=on_event,
            should_cancel=should_cancel,
            final_tool=task.final_tool,
        )

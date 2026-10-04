"""
Agent engines: interchangeable ways for a team member to carry out one piece of work.

    loop  our own think -> tool -> observe loop against a model provider (API key)
    agy   the Antigravity CLI, which is a complete coding agent on a subscription login

The orchestrator hands an engine a task and gets back the same AgentLoopResult either way.
"""

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from src.application.agent_loop import AgentLoopResult, EventSink


@dataclass
class AgentTask:
    system_prompt: str
    user_prompt: str
    workspace_root: Path
    # Read-only roles (manager, reviewer) must not change the working tree
    read_only: bool = False
    # Tool spec whose arguments are the structured answer the role must end with
    final_tool: dict[str, Any] | None = None


class AgentEngine(Protocol):
    async def run(
        self,
        task: AgentTask,
        *,
        provider: str,
        model: str,
        on_event: EventSink | None = None,
        should_cancel: Callable[[], bool] | None = None,
    ) -> AgentLoopResult: ...

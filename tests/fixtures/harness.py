"""Reusable test harness and scripted simulation engine for agent execution."""

import asyncio
from collections.abc import Callable
from pathlib import Path
from typing import Any

from src.application.agent_engine import AgentTask
from src.application.agent_loop import AgentLoopResult

DevelopHandler = Callable[[AgentTask, int], Any]
ReviewHandler = Callable[[AgentTask], dict[str, Any]]


class ScriptedTeamHarness:
    """
    Deterministic agent engine harness that scripts the planning, development, and
    review steps for testing multi-agent workflows without calling an external LLM.
    """

    def __init__(
        self,
        tickets: list[dict[str, Any]] | None = None,
        develop: DevelopHandler | None = None,
        review: ReviewHandler | None = None,
    ) -> None:
        self.tickets = tickets or [
            {"title": "task-one", "description": "do task one", "acceptance_criteria": "pass", "depends_on": []}
        ]
        self.develop = develop or (lambda task, attempt: None)
        self.review = review or (lambda task: {"approved": True, "feedback": "Looks good."})
        self.developer_briefs: list[str] = []
        self.review_briefs: list[str] = []
        self.attempts: dict[str, int] = {}

    async def run(
        self,
        task: AgentTask,
        *,
        provider: Any = None,
        model: Any = None,
        on_event: Any = None,
        should_cancel: Any = None,
    ) -> AgentLoopResult:
        final_tool_name = task.final_tool["name"] if task.final_tool else None

        # 1. Manager Planning
        if final_tool_name == "submit_plan":
            return AgentLoopResult(
                final_text="",
                stop_reason="completed",
                final_payload={"summary": "Automated Plan", "tickets": self.tickets},
            )

        # 2. Reviewer Decision
        if final_tool_name == "submit_review":
            self.review_briefs.append(task.user_prompt)
            return AgentLoopResult(
                final_text="",
                stop_reason="completed",
                final_payload=self.review(task),
            )

        # 3. Read-only QA or Manager question
        if task.read_only:
            return AgentLoopResult(final_text="Task verified.", stop_reason="completed")

        # 4. Developer Ticket Work
        self.developer_briefs.append(task.user_prompt)
        title = "ticket"
        if "Your ticket: " in task.user_prompt:
            title = task.user_prompt.split("Your ticket: ", 1)[1].split("\n", 1)[0]
        self.attempts[title] = self.attempts.get(title, 0) + 1

        outcome = self.develop(task, self.attempts[title])
        if asyncio.iscoroutine(outcome):
            outcome = await outcome

        if isinstance(outcome, AgentLoopResult):
            return outcome

        return AgentLoopResult(
            final_text="Ticket completed.",
            stop_reason="completed",
            usage={"total_tokens": 50},
        )


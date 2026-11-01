"""
Run a Software Studio project from the command line, without the API or a database.

    python -m scripts.run_studio_project "Add a /health endpoint with a test" --repo path/to/repo
    python -m scripts.run_studio_project "Build a CLI todo app in Python with tests" --test "python -m pytest -q"

The source repository is cloned into scratch/studio/<project-id>; the original is not
modified. The team's commits land on the branch agency/<project-id> in that clone.
"""

import argparse
import asyncio
import sys
import uuid

from src.application.dev_team_service import DevTeamOrchestrator, InMemoryDevProjectStore
from src.application.provider_registry import default_provider_registry
from src.domain.dev_project import ActivityEvent, DevProject, default_team
from src.infrastructure.config import settings
from src.infrastructure.providers.groq_provider import GroqModelProvider
from src.infrastructure.providers.openai_compatible_provider import OpenAICompatibleModelProvider


async def print_activity(event: ActivityEvent) -> None:
    print(f"[{event.actor_name:<5} {event.actor_role:<9}] {event.summary}", flush=True)


async def main() -> int:
    # Model output is Unicode; a legacy Windows console code page would crash on print
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("goal", help="What the team should build or change")
    parser.add_argument("--repo", help="Path to a local git repository to clone and work on")
    parser.add_argument("--repo-url", help="https:// URL of a git repository to clone and work on")
    parser.add_argument("--test", dest="test_command", help='Test command, e.g. "python -m pytest -q"')
    parser.add_argument("--engine", default=settings.STUDIO_ENGINE, choices=["loop", "agy"],
                        help="loop = API-key provider, agy = Antigravity CLI")
    parser.add_argument("--developers", type=int, default=settings.STUDIO_DEVELOPERS,
                        help="Developers working in parallel")
    parser.add_argument("--provider", default=settings.STUDIO_PROVIDER, help="groq or openai (loop engine)")
    parser.add_argument("--model", default="", help="One model for every role (engine defaults if empty)")
    args = parser.parse_args()

    default_provider_registry.register(GroqModelProvider())
    default_provider_registry.register(OpenAICompatibleModelProvider())

    store = InMemoryDevProjectStore()
    project = DevProject(
        id=f"prj-{uuid.uuid4().hex[:12]}",
        name=args.goal[:60],
        goal=args.goal,
        repo_url=args.repo_url,
        local_path=args.repo,
        test_command=args.test_command,
        engine=args.engine,
        provider=args.provider,
        model=args.model or (settings.STUDIO_MODEL if args.engine == "loop" else ""),
    )
    project.set_team(default_team(project.id, args.developers))
    await store.save_project(project)

    result = await DevTeamOrchestrator(store=store, on_activity=print_activity).run_project(project.id)

    print(f"\nStatus:    {result.status.value}")
    if result.failure_reason:
        print(f"Reason:    {result.failure_reason}")
    print(f"Summary:   {result.summary}")
    print(f"Workspace: {result.workspace_path}")
    print(f"Branch:    {result.branch}")
    print(f"Tokens:    {result.usage.get('total_tokens', 0)}")
    for ticket in await store.list_tickets(project.id):
        print(f"  [{ticket.status.value:<11}] {ticket.title} (attempts: {ticket.attempts})")
    return 0 if result.status.value == "COMPLETED" else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))

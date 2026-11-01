"""Command-line runner for the Agent Benchmark & Evaluation Harness."""

import argparse
import asyncio
import json
import sys
from pathlib import Path

from src.application.benchmark_service import BenchmarkHarness
from src.domain.benchmark import BenchmarkTask


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run evaluation benchmarks against the Autonomous Agency Software Studio."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--task",
        type=Path,
        help="Path to a single benchmark task JSON file.",
    )
    group.add_argument(
        "--tasks-dir",
        type=Path,
        help="Directory containing benchmark task JSON files.",
    )

    parser.add_argument(
        "--engine",
        default="loop",
        choices=["loop", "agy"],
        help="Agent engine to evaluate ('loop' or 'agy'). Default: 'loop'.",
    )
    parser.add_argument(
        "--model",
        default="",
        help="Specific model name (e.g. gpt-4o, llama-3.3-70b-versatile, gemini-3.8-flash-high).",
    )
    parser.add_argument(
        "--developers",
        type=int,
        default=2,
        help="Number of concurrent developers. Default: 2.",
    )
    parser.add_argument(
        "--runner-mode",
        default="local",
        choices=["local", "docker"],
        help="Execution runner mode: 'local' or 'docker'. Default: 'local'.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Path to write the scorecard report (JSON or Markdown based on extension).",
    )
    parser.add_argument(
        "--suite-name",
        default="Standard Benchmark Suite",
        help="Display name for the benchmark suite.",
    )
    parser.add_argument(
        "--no-clean",
        action="store_true",
        help="Keep temporary benchmark workspaces for inspection.",
    )
    return parser.parse_args()


async def main() -> int:
    args = parse_args()
    harness = BenchmarkHarness(runner_mode=args.runner_mode, clean_after=not args.no_clean)

    tasks: list[BenchmarkTask] = []
    if args.task:
        if not args.task.is_file():
            print(f"Error: Task file not found: {args.task}", file=sys.stderr)
            return 1
        tasks = [harness.load_task_from_file(args.task)]
    elif args.tasks_dir:
        if not args.tasks_dir.is_dir():
            print(f"Error: Tasks directory not found: {args.tasks_dir}", file=sys.stderr)
            return 1
        tasks = harness.load_tasks_from_dir(args.tasks_dir)

    if not tasks:
        print("No benchmark tasks found to execute.", file=sys.stderr)
        return 1

    print(f"Loaded {len(tasks)} benchmark task(s). Starting execution with engine='{args.engine}'...")

    suite_result = await harness.run_suite(
        suite_name=args.suite_name,
        tasks=tasks,
        engine=args.engine,
        model=args.model,
        developers=args.developers,
    )

    markdown_report = suite_result.to_markdown_report()
    print("\n" + markdown_report)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        if args.output.suffix.lower() == ".json":
            args.output.write_text(json.dumps(suite_result.to_dict(), indent=2), encoding="utf-8")
        else:
            args.output.write_text(markdown_report, encoding="utf-8")
        print(f"Scorecard saved to: {args.output}")

    return 0 if suite_result.passed_tasks == suite_result.total_tasks else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))


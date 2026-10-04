"""
Stand-in for the Antigravity CLI in tests. It checks it was invoked the way AgyEngine
promises, then replays a scenario as the same NDJSON event stream the real CLI prints.

The scenario comes from the FAKE_AGY_SCENARIO environment variable.
"""

import json
import os
import sys
import time
from pathlib import Path


def emit(event: dict) -> None:
    print(json.dumps(event), flush=True)


def step(index: int, state: str, tool: str, parameters: dict, error: str | None = None) -> None:
    info: dict = {"name": tool, "parameters": parameters}
    if error:
        info["error"] = {"type": "TOOL_ERROR", "message": error}
    emit({"event": "step_update", "step_update": {"step_index": index, "state": state, "step_type": "tool", "tool_name": tool, "tool_info": info}})


def flag(name: str) -> str | None:
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else None


def main() -> int:
    scenario = os.environ.get("FAKE_AGY_SCENARIO", "edit")
    prompt = next(a for a in sys.argv[1:] if a.startswith("-p="))
    brief_path = Path(prompt.split("Read the file ", 1)[1].split(" and carry out", 1)[0])
    brief = brief_path.read_text(encoding="utf-8")
    cwd = Path.cwd()
    model = flag("--model") or ""

    # Record how we were called so the test can assert on it
    (Path(os.environ["FAKE_AGY_RECORD"])).write_text(
        json.dumps({"argv": sys.argv[1:], "brief": brief, "cwd": str(cwd), "env_has_secret": "GROQ_API_KEY" in os.environ}),
        encoding="utf-8",
    )

    emit({"event": "init", "init": {"model": model, "cwd": str(cwd)}})
    usage = {"input_tokens": 100, "output_tokens": 20, "total_tokens": 120}
    result = {"status": "SUCCESS", "response": "", "usage": usage}

    if scenario == "edit":
        target = cwd / "feature.py"
        step(0, "ACTIVE", "view_file", {"AbsolutePath": str(brief_path)})
        step(0, "DONE", "view_file", {"AbsolutePath": str(brief_path)})
        step(1, "ACTIVE", "view_file", {"AbsolutePath": str(cwd / "README.md")})
        step(1, "DONE", "view_file", {"AbsolutePath": str(cwd / "README.md")})
        step(2, "ACTIVE", "write_to_file", {"TargetFile": str(target)})
        target.write_text("VALUE = 1\n", encoding="utf-8")
        step(2, "DONE", "write_to_file", {"TargetFile": str(target)})
        result["response"] = "Added feature.py."
    elif scenario == "denied_command":
        target = cwd / "feature.py"
        step(1, "ACTIVE", "write_to_file", {"TargetFile": str(target)})
        target.write_text("VALUE = 1\n", encoding="utf-8")
        step(1, "DONE", "write_to_file", {"TargetFile": str(target)})
        step(2, "ACTIVE", "run_command", {"CommandLine": "pytest -q"})
        step(2, "ERROR", "run_command", {"CommandLine": "pytest -q"}, "permission check failed")
        result["denied_actions"] = [{"action": "command", "display_name": "RunCommand"}]
    elif scenario == "structured":
        result["response"] = "done"
        result["structured_output"] = {"approved": True, "feedback": "Looks right.", "toolAction": "Finishing task"}
    elif scenario == "quota_then_ok":
        if model != "fallback-model":
            emit({"event": "result", "result": {"status": "ERROR", "response": "", "error": "RESOURCE_EXHAUSTED: quota exceeded for model", "usage": {}}})
            return 1
        result["response"] = f"answered by {model}"
    elif scenario == "network_then_ok":
        counter = Path(os.environ["FAKE_AGY_RECORD"]).with_suffix(".count")
        seen = int(counter.read_text()) if counter.exists() else 0
        counter.write_text(str(seen + 1))
        if seen < 2:
            message = (
                'API error (attempt 1): request failed: Post "https://example.invalid/v1": write tcp '
                "10.0.0.2:64732->10.0.0.1:443: wsasend: An existing connection was forcibly closed by the remote host."
            )
            emit({"event": "result", "result": {"status": "ERROR", "response": "", "error": message, "usage": {}}})
            return 1
        result["response"] = f"answered after {seen} dropped connections"
    elif scenario == "error":
        emit({"event": "result", "result": {"status": "ERROR", "response": "", "error": "something broke", "usage": {}}})
        return 1
    elif scenario == "crash":
        print("fatal: not signed in", file=sys.stderr)
        return 3
    elif scenario == "hang":
        step(1, "ACTIVE", "view_file", {"AbsolutePath": str(cwd / "README.md")})
        time.sleep(60)
    elif scenario == "outside":
        step(1, "ACTIVE", "write_to_file", {"TargetFile": str(cwd.parent / "elsewhere.txt")})
        step(1, "DONE", "write_to_file", {"TargetFile": str(cwd.parent / "elsewhere.txt")})
        result["response"] = "wrote"

    emit({"event": "result", "result": result})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

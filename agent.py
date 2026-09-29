"""
TOOLS
The agent can list repository files, read files, replace complete files, apply
small exact-text patches, and run the provided tests.

LOOP
On each turn the model chooses one tool action. The tool result is added to the
conversation so the next turn can inspect more context, edit code, or test it.

FAILURE HANDLING
Invalid JSON, unknown actions, and tool errors are returned to the model as
feedback. The model may use a later turn to correct the mistake.

STOPPING
The agent stops when tests pass, the model explicitly finishes, or the runtime's
five-model-call limit is reached.
"""

from __future__ import annotations

import json
from typing import Any


SYSTEM_PROMPT = """
You are an expert Python engineer fixing a bug in pytest.
The task, visible test, and target source file are already provided in the prompt.
Your primary action on turn 1 must be `patch_file` (or `write_file`) with the minimal correct fix.
Do NOT re-read the target file or test file. Tests are run automatically after editing.

Available actions:
{"action":"patch_file","path":"src/...","replacements":[{"old":"exact existing code","new":"replacement code"}]}
{"action":"write_file","path":"src/...","content":"full file"}
{"action":"read_file","path":"..."}
{"action":"finish","summary":"summary"}

Rules:
- For `patch_file`, `old` MUST match the existing source code character-for-character including indentation.
- Include 1-3 lines of surrounding context in `old` to guarantee uniqueness.
- Never edit test files. Write general, clean fixes that preserve existing functionality.
""".strip()


def parse_action(response: str) -> dict[str, Any]:
    text = response.strip()
    if text.startswith("```"):
        text = text.removeprefix("```json").removeprefix("```")
        text = text.removesuffix("```").strip()
    value = json.loads(text)
    if not isinstance(value, dict) or not isinstance(value.get("action"), str):
        raise ValueError("Expected a JSON object containing an action")
    return value


def execute_action(action: dict[str, Any], tools: Any) -> str:
    name = action["action"]
    if name == "list_files":
        return tools.list_files()
    if name == "read_file":
        return tools.read_file(str(action.get("path", "")))
    if name == "write_file":
        return tools.write_file(
            str(action.get("path", "")),
            str(action.get("content", "")),
        )
    if name == "patch_file":
        replacements = action.get("replacements")
        if not isinstance(replacements, list):
            raise ValueError("patch_file requires a replacements list")
        return tools.patch_file(str(action.get("path", "")), replacements)
    if name == "run_tests":
        return tools.run_tests()
    if name == "finish":
        return str(action.get("summary", "Finished"))
    raise ValueError(f"Unknown action: {name}")


def solve(task: str, tools: Any, llm: Any) -> str:
    test_content = ""
    try:
        test_content = tools.read_file("tests/test_task.py")
    except Exception:
        pass

    target_path = None
    source_content = ""
    import re
    match = re.search(r"src/[a-zA-Z0-9_/]+\.py", task)
    if match:
        target_path = match.group(0)
        try:
            source_content = tools.read_file(target_path)
        except Exception:
            pass

    user_content = task
    if test_content:
        user_content += f"\n\nVisible test (tests/test_task.py):\n```python\n{test_content}\n```"
    if target_path and source_content:
        user_content += f"\n\nSource code ({target_path}):\n```python\n{source_content}\n```"

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]

    for _ in range(5):
        response = llm.ask(messages)
        messages.append({"role": "assistant", "content": response})
        try:
            action = parse_action(response)
            if action["action"] == "finish":
                return str(action.get("summary", "Finished"))
            result = execute_action(action, tools)
            if action["action"] == "run_tests":
                if result.startswith("Exit code: 0"):
                    return "Implemented the fix and tests pass"
            elif action["action"] in ("patch_file", "write_file"):
                test_output = tools.run_tests()
                if test_output.startswith("Exit code: 0"):
                    return "Implemented the fix and tests pass"
                result += f"\nAutomatic test run failed:\n{test_output}"
        except Exception as error:
            result = f"ACTION_ERROR: {type(error).__name__}: {error}"
        messages.append({"role": "user", "content": f"Tool result:\n{result}"})

    return "Model-call limit reached"

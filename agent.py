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
You are a coding agent working inside a large Python repository.

Solve the user's task by inspecting files, making a focused source-code change,
and running tests. Return exactly one JSON object on every turn.

Available actions:
{"action":"list_files"}
{"action":"read_file","path":"relative/path.py"}
{"action":"write_file","path":"relative/path.py","content":"complete file"}
{"action":"patch_file","path":"relative/path.py","replacements":[{"old":"exact existing text","new":"replacement text"}]}
{"action":"run_tests"}
{"action":"finish","summary":"what happened"}

`patch_file` is preferred for large files. Each replacement may include an
optional 1-based `occurrence` when its old text appears more than once.

Rules:
- Paths explicitly named in the task may be read directly without listing files.
- Inspect the visible test and relevant implementation before editing.
- Make the smallest correct change and never edit tests.
- Anticipate hidden regression tests instead of overfitting the visible test.
- Run tests after editing.
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
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": task},
    ]

    for _ in range(5):
        response = llm.ask(messages)
        messages.append({"role": "assistant", "content": response})
        try:
            action = parse_action(response)
            if action["action"] == "finish":
                return str(action.get("summary", "Finished"))
            result = execute_action(action, tools)
            if action["action"] == "run_tests" and result.startswith("Exit code: 0"):
                return "Implemented the fix and tests pass"
        except Exception as error:
            result = f"ACTION_ERROR: {type(error).__name__}: {error}"
        messages.append({"role": "user", "content": f"Tool result:\n{result}"})

    return "Model-call limit reached"

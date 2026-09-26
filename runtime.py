from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from openai import OpenAI


MODEL = "stealth/space-bunny-alpha"
MAX_FILE_BYTES = 50_000
MAX_TOOL_OUTPUT = 40_000


class OpenRouterLLM:
    def __init__(self, max_calls: int = 5) -> None:
        api_key = os.environ.get("OPENROUTER_API_KEY")
        if not api_key:
            raise RuntimeError("Set OPENROUTER_API_KEY before running the agent")
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
            timeout=45.0,
            max_retries=1,
        )
        self.max_calls = max_calls
        self.call_count = 0

    def ask(self, messages: list[dict[str, str]]) -> str:
        if self.call_count >= self.max_calls:
            raise RuntimeError("Model-call limit reached")
        self.call_count += 1
        response = self.client.chat.completions.create(
            model=MODEL,
            messages=messages,
            temperature=0.0,
            max_tokens=4_000,
            response_format={"type": "json_object"},
        )
        return response.choices[0].message.content or "{}"


class WorkspaceTools:
    def __init__(self, root: Path, max_tool_calls: int = 12) -> None:
        self.root = root.resolve()
        self.max_tool_calls = max_tool_calls
        self.tool_call_count = 0

    def _count(self) -> None:
        self.tool_call_count += 1
        if self.tool_call_count > self.max_tool_calls:
            raise RuntimeError("Tool-call limit reached")

    def _path(self, relative: str) -> Path:
        if not relative or Path(relative).is_absolute():
            raise ValueError("A non-empty repository-relative path is required")
        resolved = (self.root / relative).resolve()
        if resolved != self.root and self.root not in resolved.parents:
            raise ValueError("Path escapes the repository")
        return resolved

    @staticmethod
    def _limit(value: str) -> str:
        if len(value) <= MAX_TOOL_OUTPUT:
            return value
        return value[:MAX_TOOL_OUTPUT] + "\n... output truncated ..."

    def list_files(self) -> str:
        self._count()
        files = [
            str(path.relative_to(self.root))
            for path in self.root.rglob("*")
            if path.is_file() and "__pycache__" not in path.parts and ".git" not in path.parts
        ]

        def priority(path: str) -> tuple[int, str]:
            if path.startswith("tests/"):
                return (0, path)
            if path.startswith("src/"):
                return (1, path)
            if "/tests/" in f"/{path}":
                return (2, path)
            return (3, path)

        return self._limit("\n".join(sorted(files, key=priority)))

    def read_file(self, relative: str) -> str:
        self._count()
        path = self._path(relative)
        if not path.is_file():
            raise FileNotFoundError(relative)
        content = path.read_text(encoding="utf-8")
        if len(content) <= MAX_TOOL_OUTPUT:
            return content
        half = MAX_TOOL_OUTPUT // 2
        return (
            content[:half]
            + "\n... middle of file omitted ...\n"
            + content[-half:]
        )

    def write_file(self, relative: str, content: str) -> str:
        self._count()
        path = self._path(relative)
        if "tests" in path.relative_to(self.root).parts:
            raise PermissionError("Test files are read-only")
        encoded = content.encode("utf-8")
        if len(encoded) > MAX_FILE_BYTES:
            raise ValueError(f"File exceeds {MAX_FILE_BYTES} bytes")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(encoded)
        return f"Wrote {relative} ({len(encoded)} bytes)"

    def patch_file(self, relative: str, replacements: list[dict[str, Any]]) -> str:
        self._count()
        path = self._path(relative)
        if "tests" in path.relative_to(self.root).parts:
            raise PermissionError("Test files are read-only")
        if not path.is_file():
            raise FileNotFoundError(relative)
        if not replacements or len(replacements) > 8:
            raise ValueError("Provide between 1 and 8 replacements")
        content = path.read_text(encoding="utf-8")
        for replacement in replacements:
            old = replacement.get("old")
            new = replacement.get("new")
            occurrence = replacement.get("occurrence", 1)
            if not isinstance(old, str) or not old:
                raise ValueError("Replacement old text must be non-empty")
            if not isinstance(new, str) or not isinstance(occurrence, int) or occurrence < 1:
                raise ValueError("Replacement new text or occurrence is invalid")
            starts = [match.start() for match in re.finditer(re.escape(old), content)]
            if not starts:
                raise ValueError("Replacement old text was not found")
            if len(starts) > 1 and "occurrence" not in replacement:
                raise ValueError(f"Replacement is ambiguous ({len(starts)} matches)")
            if occurrence > len(starts):
                raise ValueError(f"Replacement occurrence {occurrence} is unavailable")
            start = starts[occurrence - 1]
            content = content[:start] + new + content[start + len(old) :]
        path.write_text(content, encoding="utf-8")
        return f"Patched {relative} ({len(replacements)} replacements)"

    def run_tests(self) -> str:
        self._count()
        return self._limit(run_repository_tests(self.root))


def run_repository_tests(root: Path, tests_directory: str = "tests") -> str:
    completed = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", tests_directory, "-v"],
        cwd=root,
        capture_output=True,
        text=True,
        timeout=20,
        env={"PATH": os.environ.get("PATH", ""), "PYTHONPATH": str(root)},
    )
    output = completed.stdout + completed.stderr
    if len(output) > MAX_TOOL_OUTPUT:
        output = output[:MAX_TOOL_OUTPUT] + "\n... output truncated ..."
    return f"Exit code: {completed.returncode}\n{output}"


def run_external_test(root: Path, test_file: Path) -> str:
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "unittest",
            "discover",
            "-s",
            str(test_file.parent),
            "-p",
            test_file.name,
            "-v",
        ],
        cwd=root,
        capture_output=True,
        text=True,
        timeout=20,
        env={"PATH": os.environ.get("PATH", ""), "PYTHONPATH": str(root)},
    )
    output = completed.stdout + completed.stderr
    if len(output) > MAX_TOOL_OUTPUT:
        output = output[:MAX_TOOL_OUTPUT] + "\n... output truncated ..."
    return f"Exit code: {completed.returncode}\n{output}"


def copy_workspace(source: Path) -> tuple[tempfile.TemporaryDirectory[str], Path]:
    temporary = tempfile.TemporaryDirectory(prefix="code-agent-")
    destination = Path(temporary.name) / "repo"
    shutil.copytree(source, destination)
    return temporary, destination


def load_agent(agent_path: Path) -> Any:
    import importlib.util

    specification = importlib.util.spec_from_file_location("candidate_agent", agent_path)
    if not specification or not specification.loader:
        raise RuntimeError("Could not load agent.py")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    if not callable(getattr(module, "solve", None)):
        raise RuntimeError("agent.py must export solve(task, tools, llm)")
    return module

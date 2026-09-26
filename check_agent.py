from __future__ import annotations

import argparse
import ast
from pathlib import Path


REQUIRED_SECTIONS = ("TOOLS", "LOOP", "FAILURE HANDLING", "STOPPING")
MAX_AGENT_BYTES = 20_000
MAX_AGENT_LINES = 280
FORBIDDEN_IMPORTS = {
    "ctypes",
    "http",
    "importlib",
    "multiprocessing",
    "os",
    "pathlib",
    "requests",
    "shutil",
    "socket",
    "subprocess",
    "tempfile",
    "urllib",
}
FORBIDDEN_CALLS = {"__import__", "compile", "eval", "exec", "input", "open"}


def validate_agent(agent_path: Path) -> list[str]:
    errors: list[str] = []
    if not agent_path.is_file():
        return [f"File not found: {agent_path}"]
    if agent_path.name != "agent.py":
        errors.append("The submitted file must be named agent.py")
    if agent_path.stat().st_size > MAX_AGENT_BYTES:
        errors.append("agent.py must be 20 KB or smaller")

    try:
        source = agent_path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(agent_path))
    except (UnicodeDecodeError, SyntaxError) as error:
        return errors + [f"Invalid Python file: {error}"]

    if len(source.splitlines()) > MAX_AGENT_LINES:
        errors.append("agent.py must be 280 lines or fewer")

    docstring = ast.get_docstring(tree, clean=False) or ""
    if not docstring:
        errors.append("Add the required architecture explanation as the module docstring")
    else:
        upper_docstring = docstring.upper()
        for section in REQUIRED_SECTIONS:
            if section not in upper_docstring:
                errors.append(f"Architecture docstring is missing the {section} section")
        if len(docstring.split()) > 300:
            errors.append("Architecture docstring must be at most 300 words")

    solve_functions = [
        node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "solve"
    ]
    if not solve_functions:
        errors.append("agent.py must export solve(task, tools, llm)")
    elif len(solve_functions[0].args.args) != 3:
        errors.append("solve must accept exactly three positional arguments: task, tools, llm")

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules = [alias.name.split(".", 1)[0] for alias in node.names]
            blocked = sorted(set(modules) & FORBIDDEN_IMPORTS)
            if blocked:
                errors.append(f"Forbidden import: {', '.join(blocked)}")
        elif isinstance(node, ast.ImportFrom) and node.module:
            module = node.module.split(".", 1)[0]
            if module in FORBIDDEN_IMPORTS:
                errors.append(f"Forbidden import: {module}")
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id in FORBIDDEN_CALLS:
                errors.append(f"Forbidden call: {node.func.id}()")

    return list(dict.fromkeys(errors))


def main() -> int:
    parser = argparse.ArgumentParser(description="Check an agent.py submission")
    parser.add_argument("agent", nargs="?", default="agent.py")
    agent_path = Path(parser.parse_args().agent).resolve()
    errors = validate_agent(agent_path)
    if errors:
        print("INVALID agent.py")
        for error in errors:
            print(f"- {error}")
        return 1
    print("VALID agent.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

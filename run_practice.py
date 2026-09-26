from __future__ import annotations

import argparse
from pathlib import Path
import shutil

from runtime import (
    OpenRouterLLM,
    WorkspaceTools,
    copy_workspace,
    load_agent,
    run_external_test,
    run_repository_tests,
)


ROOT = Path(__file__).parent
PRACTICE_ROOT = ROOT / "practice-cases"
PRACTICE_REPO = ROOT / "practice-repo"


def run_case(case_name: str, agent_path: Path) -> bool:
    case_directory = PRACTICE_ROOT / case_name
    if not (case_directory / "task.txt").is_file():
        raise SystemExit(f"Unknown practice case: {case_name}")

    task = (case_directory / "task.txt").read_text(encoding="utf-8").strip()
    visible_test = case_directory / "visible_test.py"
    if not visible_test.is_file():
        raise SystemExit(f"Missing visible test for practice case: {case_name}")

    temporary, workspace_path = copy_workspace(PRACTICE_REPO)
    try:
        tests_directory = workspace_path / "tests"
        tests_directory.mkdir()
        (tests_directory / "__init__.py").write_text("", encoding="utf-8")
        shutil.copy2(visible_test, tests_directory / "test_task.py")
        agent = load_agent(agent_path)
        tools = WorkspaceTools(workspace_path)
        llm = OpenRouterLLM()
        try:
            summary = agent.solve(task, tools, llm)
        except Exception as error:
            summary = f"AGENT_ERROR: {type(error).__name__}: {error}"
        final_tests = run_repository_tests(workspace_path)
        evaluation_file = case_directory / "evaluation_test.py"
        evaluation_tests = (
            run_external_test(workspace_path, evaluation_file)
            if evaluation_file.is_file()
            else None
        )

        print(f"\n=== PRACTICE CASE: {case_name} ===")
        print("\n=== AGENT SUMMARY ===")
        print(summary)
        print("\n=== INCLUDED TESTS ===")
        print(final_tests)
        if evaluation_tests is not None:
            print("\n=== PRIVATE EVALUATION TEST ===")
            print(evaluation_tests)
        print(f"\nModel calls: {llm.call_count}")
        print(f"Tool calls: {tools.tool_call_count}")
        passed = final_tests.startswith("Exit code: 0") and (
            evaluation_tests is None or evaluation_tests.startswith("Exit code: 0")
        )
        print(f"Result: {'PASS' if passed else 'FAIL'}")
        return passed
    finally:
        temporary.cleanup()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--agent", default="agent.py")
    parser.add_argument("--case", default="01_pytest_monkeypatch")
    parser.add_argument("--all", action="store_true")
    arguments = parser.parse_args()

    agent_path = (ROOT / arguments.agent).resolve()
    cases = (
        sorted(path.name for path in PRACTICE_ROOT.iterdir() if path.is_dir())
        if arguments.all
        else [arguments.case]
    )
    passed = [run_case(case_name, agent_path) for case_name in cases]
    raise SystemExit(0 if all(passed) else 1)


if __name__ == "__main__":
    main()

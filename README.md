# Large-Repository Coding Agent Challenge

## Task

Improve `agent.py` so it can solve issue-style coding tasks in a large Python
repository. The agent must inspect files, edit source code, run tests, and stop
when done. You may use Codex, Claude Code, ChatGPT, or another development tool.
Suggested time: **3 hours**.

The included `agent.py` is intentionally a small starter implementation. It is
designed to be easy to understand, not to meet the hiring score without changes.

## Submission

Submit only `agent.py`.

- Maximum 280 lines and 20 KB.
- Per task: maximum 5 LLM calls, 12 tool calls, and 90 seconds.
- Export `solve(task, tools, llm)` as a normal synchronous function.
- Do not modify tests or access files/network outside the supplied interfaces.
- Other changed files are ignored.

Add a short module docstring explaining your design under these headings:
`TOOLS`, `LOOP`, `FAILURE HANDLING`, and `STOPPING`.

## Available Interfaces

```python
response = llm.ask(messages)          # fixed OpenRouter model
tools.list_files()
tools.read_file(path)                 # oversized files return head + tail
tools.write_file(path, content)       # complete-file write; tests are read-only
tools.patch_file(path, replacements)  # atomic exact-text replacements
tools.run_tests()
```

Each `patch_file` replacement is `{"old": "...", "new": "..."}` with an
optional 1-based `occurrence`. One `patch_file` call can contain up to eight
replacements for one source file and counts as one tool call.

## Setup

Use Python 3.10 or newer.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export OPENROUTER_API_KEY=your-key
python check_agent.py
```

Never commit or share your API key.

## Practice Cases

The public package contains 10 tasks over one shared pytest snapshot in
`practice-repo/`. Each directory under `practice-cases/` contains a task and a
visible test injected into a fresh repository copy. Private evaluation tests and
upstream solution references are intentionally excluded from the public repo.

```bash
python run_practice.py --case 01_pytest_monkeypatch
python run_practice.py --all
```

## Evaluation

The grader runs the 10 task prompts in clean repository copies and adds private
regression tests. A task scores one point only when both its visible and private
tests pass. The main score is solved tasks; ties use fewer LLM calls, then fewer
tool calls.

### Recommended Hiring Bar

- **5/10 or higher:** passes the technical benchmark.
- **4/10:** borderline; review the approach and rerun once.
- **0–3/10:** below the recommended benchmark.
- **8–10/10:** exceptional.

Model output can vary even with temperature set to zero. Record the model, date,
score, LLM calls, and tool calls for every official run. Do not reward solutions
that hardcode task names, issue numbers, test contents, or known fixes. The
submitted `agent.py` must implement a general orchestration strategy.

## Repository Rules

- Do not publish private evaluation tests or upstream solution references.
- Run untrusted submissions in an isolated environment.
- The bundled pytest source retains its upstream license and notices.

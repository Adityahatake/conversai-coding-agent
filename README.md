# Large-Repository Coding Agent Challenge

## Task

Improve `agent.py` so it can solve issue-style coding tasks in a large Python
repository. The agent must inspect files, edit source code, run tests, and stop
when done. You may use Codex, Claude Code, ChatGPT, or another development tool.
Suggested time: **3 hours**.

The included `agent.py` is intentionally a small starter implementation. It is
designed to be easy to understand, not to meet the hiring score without changes.

## Repository Map

| Path | Purpose |
| --- | --- |
| `agent.py` | Starter implementation and the only file candidates submit. Candidates may modify or replace it completely. |
| `runtime.py` | Fixed evaluation harness containing the OpenRouter client, repository tools, and call limits. Do not modify it. |
| `validation.py` | Static rules for the submitted `agent.py`, including size, line-count, signature, and import restrictions. |
| `check_agent.py` | Checks only the submission rules. It does not call the model or run a coding task. |
| `run_practice.py` | Runs the agent on one or all practice tasks. It calls OpenRouter, creates a temporary repository copy, runs tests, and reports usage. |
| `practice-repo/` | Shared pytest source snapshot that the agent modifies inside a temporary copy for every case. |
| `practice-cases/` | Ten public task prompts and their visible tests. |
| `requirements.txt` | Python dependencies needed by the challenge runner and pytest snapshot. |

Private regression tests and solution provenance are maintained separately by
the challenge owner and are not included in this repository.

## Submission

Submit only `agent.py`.

- Maximum 280 lines and 20 KB.
- Per task: maximum 5 LLM calls, 12 tool calls, and 90 seconds.
- Export `solve(task, tools, llm)` as a normal synchronous function.
- Do not modify tests or access files/network outside the supplied interfaces.
- Other changed files are ignored.

Add a short module docstring explaining your design under these headings:
`TOOLS`, `LOOP`, `FAILURE HANDLING`, and `STOPPING`.

## Fixed Evaluation Model

Candidates may use any coding assistant while developing their submission, but
the submitted agent does **not** choose its runtime model. Every official run
uses this fixed OpenRouter model and configuration from `runtime.py`:

- Model: `stealth/space-bunny-alpha`
- Model page: https://openrouter.ai/stealth/space-bunny-alpha
- Pricing: currently free on OpenRouter (`$0` input and output token pricing)
- API: OpenRouter's OpenAI-compatible chat-completions endpoint
- Temperature: `0.0`
- Maximum output: `4,000` tokens per model call
- Maximum model calls: `5` per task

Use only the supplied `llm.ask(messages)` interface inside `agent.py`. Do not
create another API client, select another model, or make direct network calls.
The `OPENROUTER_API_KEY` environment variable is used by the runner and is not
available to the submitted agent as a supported interface.
An OpenRouter API key is still required even though the model is currently free.
Model availability and pricing may change, so the challenge owner should verify
the model page before each official evaluation session.

## Available Interfaces

Your `solve()` function receives `tools` and `llm`. These are the only supported
ways to inspect the repository, change code, run tests, and call the model.

### `llm.ask(messages)`

Sends an OpenAI-style message list to the fixed model and returns its response
as a string. Every call counts toward the limit of five model calls.

```python
response = llm.ask([
    {"role": "system", "content": "Return JSON."},
    {"role": "user", "content": "Find the bug."},
])
```

### `tools.list_files()`

Returns the repository's file paths as a newline-separated string. It does not
return file contents.

### `tools.read_file(path)`

Returns a UTF-8 text file's contents. For a file larger than the output limit,
the tool returns its beginning and end with an omission marker in the middle.

### `tools.write_file(path, content)`

Replaces an entire source file. Use this for small files. Test files are
read-only, and files larger than 50 KB cannot be written with this method.

### `tools.patch_file(path, replacements)`

Applies small exact-text replacements without returning or rewriting the entire
file. This is the preferred way to modify large files.

```python
tools.patch_file(
    "src/example.py",
    [
        {
            "old": "return old_value",
            "new": "return new_value",
        }
    ],
)
```

The `old` text must exist exactly. If it occurs more than once, add
`"occurrence": 2` to select the second match. A call may contain up to eight
replacements, all for the same file. The operation is atomic: if any replacement
is invalid, the file is not changed.

### `tools.run_tests()`

Runs the visible tests and returns a string beginning with `Exit code: 0` on
success or a nonzero exit code on failure. The output includes failure details
that can be sent back to the model for a repair attempt.

Every call to a `tools` method counts toward the limit of 12 tool calls.

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

Use `check_agent.py` first because it is fast and makes no API calls. Use
`run_practice.py` afterward to test actual agent behavior; it consumes OpenRouter
requests.

## Evaluation

Each of the 10 cases is worth one point:

1. The grader creates a fresh copy of `practice-repo/`.
2. It gives the task text, `tools`, and `llm` to the submitted `solve()` function.
3. The agent may inspect files, edit source, and run the visible tests.
4. After the agent stops, the grader runs both the visible and private tests.
5. The case earns one point only if both test groups pass.

The total score is therefore out of 10. If two candidates have the same score,
the candidate using fewer LLM calls ranks first, followed by fewer tool calls.

### Recommended Hiring Bar

- **0–3:** below the recommended benchmark.
- **4:** borderline; review the implementation and rerun once.
- **5–7:** passes the benchmark.
- **8–10:** exceptional.

The minimum recommended passing score is **5/10**. Because model output can vary,
record the score and call counts for each official run. Rerun borderline scores
once. Reject agents that hardcode task names, test contents, or known fixes; the
submission must use a general orchestration strategy.

## Repository Rules

- Do not publish private evaluation tests or upstream solution references.
- Run untrusted submissions in an isolated environment.
- The bundled pytest source retains its upstream license and notices.

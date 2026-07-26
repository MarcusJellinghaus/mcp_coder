# Step 5 — LLM session helper + prompt builders

Add the small LLM-facing layer: one resumable-session helper and the builders that turn
git state / failure keys into prompts. Not yet wired into the orchestrator (Step 6).
See [summary.md](./summary.md) ("LLM session").

## WHERE

- Modify: `src/mcp_coder/workflows/rebase.py` (add a `# --- LLM steps ---` section)
- Create: `tests/workflows/rebase/test_llm_steps.py`

## WHAT

```python
def _prompt_in_session(
    prompt: str,
    session_id: str | None,
    *,
    project_dir: Path,
    provider: str,
    env_vars: dict[str, str],
    mcp_config: str | None,
    settings_file: str | None,
    execution_dir: Path | None,
    step_name: str,
) -> tuple[str, str | None]: ...

def _build_conflict_prompt(project_dir: Path, files: list[str]) -> str: ...
def _build_regression_fix_prompt(regression_text: str) -> str: ...
def _format_failure_keys(keys: set[FailureKey]) -> str: ...
```

## HOW

- `_prompt_in_session` calls `prompt_llm` with
  `timeout=LLM_INACTIVITY_TIMEOUT_SECONDS` (imported from
  `mcp_coder.workflow_steps.constants` — precedent: `workflows/review/core.py`),
  `session_id=session_id`, `branch_name=get_branch_name_for_logging(...)`, and the
  passed-through provider/env/config args (same call shape as `check_and_fix_mypy`).
  After the call it best-effort persists via `store_session(response_data=...,
  prompt=..., store_path=str(project_dir / ".mcp-coder" / "rebase_sessions"),
  step_name=step_name, branch_name=...)` inside try/except with a warning log
  (mirrors implement). Returns `(text, response.get("session_id"))` so the caller
  threads the session onward.
- `_build_conflict_prompt` loads the "Rebase Conflict Resolution" section via
  `get_prompt` and replaces `[conflict_context]` with per-file blocks built from
  `_show_stage` (Step 3): path, then base/ours/theirs contents in fenced blocks, absent
  sides rendered as `(absent — file does not exist on this side)`.
- `_build_regression_fix_prompt` loads "Rebase Regression Fix" and replaces
  `[regression_output]`.
- `_format_failure_keys` renders a key set as sorted, one-per-line text
  (`pytest: <nodeid>` / `pylint: <file> <code> <message>` / `mypy: ...`). Sorted output
  is required: it doubles as the stall-guard comparison string in Step 6, so it must be
  deterministic.

## ALGORITHM

```
_prompt_in_session(prompt, session_id, ...):
    response = prompt_llm(prompt, provider=..., session_id=session_id,
                          timeout=LLM_INACTIVITY_TIMEOUT_SECONDS, ...)
    try: store_session(... "rebase_sessions", step_name ...)
    except Exception: logger.warning(...)
    return response.get("text", "") or "", response.get("session_id")
```

## DATA

- `_prompt_in_session`: `(response_text, new_session_id)`; LLM exceptions propagate
  (orchestrator maps them to exit 1).
- Builders return plain strings; `_format_failure_keys` returns "" for an empty set.

## TDD

Write `tests/workflows/rebase/test_llm_steps.py` first:

1. `_prompt_in_session`: mock `prompt_llm` + `store_session`; assert timeout constant,
   session_id passthrough (None on first call, provided value on resume), store path
   ends with `.mcp-coder/rebase_sessions`, `store_session` failure only warns,
   returned tuple correct.
2. `_build_conflict_prompt`: mock `_show_stage`; assert file path and all three
   versions appear; absent side renders the absence note; placeholder fully replaced.
3. `_build_regression_fix_prompt`: placeholder replaced with given text.
4. `_format_failure_keys`: deterministic sorted output; stable across set ordering;
   empty set → "".

## Commit

One commit. Suggested message:
`feat: add rebase LLM session helper and prompt builders`

## LLM Prompt

> Read `pr_info/steps/summary.md` for context, then implement `pr_info/steps/step_5.md`
> exactly: add `_prompt_in_session`, `_build_conflict_prompt`,
> `_build_regression_fix_prompt`, and `_format_failure_keys` to
> `src/mcp_coder/workflows/rebase.py`, reusing `LLM_INACTIVITY_TIMEOUT_SECONDS` from
> `workflow_steps.constants` and `store_session` under `.mcp-coder/rebase_sessions`
> (mirror implement's pattern in `workflows/implement/task_processing.py`). Write
> `tests/workflows/rebase/test_llm_steps.py` first (TDD). Do not modify the orchestrator
> yet. Run pylint, pytest, and mypy via the MCP check tools and fix any findings before
> finishing.

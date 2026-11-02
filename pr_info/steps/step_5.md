# Step 5 — Shared helper `rebase_with_llm_fallback`

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_5.md` only.
> Write the tests first, then the implementation. Run pylint, pytest (fast unit
> set, `-n auto`, plus the `git_integration` marker for the new guard test), mypy
> and lint-imports until they pass, run `run_format_code`, and make exactly one commit.

## Precondition

`from mcp_workspace.git_operations.read_operations import git_check_ignore` must work
in the installed environment. If it does not, write one line to
`pr_info/.blocked.txt` and stop.

## WHERE

- `src/mcp_coder/mcp_workspace_git.py` — re-export `git_check_ignore` (add to `__all__`)
- `src/mcp_coder/workflow_steps/rebase.py` — `RebaseOutcome.llm_detail`
- New: `src/mcp_coder/workflows/rebase_automated.py`
- New test: `tests/workflows/rebase/test_rebase_automated.py`

## WHAT

```python
# workflow_steps/rebase.py — new field on RebaseOutcome (docstring updated)
llm_detail: str | None = None   # what the LLM rebase did / why it was skipped

# workflows/rebase_automated.py
AUTOMATED_EXCLUDED_MARKERS: list[str] = [
    "not claude_cli_integration", "not copilot_cli_integration",
    "not langchain_integration", "not llm_integration",
    "not jenkins_integration", "not install_integration",
]
_LLM_TRIGGER_REASONS = ("conflict", "rebase_failed")
_IGNORE_PROBE = ".mcp-coder/rebase_sessions/probe"

def _mcp_coder_dir_problem(project_dir: Path) -> str | None:
    """Return why the LLM rebase must not run (``.mcp-coder/`` not ignored), or None."""

def rebase_with_llm_fallback(
    project_dir: Path,
    provider: str,
    mcp_config: str | None,
    settings_override: str | None = None,
) -> RebaseOutcome:
    """Git-only rebase, then the LLM rebase on conflict / rebase_failed."""
```

## HOW

- Imports: `_attempt_rebase_and_push`, `RebaseOutcome` (workflow_steps.rebase),
  `push_changes` (workflow_steps.commit), `git_check_ignore` (shim),
  `rebase_settings_file` (rebase_permissions), `run_rebase_workflow` (rebase),
  `exception_summary` (workflow_utils.failure_handling), `dataclasses.replace`.
- The probe path is inside the folder, never `.mcp-coder` itself: a `/.mcp-coder/*`
  rule does not match the folder, and a `.mcp-coder/` rule cannot match a missing folder.
- `git_check_ignore` returns a string; `"No paths are ignored."` means not ignored.
  Any exception → problem string.
- Never force-with-lease after the LLM: plain `push_changes(project_dir)` only.

## ALGORITHM

```
outcome = _attempt_rebase_and_push(project_dir)
if outcome.reason not in _LLM_TRIGGER_REASONS: return outcome
if problem := _mcp_coder_dir_problem(project_dir): return replace(outcome, llm_detail=problem)
try:
    with rebase_settings_file(settings_override) as settings:
        result = run_rebase_workflow(project_dir, provider, outcome.base_branch, mcp_config,
                                     settings, markers=AUTOMATED_EXCLUDED_MARKERS)
except Exception as exc: return replace(outcome, llm_detail=f"LLM rebase crashed: {exception_summary(exc)}")
if result.push_rejected: return replace(outcome, reason="push_failed", files=(), llm_detail=result.reason)
if result.exit_code != 0: return replace(outcome, llm_detail=result.reason)
if not push_changes(project_dir): return replace(outcome, reason="push_failed", files=(), llm_detail="LLM rebase succeeded, but the plain push was rejected")
return replace(outcome, reason="ok", files=(), llm_detail=result.reason)
```

## DATA

Returns `RebaseOutcome`; `reason` is the git-only reason, `"ok"` or `"push_failed"`.

## Tests (`test_rebase_automated.py`)

- Mocked (parametrized where possible):
  - git-only `ok` / `dirty_tree` / `no_base` / `base_missing` / `push_failed` → returned
    unchanged, LLM not called.
  - `conflict` and `rebase_failed` both trigger the LLM with `base_branch` from the outcome
    and `markers=AUTOMATED_EXCLUDED_MARKERS`, and a settings path that exists during the
    call and is gone afterwards (no override); override passed through.
  - LLM exit 0 + push ok → `ok`, `push_changes` called without `force_with_lease`.
  - LLM exit 0 + push rejected → `push_failed`.
  - `push_rejected=True` → `push_failed`, `llm_detail` = result reason.
  - Both `push_failed` paths and the `ok` path (from a git-only `conflict` outcome with
    files) → `files == ()`, so hand-off comments (e.g. fix-conflict's `_fail` on a
    still-`dirty` state) don't list the conflict files as "Uncommitted files".
  - exit 1 / non-push exit 2 → git-only reason kept, `llm_detail` set.
  - `run_rebase_workflow` raises → git-only reason kept, `llm_detail` names the error.
  - guard problem → LLM not called, `llm_detail` set; `git_check_ignore` raising → same.
- Real git repo (`@pytest.mark.git_integration`), `.mcp-coder/` absent:
  `.gitignore` with `/.mcp-coder/*` → None; with `.mcp-coder/` → None;
  no rule → problem string.

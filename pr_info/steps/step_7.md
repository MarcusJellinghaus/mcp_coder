# Step 7 — create-pr: rebase before the summary when the branch is behind

## LLM prompt
> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_7.md` exactly.
> Write the tests first, then the code. Run pylint, pytest (fast unit set, `-n auto`) and mypy; all must pass.
> Format the code and make exactly one commit for this step.

## WHERE
- `src/mcp_coder/workflows/create_pr/core.py`
- `tests/workflows/create_pr/test_workflow.py` (or `test_workflow_helpers.py` for the helper's unit tests)

## WHAT
```python
def _rebase_if_needed(project_dir: Path) -> None:
    """Rebase onto the base branch and push, only when the branch is behind. Never fails the workflow."""
```
Called inside `body()` right after the prerequisites check, before "Generate PR summary".

## ALGORITHM
```
branch = get_current_branch_name(project_dir); base = detect_base_branch(project_dir, current_branch=branch)
if base is None: logger.warning(...); return
needed, reason = needs_rebase(project_dir, base)
if not needed:
    log warning if reason.startswith("error:") else info "up to date"; return
outcome = _attempt_rebase_and_push(project_dir); logger.log(OUTPUT, "Rebase result: %s", outcome.reason)
```

## HOW
- Imports: `needs_rebase` from `mcp_coder.mcp_workspace_git` (shim already exports it);
  `_attempt_rebase_and_push` from `mcp_coder.workflow_steps.rebase`.
- Mirrors the `needs_rebase` error handling in `workflows/rebase.py:466`, but an error is logged and skipped, not a failure.
- A failed rebase (`conflict`, `push_failed`, ...) is logged only; phase B handles a resulting `dirty` PR.
- Adjust the "Step N/5" log labels if you add a numbered log line; keep it simple.

## Tests (write first)
Patch `needs_rebase` and `_attempt_rebase_and_push` at `mcp_coder.workflows.create_pr.core.*`.
- `(True, "...")` → `_attempt_rebase_and_push` called once, before `generate_pr_summary` (use a shared `MagicMock`
  manager or call-order list).
- `(False, "up to date")` → not called.
- `(False, "error: fetch failed")` → not called, warning logged, workflow continues (exit 0).
- Rebase outcome `conflict` → workflow continues.
- Existing `test_workflow.py` tests: patch `_rebase_if_needed` (or `needs_rebase` returning `(False, "")`) where they
  would otherwise hit git.

## DATA
Returns `None`.

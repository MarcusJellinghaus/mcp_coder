# Step 7 — create-pr: rebase before the summary when the branch is behind

## LLM prompt
> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_7.md` exactly.
> Write the tests first, then the code. Run pylint, pytest (fast unit set, `-n auto`) and mypy; all must pass.
> Format the code and make exactly one commit for this step.

## WHERE
- New `src/mcp_coder/workflows/create_pr/pre_creation.py` — `_rebase_if_needed` (keeps `core.py` under the
  750-line CI gate, `ci.yml:104`; step 11 adds the resume helpers to the same module)
- `src/mcp_coder/workflows/create_pr/core.py` — imports and calls `_rebase_if_needed`
- New `tests/workflows/create_pr/test_pre_creation.py` (helper unit tests), `tests/workflows/create_pr/test_workflow.py` (call order)

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
- `pre_creation.py` imports: `needs_rebase`, `get_current_branch_name` from `mcp_coder.mcp_workspace_git` (shim already
  exports them); `_attempt_rebase_and_push` from `mcp_coder.workflow_steps.rebase`; `detect_base_branch` from
  `mcp_coder.workflow_utils.base_branch`. It must not import `create_pr.core` (no cycle).
- `core.py`: `from mcp_coder.workflows.create_pr.pre_creation import _rebase_if_needed`.
- Mirrors the `needs_rebase` error handling in `workflows/rebase.py:466`, but an error is logged and skipped, not a failure.
- A failed rebase (`conflict`, `push_failed`, ...) is logged only; phase B handles a resulting `dirty` PR.
- Adjust the "Step N/5" log labels if you add a numbered log line; keep it simple.

## Tests (write first)
`test_pre_creation.py` — patch `needs_rebase`, `_attempt_rebase_and_push`, `get_current_branch_name`,
`detect_base_branch` at `mcp_coder.workflows.create_pr.pre_creation.*`:
- `(True, "...")` → `_attempt_rebase_and_push` called once.
- `(False, "up to date")` → not called.
- `(False, "error: fetch failed")` → not called, warning logged, returns normally.
- Base `None` → `needs_rebase` not called, warning logged.
- Rebase outcome `conflict` → returns normally.

`test_workflow.py` — patch `mcp_coder.workflows.create_pr.core._rebase_if_needed`:
- called once, before `generate_pr_summary` (shared `MagicMock` manager or call-order list).
- Existing tests: patch `core._rebase_if_needed` where they would otherwise hit git.

## DATA
Returns `None`.

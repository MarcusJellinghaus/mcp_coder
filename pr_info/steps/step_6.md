# Step 6 — Extract shared `is_branch_not_base` prerequisite step

**Goal:** Consolidate the "current branch is not the base branch" sub-check as a **pure
comparison**, so `implement` (compares vs default branch) and `create_pr` (compares vs
`detect_base_branch`, which may be a custom base) share one helper without the step
resolving the base itself. Independent of Step 5.

## WHERE

Modify:
- `src/mcp_coder/workflow_steps/prerequisites.py` (add the helper)
- `tests/workflow_steps/test_prerequisites.py` (add tests)
- `src/mcp_coder/workflows/implement/prerequisites.py` (`check_main_branch` delegates)
- `src/mcp_coder/workflows/create_pr/core.py` (branch check in `check_prerequisites` delegates)

## WHAT (signature)

In `workflow_steps/prerequisites.py`:
```python
def is_branch_not_base(current_branch: Optional[str], base_branch: Optional[str]) -> bool
```

Pure comparison + logging; it does **not** call any git resolver.

## HOW (integration points)

- `implement/prerequisites.py::check_main_branch`: keep resolving
  `current = get_current_branch_name(project_dir)` and
  `base = get_default_branch_name(project_dir)`, then
  `return is_branch_not_base(current, base)`.
- `create_pr/core.py::check_prerequisites`: keep resolving
  `current = get_current_branch_name(project_dir)` and
  `base = detect_base_branch(project_dir, current_branch=current)`, then use
  `is_branch_not_base(current, base)`. This preserves the custom-base semantics —
  the step only compares, the orchestrator still chooses the base.

## ALGORITHM

```
if current_branch is None:  log error (detached HEAD); return False
if base_branch is None:     log error (could not determine base); return False
if current_branch == base_branch:  log error (on base branch); return False
return True
```

## DATA

`bool` — True when `current_branch` is a valid, non-base feature branch.

## TDD

Add `tests/workflow_steps/test_prerequisites.py::test_is_branch_not_base_*` first
(current None → False; base None → False; equal → False; distinct → True). Then extract
and repoint both callers. The error messages become shared/generic wording (log-only
delta); adjust the two callers' branch-check tests if they assert exact messages. The
`detect_base_branch` resolution and `get_default_branch_name` resolution stay in their
respective orchestrators, unchanged.

## Checks / commit

All enforcers + pylint / pytest / mypy green. One commit:
`refactor(workflow_steps): extract shared is_branch_not_base prerequisite`.

## LLM prompt

> Read `pr_info/steps/summary.md` (section "Prerequisite extraction") and
> `pr_info/steps/step_6.md`. Add `is_branch_not_base(current_branch, base_branch) -> bool`
> to `workflow_steps/prerequisites.py` as a pure comparison (no git resolver calls).
> Repoint `implement/prerequisites.py::check_main_branch` (resolving the default branch)
> and the branch check in `create_pr/core.py::check_prerequisites` (resolving via
> `detect_base_branch`) to delegate to it — each keeps resolving its own base. Write the
> comparison tests in `tests/workflow_steps/test_prerequisites.py` first, then adjust the
> two callers' tests for the shared wording. Confirm create_pr's custom-base behavior is
> unchanged. Verify all enforcers and the pylint/pytest/mypy trio are green, then produce
> one commit.

# Step 2 — create-plan config-gated success transition

**Read `pr_info/steps/summary.md` first** (§2 Config-gated success transitions). This step gates
the create-plan success label on `auto_review_plan`. Depends on Step 1 (`get_repo_flag`).
TDD: write the test cases first, then the gate.

## WHERE
- Modify `src/mcp_coder/workflows/create_plan/core.py` (the success label transition, currently
  hardcoded `to_label_id="plan_review"` inside the `if update_issue_labels:` block near the end of
  the workflow function, after commit + push).
- Add/modify tests under `tests/workflows/create_plan/` (e.g. `test_main.py` or a focused test
  module) — no existing test asserts `to_label_id`, so this is fresh coverage.

## WHAT
No new function. Compute the target label id from the flag before calling `update_workflow_label`.

## HOW
- `from mcp_coder.utils.repo_config import get_repo_flag`
- `project_dir` and `issue_number` are already in scope at the transition site.
- Leave `from_label_id="planning"` and `validated_issue_number=issue_number` unchanged.

## ALGORITHM
```
to_label_id = (
    "plan_review_bot"
    if get_repo_flag(project_dir, "auto_review_plan")
    else "plan_review"
)
update_workflow_label(issue_manager, from_label_id="planning",
                      to_label_id=to_label_id, validated_issue_number=issue_number)
```

## DATA
- No signature change; `to_label_id` is `"plan_review"` (flag off) or `"plan_review_bot"` (flag on).

## TESTS
Patch `get_repo_flag` at `mcp_coder.workflows.create_plan.core.get_repo_flag` and
`update_workflow_label` / `IssueManager` as the existing success-path tests do. Drive the workflow
to the success transition with `update_issue_labels=True` and assert:
1. Flag off (`get_repo_flag` → False) → `update_workflow_label(..., to_label_id="plan_review")`.
2. Flag on (`get_repo_flag` → True) → `update_workflow_label(..., to_label_id="plan_review_bot")`.
Reuse the existing mock scaffolding for the create-plan success path (mock commit/push/validate so
the run reaches the label step).

## Commit
One commit: gate + tests. Run pylint, pytest (`-n auto` unit exclusion), mypy, `lint-imports`.

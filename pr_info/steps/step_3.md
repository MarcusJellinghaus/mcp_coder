# Step 3 — implement config-gated success transition

**Read `pr_info/steps/summary.md` first** (§2 Config-gated success transitions). This step gates
the implement success label on `auto_review_implementation`. Depends on Step 1 (`get_repo_flag`).
TDD: update the existing assertion into flag-off + flag-on cases first, then the gate.

## WHERE
- Modify `src/mcp_coder/workflows/implement/core.py` — "Step 6: Success label transition" block
  (currently hardcoded `to_label_id="code_review"` inside `if update_issue_labels:`).
- Update `tests/workflows/implement/test_core_workflow.py` (the existing test asserting
  `to_label_id="code_review"`).

## WHAT
No new function. Compute the target label id from the flag before `update_workflow_label`.

## HOW
- `from mcp_coder.utils.repo_config import get_repo_flag`
- `project_dir` is already in scope. `update_workflow_label` here takes no `validated_issue_number`
  (branch-derived) — keep that call shape; only change `to_label_id`.

## ALGORITHM
```
to_label_id = (
    "code_review_bot"
    if get_repo_flag(project_dir, "auto_review_implementation")
    else "code_review"
)
update_workflow_label(issue_manager, from_label_id="implementing", to_label_id=to_label_id)
```

## DATA
- No signature change; `to_label_id` is `"code_review"` (flag off) or `"code_review_bot"` (flag on).

## TESTS
Patch `get_repo_flag` at `mcp_coder.workflows.implement.core.get_repo_flag`. In the existing
`test_success_...update_issue_labels`-style test:
1. Keep a flag-off case (`get_repo_flag` → False) asserting `to_label_id="code_review"`
   (the current assertion, now with the mock added).
2. Add a flag-on case (`get_repo_flag` → True) asserting `to_label_id="code_review_bot"`.
The success-path mocks (git clean, branch, CI, finalise, IssueManager, update_workflow_label) are
already present in that test — add the `get_repo_flag` patch to the decorator stack.

## Commit
One commit: gate + test updates. Run pylint, pytest (`-n auto` unit exclusion), mypy, `lint-imports`.

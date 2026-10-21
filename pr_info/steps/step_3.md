# Step 3: `validate_branch_issue_linkage()` uses `is_branch_linked_to_issue` (closes #708)

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_3.md`.
> Steps 1 and 2 are already done. Use TDD: first update
> `TestValidateBranchIssueLinkage` in
> `tests/workflows/create_pr/test_workflow_helpers.py`, then change
> `validate_branch_issue_linkage()` in
> `src/mcp_coder/workflows/create_pr/core.py`. Run pylint, mypy, the fast
> pytest set (`-n auto`), ruff, lint-imports and tach; all must pass. Run the
> formatter and make exactly one commit.

## Precondition

`src/mcp_coder/workflow_utils/branch_linkage.py` must exist and define
`is_branch_linked_to_issue`. If it does not, write one line to
`pr_info/.blocked.txt` and stop.

## WHERE

- `src/mcp_coder/workflows/create_pr/core.py`: modify `validate_branch_issue_linkage()`
- `tests/workflows/create_pr/test_workflow_helpers.py`: modify `TestValidateBranchIssueLinkage`

## WHAT

`validate_branch_issue_linkage(project_dir: Path) -> Optional[int]` keeps its
signature and return contract. Update the docstring: "linked" now means a
linked branch or the head of an open closing PR.

## HOW

- Add `from mcp_coder.workflow_utils.branch_linkage import is_branch_linked_to_issue`.
- Keep `IssueBranchManager(project_dir=project_dir)` in `core.py`: tests patch
  `mcp_coder.workflows.create_pr.core.IssueBranchManager`.
- Replace steps 3–4 (the `get_linked_branches()` call and the if/else logging)
  with the helper call. The helper does all the logging, so the callers'
  `logger.info` / `logger.warning` lines are removed.
- The outer `try/except` stays.

## ALGORITHM

```
branch_name = get_current_branch_name(project_dir)          # unchanged
issue_number = extract_issue_number_from_branch(branch_name) # unchanged
branch_manager = IssueBranchManager(project_dir=project_dir)
if is_branch_linked_to_issue(branch_manager, issue_number, branch_name): return issue_number
return None   # helper already logged WARNING (not linked) or ERROR (lookup failed)
```

## DATA

Returns `Optional[int]`: the issue number if linked; `None` if not linked, if
the lookup failed, or on an exception.

## Tests (`TestValidateBranchIssueLinkage`)

1. **Re-patch `test_validate_branch_issue_linkage_success`.** Set
   `mock_manager.get_linked_branch_and_closing_prs_or_none.return_value = (["123-feature"], [])`
   and assert that method was called once with `123`.
2. **Re-patch `test_validate_branch_issue_linkage_not_linked`.** Use
   `return_value = ([], [])` and the same `assert_called_once_with(123)`.
3. **New `test_validate_branch_issue_linkage_post_pr_closing_pr`.** Use
   `return_value = ([], [ClosingPRRef(42, "123-feature")])` and assert the
   result is `123`. Import `ClosingPRRef` from `mcp_coder.mcp_workspace_github`.
4. **New `test_validate_branch_issue_linkage_lookup_failed`.** Use
   `return_value = None` and assert the result is `None`. Also assert that an
   ERROR record exists in `caplog.records` (use `any(...)`, never an exact count).
5. `test_validate_branch_issue_linkage_no_issue_number` stays unchanged.

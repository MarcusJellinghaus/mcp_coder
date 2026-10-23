# Step 3 — `prerequisites.py` uses `create_empty_issue_data()`

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_3.md` exactly.
> Update the test first, then the source. Run the checks listed in the summary; all must
> pass. Produce one commit.

## WHERE
- `src/mcp_coder/workflows/create_plan/prerequisites.py`
- `tests/workflows/create_plan/test_prerequisites.py`

## WHAT

Test (first): in `test_check_prerequisites_empty_issue_data_structure`, add
`assert issue_data == create_empty_issue_data()` (import from `mcp_coder.mcp_workspace_github`).
Leave the rest of this file for step 6.

Implementation:
- Replace the 13-line `IssueData(number=0, ..., author_association=None)` literal with
  `empty_issue_data = create_empty_issue_data()`.
- Import `create_empty_issue_data` from `mcp_coder.mcp_workspace_github` in the existing
  import block. Keep `IssueData` (still used in the return annotation).

## HOW
Calls upstream code through the shim; `src/` must not import anything from `tests/`.

## DATA
Unchanged: `check_prerequisites(...) -> tuple[bool, IssueData]`; failure returns the empty sentinel.

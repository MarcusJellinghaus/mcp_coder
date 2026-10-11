# Summary: Guarantee a closing reference to the linked issue in create-pr (#1189)

## Problem

`run_create_pr_workflow` sends the PR body exactly as the LLM wrote it. A `Closes #N` line appears only if the LLM wrote one. When it is missing, GitHub never auto-closes the issue on merge, even though the workflow already knows the issue number from the branch (`validate_branch_issue_linkage`).

## Design changes

1. **Issue number is always resolved.** `cached_issue_number = validate_branch_issue_linkage(project_dir)` is no longer gated behind `update_issue_labels`. It still runs before PR creation, because GitHub clears `linkedBranches` once the PR exists. The label update and the body injection both use this one cached value; there is no new resolution logic.
2. **New pure text helper** `ensure_closing_reference(body, issue_number) -> str` in `workflows/create_pr/helpers.py`, re-exported from `core.py` (same convention as `parse_pr_summary`). It detects GitHub's closing keywords (`close/closes/closed`, `fix/fixes/fixed`, `resolve/resolves/resolved`, case-insensitive, word-boundaried on both sides, followed by `#<N>` with a word boundary after the number):
   - If the body already closes the linked issue, it returns the body unchanged.
   - Otherwise it appends `"\n\nCloses #<N>"`. If the body closes other issues, it logs one warning naming all of them (distinct, sorted).
3. **Injection lives in the orchestrator.** In step 5 of `run_create_pr_workflow`, just before `create_pull_request(project_dir, title, body)`, the body passes through the helper when `cached_issue_number` is set. `create_pull_request` keeps its signature.
4. **Side effect:** failure handlers now receive the verified issue number even when `update_issue_labels=False`. Label changes stay gated by that flag inside `handle_workflow_failure`, so the only effect is that failure comments target the verified issue.

The new helper is named so it is not confused with `PullRequestManager.get_closing_issue_numbers`, which is the GraphQL-based lookup that runs after the PR is created. That lookup stays unchanged as the label-update fallback.

## Files

| File | Change |
|---|---|
| `src/mcp_coder/workflows/create_pr/helpers.py` | Modified: add `_CLOSING_REF_RE` and `ensure_closing_reference` |
| `src/mcp_coder/workflows/create_pr/core.py` | Modified: re-export the helper, remove the gate, fix the no-link warning text, inject before PR creation |
| `tests/workflows/create_pr/test_parsing.py` | Modified: helper unit tests |
| `tests/workflows/create_pr/conftest.py` | **New**: autouse fixture mocking `validate_branch_issue_linkage` → `None` |
| `tests/workflows/create_pr/test_workflow.py` | Modified: two wiring tests |
| `tests/workflows/test_create_pr_integration.py` | Modified: explicit `@patch` of `validate_branch_issue_linkage` on the two workflow tests |

## Steps

1. `step_1.md`: closing-reference helper and its unit tests.
2. `step_2.md`: orchestrator wiring (gate removal and injection) and the test updates.

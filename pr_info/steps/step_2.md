# Step 2: `update_workflow_label()` uses `is_branch_linked_to_issue`

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_2.md`.
> Step 1 (the helper in `workflow_utils/branch_linkage.py`) is already done.
> Use TDD: first update `tests/workflow_utils/test_label_transitions.py`
> (re-patch existing tests and add the new parametrized test), then change
> `src/mcp_coder/workflow_utils/label_transitions.py`. Run pylint, mypy, the
> fast pytest set (`-n auto`), ruff, lint-imports and tach; all must pass. Run
> the formatter and make exactly one commit.

## Precondition

`src/mcp_coder/workflow_utils/branch_linkage.py` must exist and define
`is_branch_linked_to_issue`. If it does not, write one line to
`pr_info/.blocked.txt` and stop.

## WHERE

- `src/mcp_coder/workflow_utils/label_transitions.py`: modify Step 3 of `update_workflow_label()`
- `tests/workflow_utils/test_label_transitions.py`: modify

## WHAT

`update_workflow_label()` keeps its signature and return contract. Only the
linkage check changes.

## HOW

- Add `from mcp_coder.workflow_utils.branch_linkage import is_branch_linked_to_issue`.
- Keep the `IssueBranchManager.__new__` + `BaseGitHubManager.__init__`
  construction exactly as it is.
- Replace the `get_linked_branches()` call and the `if actual_branch_name not in linked_branches:` warning block with:

```python
if not is_branch_linked_to_issue(
    branch_manager, issue_number, actual_branch_name
):
    return False
```

The helper logs ERROR (lookup failed) or WARNING (not linked), so this block
logs nothing itself. `None` and `False` both return False.

## ALGORITHM

```
... steps 1-2 unchanged (branch name, issue number) ...
branch_manager = <existing __new__ + BaseGitHubManager.__init__>
if not is_branch_linked_to_issue(branch_manager, issue_number, actual_branch_name): return False
... steps 4-6 unchanged ...
```

## DATA

Returns `bool`, as before. It never raises: the outer `try/except` stays.

## Tests (`tests/workflow_utils/test_label_transitions.py`)

1. **Re-patch mechanically.** Replace every
   `patch.object(IssueBranchManager, "get_linked_branches", return_value=X)` with
   `patch.object(IssueBranchManager, "get_linked_branch_and_closing_prs_or_none", return_value=(X, []))`.
   There are about 11 sites, including the `validated_issue_number` tests and the race-condition test.
   Do not refactor the fixtures.
2. **In the two `validated_issue_number` tests that patch the method**
   (`test_update_workflow_label_with_validated_issue_number` and
   `test_update_workflow_label_race_condition_scenario`), bind the patch
   (`as mock_lookup`) and add `mock_lookup.assert_not_called()`.
3. **Add one parametrized test**,
   `test_update_workflow_label_linkage_via_closing_prs`, with the same patch
   setup as the happy path (`transition_issue_label` → True,
   `get_current_branch_name` → `"123-feature"`). Import `ClosingPRRef` from
   `mcp_coder.mcp_workspace_github`.

   | lookup return | expected | extra assert |
   |---|---|---|
   | `([], [ClosingPRRef(42, "123-feature")])` | `True` | `transition_issue_label` called once with 123 |
   | `([], [ClosingPRRef(42, "other-branch")])` | `False` | `transition_issue_label` not called |
   | `None` | `False` | an ERROR record exists in `caplog.records`; `transition_issue_label` not called |

   The case where neither source matches (`([], [])`) is already covered by
   the re-patched `test_update_workflow_label_branch_not_linked`.
   For the `None` case, assert with `any(r.levelno == logging.ERROR ...)`,
   never on an exact count: the mcp-workspace method may log too.

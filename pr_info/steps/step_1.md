# Step 1: Shared helper `is_branch_linked_to_issue` + `ClosingPRRef` shim re-export

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_1.md`.
> Use TDD: write `tests/workflow_utils/test_branch_linkage.py` first, then the
> shim change and `src/mcp_coder/workflow_utils/branch_linkage.py`. Do not
> touch any caller of the helper in this step. Run pylint, mypy, the fast
> pytest set (`-n auto`), ruff, lint-imports and tach; all must pass. Run the
> formatter and make exactly one commit.

## Precondition

Check that `mcp_workspace.github_operations.issues.linked_branches_mixin`
exports `ClosingPRRef` and that `IssueBranchManager` has
`get_linked_branch_and_closing_prs_or_none` (use `get_library_source`). If
either is missing, write one line to `pr_info/.blocked.txt` and stop.

## WHERE

- `src/mcp_coder/mcp_workspace_github.py`: modify
- `src/mcp_coder/workflow_utils/branch_linkage.py`: create
- `tests/workflow_utils/test_branch_linkage.py`: create
- `docs/architecture/architecture.md`: modify line ~349 (add `branch_linkage` to the `workflow_utils` capability list)

## WHAT

### Shim

```python
from mcp_workspace.github_operations.issues.linked_branches_mixin import ClosingPRRef
```

Add `"ClosingPRRef"` to `__all__` in the `# Issues` group.

### Helper

```python
def is_branch_linked_to_issue(
    branch_manager: IssueBranchManager,
    issue_number: int,
    branch_name: str,
) -> Optional[bool]:
```

Module conventions: module docstring, `logger = logging.getLogger(__name__)`,
`__all__ = ["is_branch_linked_to_issue"]`, and imports only via
`mcp_coder.mcp_workspace_github`.

The docstring must document:

- Linked branches are checked first, then the head refs of open closing PRs
  (`includeClosedPrs: false`).
- Known limitations:
  - Only PRs that close the issue (`Closes #N` or a manual link) are seen;
    a hand-made PR without that line fails.
  - Matching uses `head_ref_name` only, so a fork PR with the same branch name
    matches.
  - If create-pr's pre-PR linkage check fails, the PR body gets no
    `Closes #N` line, so the fallback can never match for that PR.
- On failure, the mcp-workspace method logs its own line too.

## HOW

- The caller provides the `IssueBranchManager` instance; the helper does not
  construct one.
- Exactly one call to `branch_manager.get_linked_branch_and_closing_prs_or_none(issue_number)`.
- The helper does no exception handling of its own: the mcp-workspace method
  already swallows errors into `None`, and both callers keep their broad
  `try/except`.

## ALGORITHM

```
result = branch_manager.get_linked_branch_and_closing_prs_or_none(issue_number)
if result is None: log ERROR "Could not determine linkage for issue #N"; return None
linked_branches, closing_prs = result
if branch_name in linked_branches: log INFO "... linked branch of issue #N"; return True
for pr in closing_prs: if pr.head_ref_name == branch_name: log INFO "... head of closing PR #<pr.number>"; return True
log WARNING "Branch X is not linked to issue #N: no linked branch or open closing PR matches
  (a PR without 'Closes #N' is not detected). Linked branches: [...], closing PRs: [#..]"; return False
```

## DATA

- Input from mcp-workspace: `Optional[Tuple[List[str], List[ClosingPRRef]]]`.
- `ClosingPRRef(number: int, head_ref_name: str)` is snake_case;
  `headRefName` is only the GraphQL field name.
- Return value: `True` (linked), `False` (not linked), `None` (lookup failed).

## Tests (`tests/workflow_utils/test_branch_linkage.py`)

Use a `MagicMock()` branch manager and set
`get_linked_branch_and_closing_prs_or_none.return_value`. Build PR refs with
`ClosingPRRef` from the shim.

1. Linked match: `(["123-feature"], [])` returns `True`; caplog INFO mentions "linked branch".
2. Closing-PR head match: `([], [ClosingPRRef(42, "123-feature")])` returns `True`; caplog INFO mentions `#42`.
3. Closing PRs, none matching: `([], [ClosingPRRef(42, "other-branch")])` returns `False`; caplog WARNING contains "not linked".
4. Lookup failed: `None` returns `None`; caplog has an ERROR record containing "Could not determine linkage".
   Assert with `any(...)` over `caplog.records`, never on the exact record count.
5. All tests assert that the method was called exactly once with `123`.

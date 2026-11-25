# Step 1 — Move shared helpers to `workflow_utils/issue_helpers.py` (move only)

## LLM prompt

> Read `pr_info/steps/summary.md` and this file (`pr_info/steps/step_1.md`), plus
> `.claude/knowledge_base/refactoring_principles.md`. Implement step 1 only: a pure move of
> `get_issue_status`, `is_marked` and `lookup_branch` into the new module
> `src/mcp_coder/workflow_utils/issue_helpers.py`, with their tests. No behaviour change, no
> re-exports. Run all checks from the summary; all must pass. Produce exactly one commit.

## WHERE

- New: `src/mcp_coder/workflow_utils/issue_helpers.py`
- New: `tests/workflow_utils/test_issue_helpers.py`
- Modified (imports only): `src/mcp_coder/workflows/vscodeclaude/helpers.py`, `issues.py`,
  `checks.py`, `session_launch.py`, `session_restart.py`, `status.py`, `workspace.py`
- Modified (tests moved out / constant): `tests/workflows/vscodeclaude/test_helpers.py`,
  `tests/workflows/vscodeclaude/test_issues_branch_check.py`, `tests/workflows/vscodeclaude/test_checks.py`

## WHAT

Moved unchanged (signatures stay):

```python
# src/mcp_coder/workflow_utils/issue_helpers.py
def get_issue_status(issue: IssueData) -> str: ...
def is_marked(body: str, marker: str = "❌") -> bool: ...
def lookup_branch(cache: BranchLookupCache, issue: IssueData) -> str | None: ...
```

Module boilerplate: docstring, `logger = logging.getLogger(__name__)` (used by `lookup_branch`),
`__all__ = ["get_issue_status", "is_marked", "lookup_branch"]`. Imports from
`mcp_coder.mcp_workspace_github`: `BranchLookupCache`, `BranchLookupError`, `GithubException`, `IssueData`.

## HOW

1. Tests first: create `tests/workflow_utils/test_issue_helpers.py` by moving, unchanged except imports:
   - `TestIssueStatus` and `TestIsMarked` from `tests/workflows/vscodeclaude/test_helpers.py`
     (drop `get_issue_status`, `is_marked` from that file's import list);
   - `TestLookupBranch` from `tests/workflows/vscodeclaude/test_issues_branch_check.py`
     (drop `lookup_branch` from that file's import). The moved class's `caplog` logger
     constant becomes `ISSUE_HELPERS = "mcp_coder.workflow_utils.issue_helpers"`.
   Import the three functions from `mcp_coder.workflow_utils.issue_helpers`.
2. Move the code with `mcp__mcp-tools-py__move_symbol` (source `vscodeclaude/helpers.py` for
   `get_issue_status`, `is_marked`; source `vscodeclaude/issues.py` for `lookup_branch`; destination
   `src/mcp_coder/workflow_utils/issue_helpers.py`). Then verify by hand:
   - `issue_helpers.py` defines its own `logger`; it must not import `logger` (or anything) from
     `vscodeclaude`.
   - Every consumer imports the names from `...workflow_utils.issue_helpers` directly:
     `issues.py` (`get_issue_status`), `checks.py`, `session_launch.py` (`get_issue_status`,
     `lookup_branch`), `session_restart.py`, `status.py`, `workspace.py` (`is_marked`).
     No import of these names through `vscodeclaude.helpers` / `vscodeclaude.issues` remains.
   - Remove `"get_issue_status"` and `"is_marked"` from `vscodeclaude/helpers.py` `__all__`.
   - Remove imports left unused in `helpers.py` / `issues.py` (e.g. `BranchLookupError`,
     `GithubException` if no longer used in `issues.py`).
3. `tests/workflows/vscodeclaude/test_checks.py`: the `ISSUES` constant is only used by
   `TestResolvePrTarget.test_branch_lookup_raises_returns_none_none` (`caplog` for `lookup_branch`'s
   warning). Replace it with `ISSUE_HELPERS = "mcp_coder.workflow_utils.issue_helpers"`.
4. String patches of `mcp_coder.workflows.vscodeclaude.issues.get_issue_status` and
   `...session_launch.get_issue_status` keep working (those modules still import the name) — leave them.

## ALGORITHM

None (pure move).

## DATA

Unchanged.

## Verify

- Test count unchanged (moved tests still collected; no test lost).
- `mcp__mcp-workspace__search_files` for `from .helpers import .*(get_issue_status|is_marked)` and
  `lookup_branch` imports from `.issues` returns nothing.
- If `move_symbol` cannot produce this layout and a hand move would require changing code inside the
  moved functions, write one line to `pr_info/.blocked.txt` and stop.

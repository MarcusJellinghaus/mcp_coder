# Step 1 — Move `TestBuildEligibleIssuesWithBranchCheck` to `test_issues_branch_check.py`

## LLM prompt
> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_1.md` exactly.
> This is a pure move: use `mcp__mcp-tools-py__move_symbol` (dry run first), never edit moved
> code by hand. Only import lines and the one `.large-files-allowlist` line may be edited.
> Run the full check suite from the summary; all must pass. Produce exactly one commit.

## WHERE
- Source: `tests/workflows/vscodeclaude/test_issues.py`
- Destination (new): `tests/workflows/vscodeclaude/test_issues_branch_check.py`
- `.large-files-allowlist`

## WHAT
Move class `TestBuildEligibleIssuesWithBranchCheck` (7 tests, currently lines 562–948) verbatim.
No new functions or signatures.

## HOW
1. **Baseline** (no marker filter; record each number in the commit message body):
   - `run_pytest_check(extra_args=["--collect-only", "-q", "tests/workflows/vscodeclaude/test_issues.py"])` → expect 47
   - `run_pytest_check(extra_args=["--collect-only", "-q", "tests/workflows/vscodeclaude/test_issues_branch_requirements.py"])` → expect 5
   - `run_pytest_check(extra_args=["--collect-only", "-q", "tests/workflows/vscodeclaude/"])` → expect 680
   - If `test_issues.py` does not contain `TestBuildEligibleIssuesWithBranchCheck`
     (`list_symbols`), write one line to `pr_info/.blocked.txt` and stop.
2. `move_symbol(source_file="tests/workflows/vscodeclaude/test_issues.py", symbol_names=["TestBuildEligibleIssuesWithBranchCheck"], dest_file="tests/workflows/vscodeclaude/test_issues_branch_check.py", dry_run=True)`.
   If the dry run touches any file other than these two, write one line to
   `pr_info/.blocked.txt` and stop. Otherwise run it with `dry_run=False`.
3. Fix imports (ruff `F401` / mypy show leftovers and gaps). Expected end state:
   - `test_issues_branch_check.py`:
     `from typing import Any`, `from unittest.mock import Mock`, `import pytest`,
     `from mcp_coder.mcp_workspace_github import IssueData`,
     `from mcp_coder.workflows.vscodeclaude.issues import build_eligible_issues_with_branch_check`,
     `from tests.github_factories import make_issue_data`. No module docstring required.
   - `test_issues.py`: remove `from typing import Any`; `IssueData` leaves the
     `mcp_workspace_github` import (keep `RepoIdentifier`); `build_eligible_issues_with_branch_check`
     leaves the `issues` import list. Keep `Mock`, `pytest`, `make_issue_data` and the other 8
     functions. Module docstring and method-local `_get_status_priority` imports untouched.
4. Remove the line `tests/workflows/vscodeclaude/test_issues.py` from `.large-files-allowlist`.
   Keep `tests/cli/commands/coordinator/test_core.py`.
5. Run the check suite from the summary.

## ALGORITHM
```
record baseline collect counts
dry-run move_symbol -> verify only 2 files touched
apply move_symbol
trim/add imports until ruff F401 + mypy are clean
remove allowlist line
run checks + compare collect counts
```

## DATA — expected results
- `--collect-only -q`: `test_issues.py` 40, `test_issues_branch_check.py` 7,
  `test_issues_branch_requirements.py` 5, `tests/workflows/vscodeclaude/` 680 (unchanged).
- `test_issues.py` ~560 lines, `test_issues_branch_check.py` ~400 lines; `check_file_size` passes
  with no stale allowlist entry.
- Compact diff: only import hunks, new file header, moved-block summary, blank-line hunks,
  one allowlist removal.

## Commit
`test(vscodeclaude): move branch-check tests to test_issues_branch_check.py (#1316)`

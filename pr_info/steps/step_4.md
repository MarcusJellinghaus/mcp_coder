# Step 4 — Move eligibility classes → `test_core_eligibility.py`

## LLM prompt

> Read `pr_info/steps/summary.md`, then do `pr_info/steps/step_4.md`. This is a pure refactor:
> move both classes in one `mcp__mcp-tools-py__move_symbol` call (dry run first). Edit only
> imports, the stale docstring bullets and, if flagged, the allowlist entry. Run every check
> listed. The step ends in exactly one commit.

## WHERE

- Source: `tests/cli/commands/coordinator/test_core.py`
- Destination (**new**): `tests/cli/commands/coordinator/test_core_eligibility.py`
- Possibly modified: `.large-files-allowlist`

## WHAT

Move these classes in one call, in source order (5 tests in total):

| Class | Tests | Tests |
|---|---:|---|
| `TestGetEligibleIssues` | 1 | `core.get_eligible_issues` |
| `TestGetCachedEligibleIssues` | 4 | `core.get_cached_eligible_issues` |

`TestGetCachedEligibleIssues` has two class-level fixtures, `sample_issue` and
`mock_issue_manager`.

## HOW

1. **Pre-counts:** run `--collect-only -q` on each path below and note the numbers.

   | Path | Expected |
   |---|---:|
   | `test_core.py` | 37 |
   | `tests/cli/commands/coordinator/` | — |
   | whole suite | — |

2. **Dry run:**
   - Call `move_symbol(..., symbol_names=["TestGetEligibleIssues", "TestGetCachedEligibleIssues"],
     dest_file="tests/cli/commands/coordinator/test_core_eligibility.py", dry_run=True)`.
   - If it lists files other than the source and the destination: write one line to
     `pr_info/.blocked.txt` and stop.
3. **Move:** run the same call without `dry_run`.
4. **Check the fixtures:** `sample_issue` and `mock_issue_manager` must still sit inside
   `TestGetCachedEligibleIssues`. If they don't: write one line to `pr_info/.blocked.txt`
   and stop.
5. **Destination imports**, exactly:
   ```python
   from unittest.mock import MagicMock, Mock, patch

   import pytest

   from mcp_coder.cli.commands.coordinator import get_cached_eligible_issues, get_eligible_issues
   from mcp_coder.mcp_workspace_github import IssueData, RepoIdentifier
   from tests.github_factories import make_issue_data
   ```
   - If the tool imported from `coordinator.core`, rewrite the import to the package.
   - Leave the stale docstring reference in `TestGetCachedEligibleIssues` unchanged
     (`tests/utils/github_operations/test_issues.cache.py`). It was stale before this move.
6. **`test_core.py`:**
   - Remove these now-unused imports: `Mock`, `get_cached_eligible_issues`, `get_eligible_issues`,
     `RepoIdentifier`. Keep the rest, which the dispatch classes still use.
   - In the module docstring, delete only these two bullets:
     - `- Issue filtering functions (get_eligible_issues)`
     - `- Cached issue retrieval (get_cached_eligible_issues)`
7. **Allowlist:** run `check_file_size`. If it reports
   `tests/cli/commands/coordinator/test_core.py` as a stale allowlist entry, remove that line
   from `.large-files-allowlist`.

## ALGORITHM

```
record counts -> dry-run -> move 2 classes in one call
verify class-level fixtures stayed in place
set destination imports, drop unused imports + 2 stale bullets in test_core.py
check_file_size -> remove stale allowlist entry if flagged
format, ruff, pylint, mypy, pytest, collect counts
```

## DATA — expected after the step

| Path | Expected |
|---|---:|
| `test_core.py` | 32 |
| `test_core_eligibility.py` | 5 |
| `tests/cli/commands/coordinator/` | unchanged |
| whole suite | unchanged |

Run `-q tests/cli/commands/coordinator/test_core_eligibility.py` → 5 passed.

## Checks

- `run_format_code`
- `run_ruff_check`
- `run_pylint_check`
- `run_mypy_check`
- fast unit `run_pytest_check` with `-n auto`
- `check_file_size`: passes, and reports no stale entries.

## Commit

`test(coordinator): split eligibility tests into test_core_eligibility.py`

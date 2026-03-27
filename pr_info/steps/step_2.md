# Step 2: Create test_get_branch_with_pr_fallback.py and delete original

> **Context**: See `pr_info/steps/summary.md` for full issue context (#539).

## Goal

Extract the largest test class (`TestGetBranchWithPRFallback`) into its own file, then delete the original `test_branch_resolution.py`. After this step, the split is complete.

## LLM Prompt

```
Implement step 2 of pr_info/steps/summary.md (issue #539).

Read the existing file tests/utils/github_operations/issues/test_branch_resolution.py.

1. Create tests/utils/github_operations/issues/test_get_branch_with_pr_fallback.py
   — move TestGetBranchWithPRFallback class verbatim
   — remove the local mock_manager fixture (uses conftest from step 1)
   — only include imports this file actually needs

2. Delete tests/utils/github_operations/issues/test_branch_resolution.py

Rules:
- Move code verbatim — no logic changes
- Only adjust imports to what the file actually needs
- Keep the pylint disable comment for protected-access
- Run pylint, pytest (unit tests only), and mypy after changes
- Commit: "refactor: complete split of test_branch_resolution.py (#539)"
```

## WHERE — Files

### Create: `tests/utils/github_operations/issues/test_get_branch_with_pr_fallback.py`

### Delete: `tests/utils/github_operations/issues/test_branch_resolution.py`

## WHAT — Contents

### test_get_branch_with_pr_fallback.py (~710 lines)

- **Module docstring**: `"""Unit tests for IssueBranchManager.get_branch_with_pr_fallback() method."""`
- **Imports**:
  - `from typing import Any`
  - `from unittest.mock import Mock`
  - `import pytest`
  - `from github import GithubException`
  - `from mcp_coder.utils.github_operations.issues import IssueBranchManager`
- **Class**: `TestGetBranchWithPRFallback` — all 20 test methods moved verbatim
- **pylint disable**: `protected-access` (tests access `_repository`, `_github_client`, `_get_repository`, `_search_branches_by_pattern`)
- **No local `mock_manager` fixture** — uses the one from `conftest.py`

## HOW — Integration

- `mock_manager` fixture is injected by pytest from `conftest.py` (created in step 1)
- All 20 test methods reference `mock_manager` as a parameter — no code changes needed, pytest discovers it automatically
- Deleting the original file removes the duplicate tests that co-existed during step 1

## DATA — Test methods moved (all 20)

```
test_linked_branch_found_returns_branch_name
test_no_linked_branch_single_pr_returns_branch (parametrized x2)
test_no_linked_branch_multiple_prs_returns_none
test_no_linked_branch_no_prs_returns_none
test_invalid_issue_number_returns_none
test_graphql_error_returns_none
test_repository_not_found_returns_none
test_malformed_timeline_response_returns_none
test_issue_not_found_in_timeline_returns_none
test_closed_prs_filtered_out
test_non_pr_cross_references_filtered_out
test_multiple_linked_branches_returns_none
test_closed_pr_with_existing_branch
test_closed_pr_with_deleted_branch
test_merged_pr_not_matched
test_closed_pr_25_check_cap
test_closed_pr_most_recent_preferred
test_closed_pr_prefers_open_pr
test_pattern_fallback_used_when_no_prs
test_pattern_fallback_not_called_when_linked_branch_found
```

## Verification

1. `mcp__tools-py__run_pylint_check` — all files pass
2. `mcp__tools-py__run_pytest_check` with `-n auto -m "not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration and not langchain_integration and not llm_integration"` — all 32 tests pass across the 3 new files
3. `mcp__tools-py__run_mypy_check` — no type errors
4. Confirm `test_branch_resolution.py` no longer exists

## Commit

```
refactor: complete split of test_branch_resolution.py (#539)
```

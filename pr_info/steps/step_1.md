# Step 1: Create conftest.py + two smaller test files

> **Context**: See `pr_info/steps/summary.md` for full issue context (#539).

## Goal

Create the shared `conftest.py` and extract the two smaller test classes (`TestExtractPrsByStates`, `TestSearchBranchesByPattern`) into their own files. The original file remains until step 2.

## LLM Prompt

```
Implement step 1 of pr_info/steps/summary.md (issue #539).

Read the existing file tests/utils/github_operations/issues/test_branch_resolution.py.

Create 3 new files in tests/utils/github_operations/issues/:

1. conftest.py — shared mock_manager fixture
2. test_extract_prs_by_states.py — TestExtractPrsByStates class
3. test_search_branches_by_pattern.py — TestSearchBranchesByPattern + _make_git_ref helper

Rules:
- Move code verbatim — no logic changes
- Only adjust imports to what each file actually needs
- Remove the local mock_manager fixture from TestSearchBranchesByPattern (it will use conftest)
- Keep the pylint disable comment for protected-access where needed
- Run pylint, pytest (unit tests only), and mypy after creating the files
- Commit: "refactor: extract conftest and smaller test classes from test_branch_resolution"
```

## WHERE — Files to Create

### `tests/utils/github_operations/issues/conftest.py`

### `tests/utils/github_operations/issues/test_extract_prs_by_states.py`

### `tests/utils/github_operations/issues/test_search_branches_by_pattern.py`

## WHAT — Contents of Each File

### conftest.py (~30 lines)

- **Imports**: `Path`, `Mock`, `patch`, `pytest`, `IssueBranchManager`
- **Fixture**: `mock_manager()` — the exact fixture body from `TestGetBranchWithPRFallback` or `TestSearchBranchesByPattern` (they are identical), promoted to module-level pytest fixture

### test_extract_prs_by_states.py (~110 lines)

- **Imports**: `Any`, `Mock`, `pytest`, `IssueBranchManager`
- **Class**: `TestExtractPrsByStates` — moved verbatim (6 tests + `_make_pr_node` static helper)
- **Note**: This class does NOT use `mock_manager` — no conftest dependency
- **pylint disable**: `protected-access` (tests call `_extract_prs_by_states`)

### test_search_branches_by_pattern.py (~270 lines)

- **Imports**: `Mock`, `patch`, `pytest`, `IssueBranchManager`
- **Module-level helper**: `_make_git_ref()` — moved verbatim from original file
- **Class**: `TestSearchBranchesByPattern` — moved verbatim, **minus** the local `mock_manager` fixture (uses conftest instead)
- **pylint disable**: `protected-access` (tests call `_search_branches_by_pattern`)

## HOW — Integration

- `conftest.py` is auto-discovered by pytest for all tests in the `issues/` directory
- No changes to `__init__.py`
- The original `test_branch_resolution.py` still exists (deleted in step 2), so both old and new tests will run — that's fine, they're independent

## DATA — Fixture signature

```python
@pytest.fixture
def mock_manager() -> IssueBranchManager:
    """Create a mock IssueBranchManager for testing."""
    # ... exact same body as existing fixture ...
```

## Verification

1. `mcp__tools-py__run_pylint_check` — all new files pass
2. `mcp__tools-py__run_pytest_check` with `-n auto -m "not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration and not langchain_integration"` — all tests pass (both old and new)
3. `mcp__tools-py__run_mypy_check` — no type errors

## Commit

```
refactor: extract conftest and smaller test classes from test_branch_resolution
```

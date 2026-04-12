# Step 2: Delete mcp_coder/formatters package and tests

**Commit message:** `refactor: delete mcp_coder/formatters package and tests`

**Context:** See `pr_info/steps/summary.md` for full issue context (#737).

## Goal

Delete the entire `src/mcp_coder/formatters/` package and `tests/formatters/`
directory. After step 1, the package has zero production callers — this step
is purely file deletion.

## WHERE — Files to delete

### Source (6 files)
- `src/mcp_coder/formatters/__init__.py`
- `src/mcp_coder/formatters/black_formatter.py`
- `src/mcp_coder/formatters/isort_formatter.py`
- `src/mcp_coder/formatters/config_reader.py`
- `src/mcp_coder/formatters/models.py`
- `src/mcp_coder/formatters/utils.py`

### Tests (9 files)
- `tests/formatters/__init__.py`
- `tests/formatters/test_black_formatter.py`
- `tests/formatters/test_isort_formatter.py`
- `tests/formatters/test_config_reader.py`
- `tests/formatters/test_models.py`
- `tests/formatters/test_utils.py`
- `tests/formatters/test_main_api.py`
- `tests/formatters/test_debug.py`
- `tests/formatters/test_integration.py`

## WHAT — No new code

This step is deletion-only. No functions added or modified.

## HOW — Deletion procedure

1. Delete all 15 files listed above
2. Run quality checks — they will fail because `.importlinter` and `tach.toml`
   still reference `mcp_coder.formatters`. That is expected and fixed in step 4.
   However, pytest/pylint/mypy should pass since no code imports the package anymore.

**Important:** After this step, `lint_imports` and `tach check` will fail.
This is intentional — step 4 fixes the config files. The core checks
(pytest, pylint, mypy) must still pass.

## DATA — No data changes

## Verification

```
mcp__tools-py__run_pytest_check   (unit tests, exclude integration)
mcp__tools-py__run_pylint_check
mcp__tools-py__run_mypy_check
```

Note: `lint_imports` / `tach check` will fail until step 4. That's OK — we commit
this as an atomic step with step 4 if needed, or accept the intermediate state.

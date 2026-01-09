# Step 6: Final Verification and Code Quality Checks

## Overview

Complete the remaining verification tasks identified during code review. This step ensures all code quality checks pass, CLI commands work correctly, and the implementation is ready for pull request.

## WHERE

No new files created. Verification only.

**Files to verify:**
- `src/mcp_coder/cli/commands/define_labels.py` - Exception handling
- `src/mcp_coder/workflows/utils.py` - ValueError pattern
- `tests/cli/commands/test_define_labels.py` - Test coverage

## WHAT

### Part A: Verify Exception Handling Pattern

Confirm `apply_labels` raises `RuntimeError` on API errors (not `sys.exit`).

**Test case exists at:** `tests/cli/commands/test_define_labels.py::TestApplyLabels::test_apply_labels_api_error_raises_runtime_error`

```python
# Expected behavior in apply_labels():
except Exception as e:
    raise RuntimeError(f"Failed to create label '{label_name}': {e}") from e
```

### Part B: Run Full Test Suite

Execute test suite excluding slow integration tests:

```bash
pytest tests/ -m "not github_integration and not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration" -n auto
```

### Part C: Verify CLI Commands

Test that CLI commands work correctly:

```bash
# Help for define-labels command
mcp-coder define-labels --help

# Main help includes define-labels
mcp-coder help
```

### Part D: Code Quality Checks

Run all three code quality tools via MCP:

1. **Pylint** - `mcp__code-checker__run_pylint_check()`
2. **Pytest** - `mcp__code-checker__run_pytest_check()`
3. **Mypy** - `mcp__code-checker__run_mypy_check()`

## HOW

### Exception pattern verification:

```python
# Quick verification script
python -c "
from mcp_coder.cli.commands.define_labels import apply_labels
from pathlib import Path
from unittest.mock import patch, MagicMock

# Mock LabelsManager to raise an exception
with patch('mcp_coder.cli.commands.define_labels.LabelsManager') as mock:
    mock_instance = MagicMock()
    mock_instance.get_labels.return_value = []
    mock_instance.create_label.side_effect = Exception('API error')
    mock.return_value = mock_instance
    
    try:
        apply_labels(Path('.'), [('test', 'abc123', 'desc')], dry_run=False)
        print('FAIL: No exception raised')
    except RuntimeError as e:
        print(f'OK: RuntimeError raised: {e}')
    except SystemExit:
        print('FAIL: sys.exit() called instead of raising exception')
"
```

## ALGORITHM

```
1. Run existing test for RuntimeError behavior
2. Execute full test suite (non-integration)
3. Test CLI help commands manually
4. Run pylint via MCP tool
5. Run mypy via MCP tool
6. Fix any issues found
```

## DATA

**Expected test results:**
- All tests pass
- No pylint errors (warnings acceptable)
- No mypy type errors

**CLI output verification:**
- `mcp-coder define-labels --help` shows: `--project-dir`, `--dry-run` options
- `mcp-coder help` includes: `define-labels` in command list

## LLM Prompt

```
Please implement Step 6 of the implementation plan in `pr_info/steps/step_6.md`.

Context: See `pr_info/steps/summary.md` for the overall plan.

Task: Complete final verification and code quality checks:

1. Verify exception handling pattern:
   - Run `pytest tests/cli/commands/test_define_labels.py::TestApplyLabels::test_apply_labels_api_error_raises_runtime_error -v`
   - Confirm test passes (apply_labels raises RuntimeError, not sys.exit)

2. Run full test suite:
   - Use MCP tool: `mcp__code-checker__run_pytest_check(extra_args=["-n", "auto", "-m", "not github_integration and not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration"])`
   - All tests should pass

3. Verify CLI commands work:
   - Run `mcp-coder define-labels --help` and verify it shows usage
   - Run `mcp-coder help` and verify define-labels appears in command list

4. Run code quality checks via MCP tools:
   - `mcp__code-checker__run_pylint_check()` - fix any errors
   - `mcp__code-checker__run_mypy_check()` - fix any type errors

5. If any issues found:
   - Fix the issues
   - Re-run the failing check
   - Update this step's verification checklist

6. Mark all tasks complete in TASK_TRACKER.md
```

## Verification

### Exception pattern:
- [ ] Test `test_apply_labels_api_error_raises_runtime_error` passes
- [ ] `apply_labels` raises `RuntimeError` on API errors (verified via test)

### Test suite:
- [ ] All unit tests pass (excluding integration markers)
- [ ] No test failures or errors

### CLI commands:
- [ ] `mcp-coder define-labels --help` displays usage with `--project-dir` and `--dry-run`
- [ ] `mcp-coder help` shows `define-labels` in command list

### Code quality (MCP tools):
- [ ] Pylint: No errors (warnings acceptable)
- [ ] Mypy: No type errors
- [ ] Pytest: All tests pass

## Acceptance Criteria

After this step completes:
- All code quality checks pass
- CLI commands work as documented
- Implementation is ready for pull request

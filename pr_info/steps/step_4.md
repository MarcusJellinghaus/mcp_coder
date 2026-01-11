# Step 4: Verify All Tests Pass

## LLM Prompt
```
Reference: pr_info/steps/summary.md and this step file.

Run the test suite to verify the refactoring is complete and all tests pass.
```

---

## WHERE: Test Locations

| Test File | Purpose |
|-----------|---------|
| `tests/workflow_utils/test_commit_operations.py` | Unit tests for moved module |
| `tests/cli/commands/test_commit.py` | Tests for commit CLI command |
| `tests/workflows/implement/test_task_processing.py` | Tests for task processing workflow |

---

## WHAT: Verification Steps

### 1. Run commit_operations unit tests

```bash
pytest tests/workflow_utils/test_commit_operations.py -v
```

**Expected**: All tests pass

### 2. Run commit CLI tests

```bash
pytest tests/cli/commands/test_commit.py -v
```

**Expected**: All tests pass

### 3. Run task_processing tests

```bash
pytest tests/workflows/implement/test_task_processing.py -v
```

**Expected**: All tests pass

### 4. Run full test suite (excluding integration tests)

```bash
pytest -m "not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration" -v
```

**Expected**: All tests pass

### 5. Run code quality checks

```bash
# Pylint
pylint src/mcp_coder/workflow_utils/commit_operations.py

# Mypy
mypy src/mcp_coder/workflow_utils/commit_operations.py
```

**Expected**: No new errors introduced

---

## HOW: Troubleshooting Common Issues

### Import Error
If you see `ModuleNotFoundError: No module named 'mcp_coder.utils.commit_operations'`:
- Check Step 3 was completed for all dependent files
- Verify no other files import from the old location

### Mock Path Error
If tests fail with mock-related errors:
- Ensure all `@patch` decorators use `mcp_coder.workflow_utils.commit_operations`
- Check both `test_commit_operations.py` and `test_commit.py`

### File Not Found
If the module can't be imported:
- Verify Step 1 created the file at correct location
- Check the file has correct Python syntax

---

## DATA: Expected Test Counts

| Test File | Approximate Test Count |
|-----------|----------------------|
| `test_commit_operations.py` | ~31 tests |
| `test_commit.py` | ~25 tests |
| `test_task_processing.py` | ~10 tests |

---

## Verification Complete Checklist

- [ ] `tests/workflow_utils/test_commit_operations.py` - All tests pass
- [ ] `tests/cli/commands/test_commit.py` - All tests pass
- [ ] `tests/workflows/implement/test_task_processing.py` - All tests pass
- [ ] Full test suite passes (excluding integration markers)
- [ ] No pylint errors in moved file
- [ ] No mypy errors in moved file
- [ ] Old file `src/mcp_coder/utils/commit_operations.py` is deleted
- [ ] Old test file `tests/utils/test_commit_operations.py` is deleted

---

## Success Criteria

The refactoring is complete when:
1. All tests pass
2. No references to `utils.commit_operations` exist in the codebase
3. The architectural violation is resolved (commit_operations is now in the application layer)

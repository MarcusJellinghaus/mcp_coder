# Step 3: Run Quality Checks and Verify Backward Compatibility

## Summary Reference
See [summary.md](summary.md) for overall context and design decisions.

## Objective
Run all quality checks (pylint, pytest, mypy) to ensure the implementation is correct and maintains backward compatibility with existing task trackers.

---

## WHERE: Files to Verify

| File | Check Type |
|------|------------|
| `src/mcp_coder/workflow_utils/task_tracker.py` | pylint, mypy |
| `tests/workflow_utils/test_task_tracker.py` | pylint, mypy, pytest |

---

## WHAT: Quality Checks to Run

### 1. Pytest - All Task Tracker Tests
```bash
pytest tests/workflow_utils/test_task_tracker.py -v
```

**Expected**: All tests pass, including:
- Existing tests (backward compatibility)
- New `TestMultiPhaseTaskTracker` tests

### 2. Pytest - Integration Tests
```bash
pytest tests/test_integration_task_tracker.py -v
```

**Expected**: All integration tests pass.

### 3. Pylint - Source and Tests
```bash
pylint src/mcp_coder/workflow_utils/task_tracker.py
pylint tests/workflow_utils/test_task_tracker.py
```

**Expected**: No errors (warnings acceptable).

### 4. Mypy - Type Checking
```bash
mypy src/mcp_coder/workflow_utils/task_tracker.py
mypy tests/workflow_utils/test_task_tracker.py
```

**Expected**: No type errors.

---

## HOW: Run All Checks

Use the MCP code checker tools:

```python
# Run all checks at once
run_all_checks(
    target_directories=["src/mcp_coder/workflow_utils", "tests/workflow_utils"],
    categories=["error", "fatal", "warning"]
)
```

Or individually:
```python
run_pytest_check(extra_args=["tests/workflow_utils/test_task_tracker.py", "-v"])
run_pylint_check(target_directories=["src/mcp_coder/workflow_utils"])
run_mypy_check(target_directories=["src/mcp_coder/workflow_utils"])
```

---

## ALGORITHM: Verification Checklist

```
1. Run pytest on task_tracker tests → All PASS
2. Run pytest on integration tests → All PASS  
3. Run pylint on modified files → No errors
4. Run mypy on modified files → No type errors
5. Verify real-world examples work (from issue #156)
```

---

## DATA: Expected Test Results

### Existing Tests (Must Pass)
| Test Class | Test Count | Expected |
|------------|------------|----------|
| `TestTaskInfo` | 2 | PASS |
| `TestExceptions` | 2 | PASS |
| `TestReadTaskTracker` | 3 | PASS |
| `TestFindImplementationSection` | 6 | PASS |
| `TestParseTaskLines` | 11 | PASS |
| `TestGetIncompleteTasksInternal` | 5 | PASS |
| `TestGetIncompleteTasks` | 8 | PASS |
| `TestHasIncompleteWork` | 3 | PASS |
| `TestGetStepProgress` | 4 | PASS |
| `TestIsTaskDone` | 10 | PASS |
| `TestNormalizeTaskName` | 5 | PASS |

### New Tests (Must Pass)
| Test Class | Test Count | Expected |
|------------|------------|----------|
| `TestMultiPhaseTaskTracker` | 5 | PASS |

---

## Real-World Verification

Test with the exact examples from issue #156:

### Example 1: Phase-Based Tracker
```python
content = """
## Tasks

## Phase 1: Initial Implementation (Steps 1-5) ✅ COMPLETE
### Step 1: Config Template Infrastructure (TDD)
- [x] Write tests for create_default_config

## Phase 2: Code Review Fixes (Steps 6-9) 📋 NEW
### Step 6: Fix Field Name Inconsistency
- [ ] Search README.md for all occurrences of test_job_path

## Pull Request
- [ ] Review all implementation steps are complete
"""

incomplete = _get_incomplete_tasks(content)
assert "Search README.md for all occurrences of test_job_path" in incomplete
assert "Review all implementation steps are complete" not in incomplete
```

### Example 2: Step-Based Tracker (Original Format)
```python
content = """
## Tasks

### Step 1: Write Tests
- [x] Create tests
- [x] Run tests

### Step 2: Implement Class
- [ ] Add class to github_utils.py

### Pull Request
- [ ] Create pull request
"""

incomplete = _get_incomplete_tasks(content)
assert incomplete == ["Add class to github_utils.py"]
```

---

## Common Issues and Fixes

| Issue | Symptom | Fix |
|-------|---------|-----|
| Import error in tests | `NameError: _find_implementation_section` | Add import to test file |
| Type hint issue | mypy error on fixture | Use `-> str` return type |
| Missing logger import | `NameError: logger` | Add `import logging` and `logger = logging.getLogger(__name__)` |

---

## LLM Prompt for Step 3

```
You are implementing Step 3 of issue #156: Support for Multi-Phase Task Tracker.

CONTEXT:
- See pr_info/steps/summary.md for overall design
- See pr_info/steps/Decisions.md for design decisions
- See pr_info/steps/step_3.md for this step's details
- Steps 1 and 2 added tests and implementation

TASK:
1. Run all quality checks using MCP tools
2. Fix any issues found
3. Verify backward compatibility with existing tests
4. Test with real-world examples from issue #156

REQUIREMENTS:
- All existing tests must pass (backward compatibility)
- All new tests must pass
- No pylint errors
- No mypy type errors

COMMANDS TO RUN:
1. run_pytest_check(extra_args=["tests/workflow_utils/test_task_tracker.py", "-v"])
2. run_pytest_check(extra_args=["tests/test_integration_task_tracker.py", "-v"])
3. run_pylint_check(target_directories=["src/mcp_coder/workflow_utils", "tests/workflow_utils"])
4. run_mypy_check(target_directories=["src/mcp_coder/workflow_utils", "tests/workflow_utils"])

SUCCESS CRITERIA:
- 0 test failures
- 0 pylint errors
- 0 mypy errors
```

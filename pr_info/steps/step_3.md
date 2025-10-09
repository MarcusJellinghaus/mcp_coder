# Step 3: Quality Checks and Integration Test

## LLM Prompt
```
Reference: pr_info/steps/summary.md

Implement Step 3: Run quality checks and extend integration test.

Requirements:
1. Extend one integration test to verify get_issue() with real API
2. Run all quality checks using MCP tools:
   - pylint (errors only)
   - pytest (unit tests, skip slow integration tests)
   - mypy (strict type checking)
3. Fix any issues found
4. Verify all checks pass

Follow the summary document for architectural context.
```

## WHERE

### Integration Test
**File**: `tests/utils/github_operations/test_issue_manager_integration.py`
**Location**: Extend existing test method to add get_issue() verification

### Quality Checks
**Tool**: MCP code-checker tools

## WHAT

### Integration Test Extension
```python
# Add to existing integration test
def test_create_and_manage_issue():
    # ... existing code ...
    
    # NEW: Test get_issue()
    retrieved = manager.get_issue(issue_number)
    assert retrieved["number"] == issue_number
    assert retrieved["title"] == title
    assert "assignees" in retrieved
    assert isinstance(retrieved["assignees"], list)
```

### Quality Check Commands
```python
# 1. Pylint - errors only
mcp__code-checker__run_pylint_check()

# 2. Pytest - fast unit tests only
mcp__code-checker__run_pytest_check(
    extra_args=[
        "-n", "auto",
        "-m", "not git_integration and not claude_integration and not formatter_integration and not github_integration"
    ]
)

# 3. Mypy - strict type checking
mcp__code-checker__run_mypy_check()
```

## HOW

### Integration Points
- **Test Extension**: Add get_issue() call to existing test flow
- **Round-trip Verification**: Create issue → get issue → verify fields match
- **MCP Tools**: Use exact tool names per CLAUDE.md requirements

### Error Resolution
If checks fail:
1. Review error messages
2. Fix issues in source code
3. Re-run specific check
4. Repeat until all pass

## ALGORITHM

### Integration Test Logic
```
1. Use existing test that creates an issue
2. After issue creation, call get_issue()
3. Verify returned data matches created issue
4. Assert assignees field exists and is list
5. Clean up (existing teardown handles this)
```

### Quality Check Process
```
1. Run pylint - verify no errors
2. Run pytest - verify all unit tests pass
3. Run mypy - verify no type errors
4. If any fail, fix and re-run
5. Document all checks passed
```

## DATA

### Integration Test Assertions
```python
# Verify basic fields
assert retrieved["number"] == issue_number
assert retrieved["title"] == expected_title
assert retrieved["state"] == "open"

# Verify new field
assert "assignees" in retrieved
assert isinstance(retrieved["assignees"], list)
```

### Expected Quality Check Results
```
✅ Pylint: No errors found
✅ Pytest: All tests passed (unit tests only)
✅ Mypy: No type errors found
```

## Verification Steps

### 1. Integration Test
```bash
# Run specific integration test
pytest tests/utils/github_operations/test_issue_manager_integration.py -v
```

### 2. Pylint Check
```python
mcp__code-checker__run_pylint_check()
# Expected: No errors (conventions/refactors acceptable)
```

### 3. Pytest Check
```python
mcp__code-checker__run_pytest_check(
    extra_args=["-n", "auto", "-m", "not git_integration and not claude_integration and not formatter_integration and not github_integration"]
)
# Expected: All unit tests pass
```

### 4. Mypy Check
```python
mcp__code-checker__run_mypy_check()
# Expected: No type errors
```

## Success Criteria
- ✅ Integration test includes get_issue() verification
- ✅ All pylint errors resolved
- ✅ All unit tests pass
- ✅ No mypy type errors
- ✅ Code follows existing patterns

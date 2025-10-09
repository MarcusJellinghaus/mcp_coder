# Step 4: Quality Checks and Integration Test

## LLM Prompt
```
Reference: pr_info/steps/summary.md

Implement Step 4: Run quality checks and extend integration test.

Requirements:
1. Add Section 1.5 to integration test `test_complete_issue_workflow` after issue creation
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
**Method**: `test_complete_issue_workflow`
**Location**: Add Section 1.5 right after Section 1 (Issue Creation)

## WHAT

### Integration Test Extension
Add Section 1.5 after issue creation to verify `get_issue()`:
```python
# ============================================================
# SECTION 1.5: Get Issue Verification
# ============================================================
print("\n" + "=" * 60)
print("SECTION 1.5: Get Issue Verification")
print("=" * 60)

retrieved = issue_manager.get_issue(issue_number)
assert retrieved["number"] == issue_number
assert retrieved["title"] == issue_title
assert retrieved["body"] == issue_body
assert retrieved["state"] == "open"
assert "assignees" in retrieved
assert isinstance(retrieved["assignees"], list)
print(f"✓ Retrieved issue #{issue_number} successfully")
print(f"  Assignees: {retrieved['assignees']}")
```

### Quality Checks
Run using MCP tools (pseudo-code for LLM):
```python
# 1. Pylint - errors only
mcp__code-checker__run_pylint_check()

# 2. Pytest - fast unit tests only
mcp__code-checker__run_pytest_check(
    extra_args=["-n", "auto", "-m", "not git_integration and not claude_integration and not formatter_integration and not github_integration"]
)

# 3. Mypy - strict type checking
mcp__code-checker__run_mypy_check()
```

## HOW

### Integration Test
- Insert new section between Section 1 and Section 2
- Use the `issue_number` variable from Section 1
- Verify round-trip: create → get → compare fields
- Print success messages matching existing format

### Quality Checks
- Run checks in order: pylint, pytest, mypy
- If any check fails, fix issues and re-run
- Document that all checks passed

## Verification Steps

### 1. Integration Test
```bash
pytest tests/utils/github_operations/test_issue_manager_integration.py::TestIssueManagerIntegration::test_complete_issue_workflow -v
```

### 2. Quality Checks
Expected results:
- ✅ Pylint: No errors
- ✅ Pytest: All unit tests pass
- ✅ Mypy: No type errors

## Success Criteria
- Integration test includes get_issue() verification
- All quality checks pass
- No regressions in existing functionality

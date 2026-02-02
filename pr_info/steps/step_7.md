# Step 7: Run all checks and verify

## LLM Prompt
```
You are implementing Issue #365: Refactor coordinator - Remove _get_coordinator() late-binding pattern.
See pr_info/steps/summary.md for full context.

This is Step 7: Run all quality checks (pylint, mypy, pytest) to verify the refactoring
is complete and correct.
```

## WHERE

This step runs verification commands - no files to modify (unless issues are found).

## WHAT

### Run Quality Checks

1. **pylint** - Check for import errors, unused imports, code style
2. **mypy** - Verify type annotations are still correct
3. **pytest** - Run all tests, especially coordinator tests

## HOW

### Check Commands

```bash
# Run pylint on modified files
pylint src/mcp_coder/utils/github_operations/issue_cache.py
pylint src/mcp_coder/cli/commands/coordinator/core.py
pylint src/mcp_coder/cli/commands/coordinator/commands.py
pylint src/mcp_coder/cli/commands/coordinator/__init__.py

# Run mypy on the package
mypy src/mcp_coder/cli/commands/coordinator/

# Run coordinator tests specifically
pytest tests/cli/commands/coordinator/ -v

# Run full test suite (optional but recommended)
pytest tests/ -v
```

### Using MCP Tools

```python
# Via mcp-code-checker
mcp__code-checker__run_pylint_check(target_directories=["src/mcp_coder/cli/commands/coordinator"])
mcp__code-checker__run_mypy_check(target_directories=["src/mcp_coder/cli/commands/coordinator"])
mcp__code-checker__run_pytest_check(extra_args=["tests/cli/commands/coordinator/", "-v"])
```

## ALGORITHM
```
1. Run pylint on modified source files
2. Fix any import errors or unused import warnings
3. Run mypy on coordinator package
4. Fix any type errors
5. Run pytest on coordinator tests
6. Fix any failing tests
7. If all pass, run full test suite for regression check
```

## EXPECTED ISSUES AND FIXES

### Potential pylint warnings:
- **Unused imports**: If `ModuleType` is no longer used in core.py, remove it
- **Import order**: May need to reorder imports after adding new ones

### Potential mypy errors:
- Should be none if imports are correct

### Potential pytest failures:
- Test failures indicate patch paths weren't updated correctly
- Check that patch path matches where the function is imported

## VERIFICATION CHECKLIST

- [ ] `_get_coordinator()` function removed from `core.py`
- [ ] All `coordinator = _get_coordinator()` patterns replaced
- [ ] Tests updated to patch at `...core.<name>` or `...commands.<name>`
- [ ] Test-only re-exports removed from `__init__.py`
- [ ] `_update_issue_labels_in_cache` renamed to `update_issue_labels_in_cache`
- [ ] pylint passes with no errors
- [ ] mypy passes with no errors
- [ ] All pytest tests pass

## SUCCESS CRITERIA

All checks pass:
```
pylint: 0 errors
mypy: Success: no issues found
pytest: all tests passed
```

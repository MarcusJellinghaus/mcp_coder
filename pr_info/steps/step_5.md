# Step 5: Run Verification Checks

## LLM Prompt

```
Read pr_info/steps/summary.md for context.

Implement Step 5: Run all verification checks to ensure the refactoring is complete and correct.

1. Run import linter to verify architectural boundaries
2. Run tach to verify module dependencies
3. Run pytest for the moved tests
4. Run pytest for coordinator tests (to ensure they still work)
5. Run mypy type checking
6. Run pylint for errors

Fix any issues found during verification.
```

## WHERE

No file changes - verification only.

## WHAT

### Verification Commands

```bash
# 1. Import Linter
lint-imports

# 2. Tach
tach check

# 3. Run moved tests
pytest tests/utils/github_operations/test_issue_cache.py -v

# 4. Run coordinator tests (should still pass)
pytest tests/cli/commands/coordinator/ -v

# 5. Type checking
mypy src/mcp_coder/utils/github_operations/issue_cache.py
mypy src/mcp_coder/cli/commands/coordinator/core.py

# 6. Pylint
pylint src/mcp_coder/utils/github_operations/issue_cache.py
pylint src/mcp_coder/cli/commands/coordinator/core.py
```

### Using MCP Tools

```python
# Run all checks
mcp__code-checker__run_all_checks(
    target_directories=["src/mcp_coder/utils/github_operations", "src/mcp_coder/cli/commands/coordinator"],
    categories=["error", "fatal", "warning"]
)

# Run specific tests
mcp__code-checker__run_pytest_check(
    extra_args=["tests/utils/github_operations/test_issue_cache.py", "-v"]
)
```

## HOW

The verification ensures:
1. **Import linter**: No architectural boundary violations
2. **Tach**: Module dependencies are valid
3. **Tests pass**: Functionality preserved
4. **Type checking**: No type errors introduced
5. **Linting**: No code quality issues

## ALGORITHM

```
# Verification checklist:
1. Import linter passes (no layer violations)
2. Tach passes (no dependency violations)
3. All test_issue_cache.py tests pass
4. All coordinator tests pass
5. Mypy reports no errors
6. Pylint reports no errors/fatals
```

## Expected Results

### Import Linter
Should pass - moving cache to `utils.github_operations` follows the layered architecture:
- `cli` → `utils` is allowed

### Tach
Should pass - no config changes needed:
- `mcp_coder.cli` already depends on `mcp_coder.utils`

### Tests
All tests should pass with identical behavior.

## DATA

No data changes.

## Troubleshooting

### If import linter fails:
- Check that `issue_cache.py` doesn't import from `cli` layer
- Verify the callback pattern is used correctly

### If tests fail:
- Check patch paths are updated correctly
- Verify logger names match new module path
- Ensure fixtures are accessible from conftest.py

### If type checking fails:
- Add missing type annotations
- Ensure `Callable` types are correctly specified for callbacks

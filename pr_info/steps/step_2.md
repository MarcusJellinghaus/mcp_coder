# Step 2: Verification Checks

## Context
See [summary.md](summary.md) for full context. This step verifies that the file moves were successful and all code quality checks pass.

## WHERE: Verification Scope

- `tests/workflows/vscodeclaude/` - moved test files
- `src/mcp_coder/workflows/vscodeclaude/` - source files (unchanged)

## WHAT: Checks to Run

1. **pytest** - All tests pass
2. **pylint** - No linting errors
3. **mypy** - Type checking passes

## HOW: Using MCP Code Checker Tools

```python
mcp__code-checker__run_pytest_check()
mcp__code-checker__run_pylint_check()
mcp__code-checker__run_mypy_check()
```

## ALGORITHM

```
1. Run mcp__code-checker__run_pytest_check()
2. Verify all tests pass (especially tests/workflows/vscodeclaude/*)
3. Run mcp__code-checker__run_pylint_check()
4. Verify no errors
5. Run mcp__code-checker__run_mypy_check()
6. Verify no type errors
7. If any check fails, investigate and fix
```

## DATA: Expected Results

- pytest: All tests pass, including vscodeclaude tests at new location
- pylint: No errors (warnings acceptable)
- mypy: No type errors

## Success Criteria

All acceptance criteria from issue #363 met:
- [x] Directory `tests/workflows/vscodeclaude/` created
- [x] All 13 test files moved
- [x] `tests/utils/vscodeclaude/` deleted entirely
- [x] pytest passes
- [x] pylint passes
- [x] mypy passes

---

## LLM Prompt

```
Review pr_info/steps/summary.md and pr_info/steps/step_2.md.

Run verification checks to confirm the test file moves were successful:

1. Run mcp__code-checker__run_pytest_check() - verify all tests pass
2. Run mcp__code-checker__run_pylint_check() - verify no linting errors
3. Run mcp__code-checker__run_mypy_check() - verify type checking passes

If any check fails, investigate the cause and fix if it's related to the file moves.

Report the status of each acceptance criterion from issue #363.
```

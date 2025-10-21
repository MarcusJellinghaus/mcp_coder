# Step 5: Remove Legacy Files and Final Validation

## Context
Read `pr_info/steps/summary.md` for full architectural context.

This is the final step - removing the legacy standalone script and batch wrapper, then running comprehensive validation to ensure everything works.

## Objective
Clean up legacy files and validate that the conversion is complete and functional.

---

## Part A: Remove Legacy Files

### WHERE - Files to Delete

1. **`workflows/create_PR.py`** - Standalone script (replaced by `src/mcp_coder/workflows/create_pr/core.py`)
2. **`workflows/create_PR.bat`** - Batch wrapper (no longer needed)

### HOW - Deletion Process

```bash
# Remove standalone Python script
rm workflows/create_PR.py

# Remove batch wrapper
rm workflows/create_PR.bat
```

### VALIDATION - Verify Files Are Gone

```bash
# Confirm files don't exist
ls workflows/create_PR.py 2>/dev/null && echo "ERROR: File still exists!" || echo "✓ create_PR.py removed"
ls workflows/create_PR.bat 2>/dev/null && echo "ERROR: File still exists!" || echo "✓ create_PR.bat removed"
```

---

## Part B: Comprehensive Testing

### Test Suite Execution

Run all tests to ensure nothing broke:

```bash
# Test 1: All create_pr workflow tests
pytest tests/workflows/create_pr/ -v
# Expected: All tests PASS

# Test 2: CLI command tests
pytest tests/cli/commands/test_create_pr.py -v
# Expected: All tests PASS

# Test 3: Integration tests
pytest tests/workflows/test_create_pr_integration.py -v
# Expected: All tests PASS

# Test 4: Legacy compatibility tests
pytest tests/test_create_pr.py -v
# Expected: All tests PASS

# Test 5: Full test suite (comprehensive check)
pytest tests/ -v
# Expected: All tests PASS

# Test 6: Just create_pr related tests
pytest tests/ -k "create_pr" -v
# Expected: All tests PASS
```

### Pytest with Parallel Execution

```bash
# Run create_pr tests with parallel execution (faster)
pytest tests/ -k "create_pr" -n auto -v
# Expected: All tests PASS
```

---

## Part C: Code Quality Validation

### Run All Code Quality Checks

```bash
# Pylint check on new workflow package
pylint src/mcp_coder/workflows/create_pr/
# Expected: No errors

# Pylint check on new CLI command
pylint src/mcp_coder/cli/commands/create_pr.py
# Expected: No errors

# Pylint check on modified CLI main
pylint src/mcp_coder/cli/main.py
# Expected: No errors

# Mypy type checking on workflow package
mypy src/mcp_coder/workflows/create_pr/
# Expected: No type errors

# Mypy type checking on CLI command
mypy src/mcp_coder/cli/commands/create_pr.py
# Expected: No type errors

# Mypy type checking on CLI main
mypy src/mcp_coder/cli/main.py
# Expected: No type errors
```

### Using MCP Code Checker Tools (Recommended)

```bash
# Run pytest with MCP tool
mcp__code-checker__run_pytest_check(
    extra_args=["-n", "auto", "-k", "create_pr"]
)

# Run pylint with MCP tool
mcp__code-checker__run_pylint_check(
    categories=["error", "fatal"]
)

# Run mypy with MCP tool
mcp__code-checker__run_mypy_check(
    strict=True
)
```

---

## Part D: Manual Functional Testing

### Test CLI Command Functionality

```bash
# Test 1: Help text shows create-pr command
mcp-coder --help
# Expected: "create-pr" appears in available commands list

# Test 2: Create-pr specific help
mcp-coder create-pr --help
# Expected: Shows usage, --project-dir and --llm-method options

# Test 3: Verify command is accessible (in a test git repo)
cd /path/to/test/repo
mcp-coder create-pr --help
# Expected: No import errors, help displays correctly
```

### Optional: Full Workflow Test (if safe)

**WARNING:** Only run this in a test repository, NOT production!

```bash
# In a test git repo with clean working directory and feature branch
cd /path/to/test/repo
git checkout -b test-create-pr-command
# Make some test changes, commit them
echo "test" > test.txt
git add test.txt
git commit -m "test: verify create-pr command works"

# Run create-pr (will attempt to create actual PR)
mcp-coder create-pr --llm-method claude_code_cli

# Expected: 
# - Prerequisites check runs
# - PR summary generated
# - PR created (if GitHub configured)
# - Repository cleaned up
# - No errors
```

---

## Part E: Documentation Verification

### Verify Command in Help Text

Check that the new command is properly documented:

```bash
# Main help shows create-pr
mcp-coder --help | grep "create-pr"
# Expected: Line showing "create-pr" with description

# Create-pr help is complete
mcp-coder create-pr --help
# Expected: Shows all options with descriptions
```

---

## ALGORITHM - Validation Process (Pseudocode)

```
1. Delete legacy files (create_PR.py, create_PR.bat)
2. Verify files are gone
3. Run comprehensive test suite:
   - Unit tests (workflows/create_pr/)
   - CLI tests (cli/commands/test_create_pr.py)
   - Integration tests
   - Legacy compatibility tests
   - Full test suite
4. Run code quality checks:
   - Pylint (errors/fatal only)
   - Mypy (strict mode)
5. Manual functional testing:
   - Verify help text
   - Test command accessibility
   - Optional: Full workflow test in safe environment
6. Confirm all success criteria met
```

---

## DATA - Final State Summary

### Files Created (5)
1. ✅ `src/mcp_coder/workflows/create_pr/__init__.py`
2. ✅ `src/mcp_coder/workflows/create_pr/core.py`
3. ✅ `src/mcp_coder/cli/commands/create_pr.py`
4. ✅ `tests/cli/commands/test_create_pr.py`

### Files Modified (9)
1. ✅ `src/mcp_coder/cli/main.py` (added create-pr command)
2. ✅ `tests/workflows/create_pr/test_file_operations.py` (updated imports)
3. ✅ `tests/workflows/create_pr/test_parsing.py` (updated imports)
4. ✅ `tests/workflows/create_pr/test_prerequisites.py` (updated imports)
5. ✅ `tests/workflows/create_pr/test_generation.py` (updated imports)
6. ✅ `tests/workflows/create_pr/test_repository.py` (updated imports)
7. ✅ `tests/workflows/create_pr/test_main.py` (updated imports)
8. ✅ `tests/workflows/test_create_pr_integration.py` (updated imports)

### Files Deleted (3)
1. ✅ `workflows/create_PR.py`
2. ✅ `workflows/create_PR.bat`
3. ✅ `tests/test_create_pr.py`

### Net Change
- **Created:** 5 files
- **Modified:** 10 files
- **Deleted:** 2 files
- **Total changed:** 17 files

---

## LLM Prompt for This Step

```
I'm implementing Step 5 (FINAL STEP) of the create_PR to CLI command conversion (Issue #139).

Context: Read pr_info/steps/summary.md for full architectural context.

Task: Remove legacy files and run comprehensive validation.

Step 5 Details: Read pr_info/steps/step_5.md

Instructions:
1. Delete legacy files:
   - rm workflows/create_PR.py
   - rm workflows/create_PR.bat

2. Run comprehensive test suite:
   - pytest tests/workflows/create_pr/ -v
   - pytest tests/cli/commands/test_create_pr.py -v
   - pytest tests/ -k "create_pr" -v
   - pytest tests/ -v (full suite)

3. Run code quality checks using MCP tools:
   - mcp__code-checker__run_pytest_check (with create_pr filter)
   - mcp__code-checker__run_pylint_check
   - mcp__code-checker__run_mypy_check

4. Manual testing:
   - mcp-coder --help (verify create-pr appears)
   - mcp-coder create-pr --help (verify options shown)

5. Verify all success criteria from summary.md are met

This is the final cleanup step - ensure everything works before marking complete!
```

---

## Success Criteria (From Issue #139)

### Must All Be True ✅

- [ ] **Command available:** `mcp-coder create-pr --help` works
- [ ] **Accepts arguments:** `--project-dir PATH` and `--llm-method METHOD` work
- [ ] **All existing tests pass** with updated imports
- [ ] **New CLI command tests pass**
- [ ] **No code duplication:** `resolve_project_dir` reused from shared utilities
- [ ] **All code quality checks pass:** pylint, pytest, mypy
- [ ] **Legacy files removed:** `workflows/create_PR.py` and `workflows/create_PR.bat` deleted
- [ ] **Consistent with implement command pattern:** Same structure and approach

### Additional Quality Checks

- [ ] No import errors when running command
- [ ] Help text is clear and complete
- [ ] Error handling works (invalid paths, etc.)
- [ ] Logging works properly
- [ ] Integration with existing CLI is seamless

---

## Verification Checklist

### Files
- [ ] `workflows/create_PR.py` deleted
- [ ] `workflows/create_PR.bat` deleted
- [ ] No references to old files remain in codebase

### Tests
- [ ] All workflow tests pass
- [ ] All CLI command tests pass
- [ ] All integration tests pass
- [ ] Full test suite passes
- [ ] Pytest with `-n auto` passes

### Code Quality
- [ ] Pylint passes (no errors/fatal issues)
- [ ] Mypy passes (strict mode)
- [ ] No type errors
- [ ] No linting errors

### Functionality
- [ ] `mcp-coder --help` shows create-pr
- [ ] `mcp-coder create-pr --help` works
- [ ] Command can be invoked without errors
- [ ] Error messages are clear

### Documentation
- [ ] Help text is accurate
- [ ] Options are documented
- [ ] Examples are clear (if any)

---

## Dependencies

### Required Before This Step
- ✅ Step 1 completed (CLI command created)
- ✅ Step 2 completed (Workflow package created)
- ✅ Step 3 completed (CLI integration done)
- ✅ Step 4 completed (All tests updated)

### Blocks
- Nothing - this is the final step!

---

## Post-Completion Verification

After completing this step, verify the implementation meets all goals:

### Before (Problems)
- ❌ Code duplication (`resolve_project_dir`)
- ❌ Inconsistent interface (batch script)
- ❌ Not accessible via standard CLI
- ❌ Platform-specific wrapper needed

### After (Solutions)
- ✅ No code duplication (shared utilities)
- ✅ Consistent CLI interface (`mcp-coder create-pr`)
- ✅ Standard pip-installed entry point
- ✅ Cross-platform (no wrapper needed)
- ✅ Follows established patterns
- ✅ All tests pass
- ✅ All code quality checks pass

---

## Notes

- **This is the cleanup step** - legacy files removed, everything validated
- **All previous steps must be complete** before running this
- **Comprehensive testing is critical** - this is the final verification
- **Manual testing recommended** - verify CLI works end-to-end
- **Safe to commit after this step** - all changes are complete and validated
- If any test fails, go back to relevant step and fix before proceeding

## Completion Criteria

**This step is complete when:**
1. Legacy files are deleted
2. ALL tests pass
3. ALL code quality checks pass
4. Manual verification confirms CLI works
5. All success criteria from issue #139 are met

**Ready to commit and create PR!** 🎉

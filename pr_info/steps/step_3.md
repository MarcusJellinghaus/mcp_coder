# Step 3: Verify Change and Run Full Test Suite

## LLM Prompt
```
Reference pr_info/steps/summary.md for context.

Implement Step 3: Verify that the template change is correct and all tests pass.
Run the full test suite to ensure no regressions were introduced.
```

## Objective
Confirm the implementation is correct, tests pass, and no regressions were introduced.

## WHERE

### Files to Verify
1. `src/mcp_coder/workflows/vscodeclaude/templates.py` - Updated template
2. `tests/workflows/vscodeclaude/test_templates.py` - New test
3. Full test suite - Ensure no regressions

## WHAT

### Verification Tasks

#### 1. Template Verification
Confirm `VENV_SECTION_WINDOWS` contains:
- ✅ `uv sync --extra dev`
- ❌ No occurrence of `uv sync --extra types`

#### 2. Test Execution
Run the new test to ensure it passes:
```python
mcp__code-checker__run_pytest_check(
    extra_args=["-n", "auto", "tests/workflows/vscodeclaude/test_templates.py::test_venv_section_installs_dev_dependencies"],
    show_details=True
)
```

#### 3. Regression Testing
Run all vscodeclaude tests:
```python
mcp__code-checker__run_pytest_check(
    extra_args=["-n", "auto", "tests/workflows/vscodeclaude/"],
    show_details=False
)
```

#### 4. Full Test Suite
Run complete test suite (excluding slow integration tests):
```python
mcp__code-checker__run_pytest_check(
    extra_args=["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration"],
    show_details=False
)
```

## HOW

### Integration Points
No new integration points - this is pure verification.

### Tools Used
- `mcp__filesystem__read_file` to verify file contents
- `mcp__code-checker__run_pytest_check` to run tests
- Manual inspection of test results

## ALGORITHM

```
1. Read templates.py and confirm "uv sync --extra dev" is present
2. Read templates.py and confirm "uv sync --extra types" is absent
3. Run new test: test_venv_section_installs_dev_dependencies
4. Run all vscodeclaude tests for regression check
5. Run full unit test suite (fast tests only)
6. Review results and confirm all pass
```

## DATA

### Input
- Updated `templates.py` file
- New `test_templates.py` file
- Existing test suite

### Expected Output

#### Template Content
```python
VENV_SECTION_WINDOWS = r"""...
    echo Installing dependencies...
    uv sync --extra dev
    if errorlevel 1 (
...
"""
```

#### Test Results
```
tests/workflows/vscodeclaude/test_templates.py::test_venv_section_installs_dev_dependencies PASSED
```

#### Full Test Suite
```
======================== N passed in X.XXs =========================
```

## Implementation Details

### Step-by-Step Verification

#### 1. Read and Verify Template
```python
# Read the updated file
file_content = mcp__filesystem__read_file(file_path="src/mcp_coder/workflows/vscodeclaude/templates.py")

# Verify changes:
# - Should contain "uv sync --extra dev"
# - Should NOT contain "uv sync --extra types"
```

#### 2. Run New Test
```python
# Run the specific test created in Step 1
mcp__code-checker__run_pytest_check(
    extra_args=["-n", "auto", "tests/workflows/vscodeclaude/test_templates.py::test_venv_section_installs_dev_dependencies"],
    show_details=True
)
```

#### 3. Run VSCodeClaude Tests
```python
# Run all vscodeclaude tests to check for regressions
mcp__code-checker__run_pytest_check(
    extra_args=["-n", "auto", "tests/workflows/vscodeclaude/"],
    show_details=False
)
```

#### 4. Run Fast Test Suite
```python
# Run all unit tests (exclude slow integration tests)
mcp__code-checker__run_pytest_check(
    extra_args=["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration"],
    show_details=False
)
```

## Verification Checklist

### Code Changes
- [ ] `templates.py` contains `uv sync --extra dev`
- [ ] `templates.py` does NOT contain `uv sync --extra types`
- [ ] Only one line changed in templates.py
- [ ] Test file created with proper imports

### Test Results
- [ ] New test `test_venv_section_installs_dev_dependencies` PASSES
- [ ] All vscodeclaude tests PASS (no regressions)
- [ ] Full unit test suite PASSES

### Code Quality
- [ ] No syntax errors
- [ ] No import errors
- [ ] Test follows project conventions
- [ ] Change is minimal and focused

## Success Criteria

### Must Pass
1. ✅ New test passes
2. ✅ No existing tests broken
3. ✅ Template correctly updated
4. ✅ Only intended changes made

### Expected Behavior
After this verification, the fix is complete:
- New vscodeclaude workspaces will install all dev dependencies
- Test dependencies (pytest-asyncio, pytest-xdist) will be available
- Issue #411 is resolved

## Notes

### Manual Testing (Optional)
If desired, create a test workspace to verify actual behavior:
```bash
# This would require actual GitHub integration
mcp-coder coordinator vscodeclaude --repo <test-repo>

# Then in the created workspace:
cd <workspace-folder>
.venv\Scripts\activate.bat
python -c "import pytest_asyncio; import pytest_xdist; print('✓ Test dependencies installed')"
```

### Rollback Plan
If issues are discovered:
1. Revert the one-line change in templates.py
2. Remove the new test file
3. File a new issue with details

## Additional Task: Update Documentation

Add a concise note to `docs/coordinator-vscodeclaude.md` about dev dependencies.

**Location**: In the "Session Lifecycle" section after the workspace setup step.

**Content to add**:
```markdown
   - **Dependency Installation**: Installs complete development environment with `uv sync --extra dev` (includes test utilities, type stubs, and development tools)
```

This provides transparency about what gets installed without excessive detail.

## Final Deliverables
- ✅ Updated template with `--extra dev`
- ✅ Test verifying the change
- ✅ All tests passing
- ✅ No regressions introduced
- ✅ Documentation updated
- ✅ Issue #411 resolved

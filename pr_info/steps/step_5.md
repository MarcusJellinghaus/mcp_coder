# Step 5: Final Validation and Documentation

## Context
Feature implementation is complete (Steps 1-4). This final step validates everything works end-to-end, runs comprehensive code quality checks, and ensures documentation is complete.

**Reference**: See `pr_info/steps/summary.md` for architectural overview.

## Objective
Perform comprehensive validation, run all code quality checks, verify test coverage, and ensure the feature is production-ready.

## WHAT: Validation Tasks

### 1. Run All Unit Tests
```bash
# Run all label update tests
mcp__code-checker__run_pytest_check(
    extra_args=["-n", "auto", "-v", "tests/utils/github_operations/test_issue_manager_label_update.py"]
)

# Run all IssueManager tests (regression check)
mcp__code-checker__run_pytest_check(
    extra_args=["-n", "auto", "-v", "tests/utils/github_operations/test_issue_manager.py"]
)

# Run fast unit tests (full suite, excluding integration)
mcp__code-checker__run_pytest_check(
    extra_args=["-n", "auto", "-m", "not git_integration and not claude_integration and not formatter_integration and not github_integration"]
)
```

### 2. Type Checking
```bash
# Full mypy check in strict mode
mcp__code-checker__run_mypy_check(
    strict=True,
    target_directories=["src", "tests"]
)
```

### 3. Code Quality
```bash
# Pylint check (errors and fatal only)
mcp__code-checker__run_pylint_check(
    categories=["error", "fatal"],
    target_directories=["src", "tests"]
)
```

### 4. Manual CLI Testing

**Test 1: Help Text Verification**
```bash
# Verify flag appears in help
mcp-coder implement --help | grep -A 2 "update-labels"
mcp-coder create-plan --help | grep -A 2 "update-labels"
mcp-coder create-pr --help | grep -A 2 "update-labels"

# Expected output for each:
# --update-labels    Automatically update GitHub issue labels on successful completion
```

**Test 2: Flag Parsing (Dry Run)**
```bash
# Test that flag is accepted (will fail on other requirements, but flag parsing works)
mcp-coder implement --update-labels 2>&1 | head -5
mcp-coder create-plan 123 --update-labels 2>&1 | head -5
mcp-coder create-pr --update-labels 2>&1 | head -5

# Should NOT show "unrecognized arguments: --update-labels"
```

**Test 3: Integration Test (if test environment available)**
```bash
# On a real feature branch linked to an issue:
cd /path/to/test/branch
git status  # Should be clean

# Test implement workflow
mcp-coder implement --update-labels

# Verify:
# 1. Workflow completes successfully (exit code 0)
# 2. Log shows "Updating GitHub issue label..."
# 3. GitHub issue label updated (check web UI)

# Test without flag (should skip label update)
mcp-coder implement

# Verify:
# 1. Workflow completes successfully
# 2. No "Updating GitHub issue label..." in logs
```

## Validation Checklist

### Code Quality
- [ ] All unit tests pass (100% pass rate)
- [ ] No mypy errors (strict mode)
- [ ] No pylint errors or fatal issues
- [ ] No regression in existing tests
- [ ] Test coverage adequate (happy path + errors)

### Functionality
- [ ] `--update-labels` flag accepted by all three commands
- [ ] Help text displays correctly for all commands
- [ ] Flag defaults to False (backward compatible)
- [ ] Label update skipped when flag not passed
- [ ] Label update attempted when flag passed
- [ ] Non-blocking: workflow succeeds even if label update fails
- [ ] Appropriate logging at all levels
- [ ] Idempotent: safe to run multiple times

### Integration
- [ ] IssueManager.update_workflow_label() method exists
- [ ] Method uses correct decorators and error handling
- [ ] Branch name extraction works correctly
- [ ] Label lookup from config works correctly
- [ ] Branch-issue verification via get_linked_branches() works
- [ ] Label transition via set_labels() works
- [ ] All three workflows integrate correctly

### Documentation
- [ ] summary.md describes architecture and changes
- [ ] All step files include clear LLM prompts
- [ ] Code includes proper docstrings
- [ ] Type hints are complete and correct
- [ ] Comments explain non-obvious logic

### Edge Cases
- [ ] Invalid branch names handled (WARNING, continue)
- [ ] Branch not linked to issue handled (WARNING, continue)
- [ ] Label not in config handled (ERROR, continue)
- [ ] GitHub API errors handled (ERROR, continue)
- [ ] Already in target state handled (DEBUG, continue)
- [ ] Missing source label handled gracefully
- [ ] Multiple status labels handled (WARNING, remove old + add new)

## Expected Test Results

### Unit Tests
```
tests/utils/github_operations/test_issue_manager_label_update.py
  ✓ test_update_workflow_label_success_happy_path
  ✓ test_update_workflow_label_invalid_branch_name
  ✓ test_update_workflow_label_branch_not_linked
  ✓ test_update_workflow_label_already_correct_state
  ✓ test_update_workflow_label_missing_source_label
  ✓ test_update_workflow_label_label_not_in_config
  ✓ test_update_workflow_label_github_api_error
  ✓ test_update_workflow_label_no_branch_provided

8 passed in X.XXs
```

### Mypy
```
Success: no issues found in N source files
```

### Pylint
```
--------------------------------------------------------------------
Your code has been rated at 10.00/10 (previous run: 10.00/10, +0.00)
```

## Files Modified Summary

### Created (1 file)
```
tests/utils/github_operations/test_issue_manager_label_update.py
  └─ 8 test functions, ~250 lines
```

### Modified (8 files)
```
src/mcp_coder/utils/github_operations/issue_manager.py
  └─ Added update_workflow_label() method (~80 lines)

src/mcp_coder/cli/main.py
  └─ Added --update-labels to 3 parsers (9 lines)

src/mcp_coder/cli/commands/implement.py
  └─ Pass update_labels flag (2 lines)

src/mcp_coder/cli/commands/create_plan.py
  └─ Pass update_labels flag (2 lines)

src/mcp_coder/cli/commands/create_pr.py
  └─ Pass update_labels flag (2 lines)

src/mcp_coder/workflows/implement/core.py
  └─ Call update_workflow_label() at end (20 lines)

src/mcp_coder/workflows/create_plan.py
  └─ Call update_workflow_label() at end (20 lines)

src/mcp_coder/workflows/create_pr/core.py
  └─ Call update_workflow_label() at end (20 lines)
```

**Total Changes**: ~400 lines (including tests and docstrings)

## Known Limitations

### By Design
1. **Opt-in only**: Requires explicit `--update-labels` flag
2. **Single label transition**: Only handles one transition per workflow run
3. **Branch naming convention**: Requires `{number}-{title}` format
4. **Branch must be linked**: GitHub branch-issue link must exist
5. **Non-blocking errors**: Label update failures don't fail workflow

### Not Implemented (Future Enhancements)
1. Custom label mappings (uses hardcoded internal IDs)
2. Multiple label transitions per run
3. Automatic label detection without flag
4. Label transition history tracking
5. Webhook-based updates

## Troubleshooting Guide

### Issue: "Branch name doesn't match pattern"
**Cause**: Branch name doesn't follow `{number}-{title}` format
**Solution**: Rename branch or manually update labels
**Example**: `feature-123` → should be `123-feature`

### Issue: "Branch not linked to issue"
**Cause**: GitHub doesn't show branch in issue's Development section
**Solution**: Use `IssueBranchManager.create_remote_branch_for_issue()` or manually link
**Example**: Check issue page on GitHub for linked branches

### Issue: "Label ID not found in configuration"
**Cause**: Internal ID doesn't exist in `src/mcp_coder/config/labels.json`
**Solution**: Check labels.json for correct internal_id values
**Example**: `"implementing"` must exist in workflow_labels array

### Issue: "GitHub API error"
**Cause**: Authentication failure, rate limit, or network issue
**Solution**: Check GitHub token in `~/.mcp_coder/config.toml`
**Example**: Token needs `repo` scope for private repos

## Commit Message Template

```
feat: add auto-update issue labels after workflow completion (#143)

Adds opt-in --update-labels flag to implement, create-plan, and create-pr 
workflows that automatically transitions GitHub issue labels on success.

Changes:
- Add IssueManager.update_workflow_label() method
- Add --update-labels CLI flag to three commands
- Integrate label updates into workflow success paths
- Add comprehensive unit tests with mocks

Label transitions:
- implement: implementing → code-review
- create-plan: planning → plan-review  
- create-pr: pr-creating → pr-created

Non-blocking design: label update failures never fail workflows.
Idempotent: safe to run multiple times.

Resolves #143
```

## Success Criteria Met

Verify all criteria from issue #143:

- [x] `--update-labels` flag added to all three workflow commands
- [x] `update_workflow_label()` method added to `IssueManager`
- [x] Method uses `@_handle_github_errors` decorator pattern
- [x] Method uses `set_labels()` for single API call
- [x] Label automatically updates when flag used + workflow succeeds
- [x] Uses `get_linked_branches()` to verify branch-issue relationship
- [x] Handles multiple status labels gracefully
- [x] Non-blocking: workflow succeeds even if label update fails
- [x] Idempotent: skips silently if already in correct state
- [x] Appropriate logging at INFO/DEBUG/WARNING/ERROR levels
- [x] Basic unit tests with mocks (happy path + error cases)
- [x] CLI help text updated via argparse
- [x] All code quality checks pass

---

## LLM Prompt for This Step

```
You are implementing Step 5 (final validation) of the auto-label update feature.

CONTEXT:
Read pr_info/steps/summary.md for architectural overview.
Implementation is complete (Steps 1-4), now validate everything works.

TASK:
Perform comprehensive validation and ensure production readiness.

VALIDATION STEPS:
1. Run all unit tests (label_update + regression)
2. Run mypy type checking (strict mode)
3. Run pylint (errors/fatal categories only)
4. Verify CLI help text displays correctly
5. Test flag parsing works (dry run)
6. Review all code changes for quality

QUALITY CHECKS:
mcp__code-checker__run_pytest_check(
    extra_args=["-n", "auto", "-v", "tests/utils/github_operations/test_issue_manager_label_update.py"]
)

mcp__code-checker__run_mypy_check(strict=True)

mcp__code-checker__run_pylint_check(categories=["error", "fatal"])

MANUAL TESTING:
# Verify help text
mcp-coder implement --help | grep "update-labels"
mcp-coder create-plan --help | grep "update-labels"
mcp-coder create-pr --help | grep "update-labels"

SUCCESS CRITERIA:
- All tests pass (100%)
- No mypy errors
- No pylint errors/fatal issues
- Help text displays correctly
- Flag parsing works
- All issue #143 requirements met

REFERENCE THIS STEP:
pr_info/steps/step_5.md (contains validation checklist and success criteria)

If all checks pass, the feature is production-ready!
```

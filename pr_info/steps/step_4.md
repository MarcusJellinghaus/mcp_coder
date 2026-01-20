# Step 4: Integrate CI Check into Workflow

## Overview

Integrate the `check_and_fix_ci()` function into the main `run_implement_workflow()` function, calling it after finalisation.

**Note:** Integration tests are simplified to only verify `check_and_fix_ci()` is called with correct parameters (see Decision 6 in Decisions.md).

## LLM Prompt for This Step

```
Implement Step 4 from pr_info/steps/step_4.md.

Reference the summary at pr_info/steps/summary.md for context.

This step integrates the CI check function into the main workflow.
Add the integration call and update tests to verify the integration.
```

---

## Part 1: Integrate into Workflow

**Note:** Integration tests removed per Decision 12. The `check_and_fix_ci()` function has comprehensive unit tests. Workflow wiring is verified manually.

### WHERE
`src/mcp_coder/workflows/implement/core.py`

### WHAT
Add CI check call in `run_implement_workflow()` after finalisation (Step 5.5), before progress summary (Step 6).

### HOW

1. Add CI check as Step 5.6 (after Step 5.5, before Step 6 - no renumbering needed):

```python
    # Step 5.6: Check CI pipeline and auto-fix if needed
    if not error_occurred:
        logger.info("Checking CI pipeline status...")
        current_branch = get_current_branch_name(project_dir)
        ci_success = check_and_fix_ci(
            project_dir=project_dir,
            branch=current_branch,
            provider=provider,
            method=method,
            mcp_config=mcp_config,
            execution_dir=execution_dir,
        )
        if not ci_success:
            logger.error("CI check failed after maximum fix attempts")
            return 1
```

Note: Branch check removed per Decision 20 - trust branch is available after successful finalisation.

No renumbering of existing steps required.

### ALGORITHM
```
1. Check if error_occurred is False
2. Get current branch name
3. Call check_and_fix_ci()
4. If returns False → log error, return 1
5. Continue to progress summary
```

### DATA

No new data structures. Uses existing:
- `get_current_branch_name()` → str
- `check_and_fix_ci()` → bool

---

## Verification

1. Run all CI check tests: `pytest tests/workflows/implement/test_ci_check.py -v`
2. Run existing workflow tests: `pytest tests/workflows/implement/test_core.py -v`
3. All tests should pass
4. Manually verify workflow wiring works end-to-end

---

## Final Checklist

After completing all steps:

- [ ] Constants added to `constants.py`
- [ ] Prompts added to `prompts.md`
- [ ] `.gitignore` updated
- [ ] Helper functions implemented with tests
- [ ] Main `check_and_fix_ci()` function implemented with tests
- [ ] Workflow integration complete with tests
- [ ] All tests pass: `pytest tests/workflows/implement/ -v`
- [ ] Code quality checks pass: pylint, mypy

# Step 6: Code Quality Improvements

## Overview

Apply code quality improvements identified during implementation review discussion. This step addresses 4 items from the review:

1. Refactor `_run_ci_analysis_and_fix` return type (Decision 29)
2. Fix defensive SHA handling (Decision 30)
3. Create `_short_sha()` helper function (Decision 31)
4. Standardize type annotations to Python 3.9+ style (Decision 32)

## LLM Prompt for This Step

```
Implement Step 6 from pr_info/steps/step_6.md.

Reference the summary at pr_info/steps/summary.md for context.

This step applies code quality improvements:
1. Refactor _run_ci_analysis_and_fix return type from tuple[bool, bool, str] to tuple[bool, Optional[bool]]
2. Fix defensive SHA handling with `or "unknown"` pattern
3. Create _short_sha() helper function
4. Standardize type annotations to Python 3.9+ style (lowercase list, dict)

Follow TDD where applicable.
```

---

## Part 1: Refactor `_run_ci_analysis_and_fix` Return Type (Decision 29)

### WHERE
`src/mcp_coder/workflows/implement/core.py`

### WHAT
Change the return type from `tuple[bool, bool, str]` to `tuple[bool, Optional[bool]]`:

**BEFORE:**
```python
def _run_ci_analysis_and_fix(
    config: CIFixConfig,
    ci_status: CIStatusData,
    ci_manager: CIResultsManager,
    fix_attempt: int,
) -> tuple[bool, bool, str]:
    """Run CI failure analysis and attempt a fix.

    Returns:
        Tuple of (should_continue, should_return, return_value_if_returning)
        - should_continue: True if should continue to next fix attempt
        - should_return: True if function should return immediately
        - return_value_if_returning: "true"/"false" if returning, empty if continuing
    """
```

**AFTER:**
```python
def _run_ci_analysis_and_fix(
    config: CIFixConfig,
    ci_status: CIStatusData,
    ci_manager: CIResultsManager,
    fix_attempt: int,
) -> tuple[bool, Optional[bool]]:
    """Run CI failure analysis and attempt a fix.

    Returns:
        Tuple of (should_continue, return_value):
        - should_continue: True if should continue to next fix attempt
        - return_value: None to continue loop, True for success (exit 0), False for failure (exit 1)
    """
```

### ALGORITHM
```
1. Change return type signature
2. Update all return statements:
   - return True, False, ""  → return True, None (continue)
   - return False, True, "true"  → return False, True (success)
   - return False, True, "false"  → return False, False (failure)
   - return False, False, ""  → return False, None (pushed, wait for new run)
3. Update caller in check_and_fix_ci() to handle new return type
4. Update docstring
```

### HOW
Update the caller code:

**BEFORE:**
```python
should_continue, should_return, return_value = _run_ci_analysis_and_fix(...)
if should_return:
    return return_value == "true"
if should_continue:
    continue
```

**AFTER:**
```python
should_continue, return_value = _run_ci_analysis_and_fix(...)
if return_value is not None:
    return return_value
if should_continue:
    continue
```

---

## Part 2: Fix Defensive SHA Handling (Decision 30)

### WHERE
`src/mcp_coder/workflows/implement/core.py`

### WHAT
Fix all locations where SHA is retrieved to handle `None` values defensively.

**BEFORE:**
```python
run_sha = ci_status.get("run", {}).get("commit_sha", "unknown")
```

**AFTER:**
```python
run_sha = ci_status.get("run", {}).get("commit_sha") or "unknown"
```

### ALGORITHM
```
1. Search for all occurrences of .get("commit_sha", "unknown")
2. Replace with .get("commit_sha") or "unknown"
3. This handles both missing keys AND explicit None values
```

### LOCATIONS
- `_poll_for_ci_completion()` - line with `run_sha = run_info.get("commit_sha", "unknown")`
- `_wait_for_new_ci_run()` - line with `new_sha = new_status.get("run", {}).get("commit_sha", "unknown")`
- `check_and_fix_ci()` - line with `run_sha = ci_status.get("run", {}).get("commit_sha", "unknown")`
- `check_and_fix_ci()` - line with `final_sha = ci_status.get("run", {}).get("commit_sha", "unknown")`

---

## Part 3: Create `_short_sha()` Helper Function (Decision 31)

### WHERE
`src/mcp_coder/workflows/implement/core.py`

### WHAT
Create a helper function to consolidate duplicate SHA truncation pattern:

```python
def _short_sha(sha: str) -> str:
    """Return first 7 characters of SHA for display.

    Args:
        sha: Full SHA string or "unknown"

    Returns:
        First 7 characters of SHA, or "unknown" if input is empty/unknown
    """
    if not sha or sha == "unknown":
        return "unknown"
    return sha[:7]
```

### HOW
1. Add the helper function near the top of the file (after `CIFixConfig` dataclass)
2. Replace all `sha[:7]` occurrences with `_short_sha(sha)`

### LOCATIONS TO UPDATE
- `_poll_for_ci_completion()`: `logger.debug(f"CI run {run_id} completed (sha: {run_sha[:7]})")`
- `_poll_for_ci_completion()`: `logger.info(f"CI_PASSED: Pipeline succeeded (sha: {run_sha[:7]})")`
- `_poll_for_ci_completion()`: `logger.info(f"CI run completed with conclusion: {run_conclusion} (sha: {run_sha[:7]})")`
- `_wait_for_new_ci_run()`: `logger.info(f"New CI run detected: {new_run_id} (sha: {new_sha[:7]})")`
- `check_and_fix_ci()`: `logger.debug(f"Latest local commit SHA: {local_sha[:7]}")`
- `check_and_fix_ci()`: `logger.info(f"CI fix attempt {fix_attempt + 1}/{CI_MAX_FIX_ATTEMPTS} (sha: {run_sha[:7]})")`
- `check_and_fix_ci()`: `logger.error(f"CI still failing after {CI_MAX_FIX_ATTEMPTS} fix attempts (sha: {final_sha[:7]})")`

---

## Part 4: Standardize Type Annotations (Decision 32)

### WHERE
`src/mcp_coder/workflows/implement/core.py`

### WHAT
Standardize all type annotations to Python 3.9+ style (lowercase `list`, `dict`, `tuple`).

### CHANGES
1. Remove unused imports from `typing` module (keep only `Any`, `Optional`)
2. Change all `List[X]` to `list[X]`
3. Change all `Dict[X, Y]` to `dict[X, Y]`
4. Change all `Tuple[X, Y]` to `tuple[X, Y]`

### LOCATIONS
Check and update:
- Import statements
- Function signatures
- Variable annotations
- Docstrings (if they reference types)

---

## Verification

1. Run tests: `pytest tests/workflows/implement/test_ci_check.py -v`
2. Run pylint: verify no new issues
3. Run mypy: verify type annotations are correct
4. All tests should pass

---

## Quality Checklist

- [ ] Refactor `_run_ci_analysis_and_fix` return type to `tuple[bool, Optional[bool]]`
- [ ] Update caller code in `check_and_fix_ci()` to handle new return type
- [ ] Update docstring for `_run_ci_analysis_and_fix`
- [ ] Fix defensive SHA handling with `or "unknown"` pattern (4 locations)
- [ ] Create `_short_sha()` helper function
- [ ] Replace all `sha[:7]` with `_short_sha(sha)` (7 locations)
- [ ] Standardize type annotations to Python 3.9+ style
- [ ] Run pylint and fix any issues
- [ ] Run pytest and fix any failing tests
- [ ] Run mypy and fix any type errors

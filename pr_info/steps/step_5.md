# Step 5: Code Review Fixes

## Overview

Apply fixes identified during code review. This step addresses 6 issues from the review discussion (Decisions 23-28).

## LLM Prompt for This Step

```
Implement Step 5 from pr_info/steps/step_5.md.

Reference the summary at pr_info/steps/summary.md for context.

This step applies code review fixes:
1. Fix commit_sha field lookup bug
2. Change branch check log level to ERROR
3. Refactor _run_ci_analysis_and_fix into smaller functions with config dataclass
4. Update type annotations to use List[JobData]
5. Add short SHA to CI log messages
6. Handle empty temp file with fallback + add test

Follow TDD where applicable.
```

---

## Part 1: Fix commit_sha Field Lookup (Decision 24)

### WHERE
`src/mcp_coder/workflows/implement/core.py`

### WHAT
Fix the field name in `_poll_for_ci_completion`:

```python
# BEFORE (bug):
run_sha = run_info.get("head_sha", "unknown")

# AFTER (fix):
run_sha = run_info.get("commit_sha", "unknown")
```

### HOW
Simple string replacement in the function.

---

## Part 2: Change Branch Check Log Level (Decision 23)

### WHERE
`src/mcp_coder/workflows/implement/core.py`

### WHAT
In `run_implement_workflow()`, change WARNING to ERROR:

```python
# BEFORE:
logger.warning("Could not determine current branch - skipping CI check")

# AFTER:
logger.error("Could not determine current branch - skipping CI check")
```

### HOW
Simple log level change.

---

## Part 3: Refactor _run_ci_analysis_and_fix (Decision 25)

### WHERE
`src/mcp_coder/workflows/implement/core.py`

### WHAT
1. Create a config dataclass to hold common parameters
2. Extract `_run_ci_analysis()` helper
3. Extract `_run_ci_fix()` helper
4. Simplify `_run_ci_analysis_and_fix()` to use these helpers
5. Remove pylint disables

### DATA
New dataclass:
```python
@dataclass
class CIFixConfig:
    """Configuration for CI fix operations."""
    project_dir: Path
    provider: str
    method: str
    env_vars: dict[str, str]
    cwd: str
    mcp_config: Optional[str]
```

### ALGORITHM for _run_ci_analysis
```
1. Load analysis prompt with substitutions
2. Call LLM with analysis prompt
3. Handle empty response (retry once)
4. Read problem description from temp file or response
5. Save conversation for debugging
6. Return problem_description or None on failure
```

### ALGORITHM for _run_ci_fix
```
1. Load fix prompt with problem_description
2. Call LLM with fix prompt
3. Handle empty response
4. Save conversation for debugging
5. Run formatters
6. Commit and push changes
7. Return success bool
```

### WHAT (function signatures)
```python
def _run_ci_analysis(
    config: CIFixConfig,
    failed_summary: dict[str, Any],
    fix_attempt: int,
) -> Optional[str]:
    """Run CI failure analysis and return problem description."""
    ...

def _run_ci_fix(
    config: CIFixConfig,
    problem_description: str,
    fix_attempt: int,
) -> bool:
    """Attempt to fix CI failure. Returns True if push succeeded."""
    ...
```

---

## Part 4: Update Type Annotation (Decision 26)

### WHERE
`src/mcp_coder/workflows/implement/core.py`

### WHAT
Update `_get_failed_jobs_summary` signature:

```python
# BEFORE:
def _get_failed_jobs_summary(
    jobs: list[dict[str, Any]] | list[Any], logs: dict[str, str]
) -> dict[str, Any]:

# AFTER:
from mcp_coder.utils.github_operations.ci_results_manager import JobData

def _get_failed_jobs_summary(
    jobs: List[JobData], logs: dict[str, str]
) -> dict[str, Any]:
```

### HOW
1. Add `JobData` to imports from `ci_results_manager`
2. Update function signature

---

## Part 5: Add Short SHA to CI Log Messages (Decision 27)

### WHERE
`src/mcp_coder/workflows/implement/core.py`

### WHAT
Update log messages in `_poll_for_ci_completion`:

```python
# CI passed message:
logger.info(f"CI_PASSED: Pipeline succeeded (sha: {run_sha[:7]})")

# CI failed message:
logger.info(f"CI run completed with conclusion: {run_conclusion} (sha: {run_sha[:7]})")
```

Also update other CI status messages to include SHA where available.

---

## Part 6: Handle Empty Temp File (Decision 28)

### WHERE
`src/mcp_coder/workflows/implement/core.py`

### WHAT
Update `_read_problem_description`:

```python
def _read_problem_description(temp_file: Path, fallback_response: str) -> str:
    """Read problem description from temp file or use fallback.

    Args:
        temp_file: Path to the temp problem description file
        fallback_response: Fallback text if file doesn't exist or is empty

    Returns:
        Problem description text
    """
    if temp_file.exists():
        try:
            content = temp_file.read_text(encoding="utf-8").strip()
            temp_file.unlink()  # Delete after reading
            if content:  # Only use file content if not empty
                logger.debug(f"Problem description:\n{content}")
                return content
            logger.debug("Temp file was empty, using fallback")
        except Exception as e:
            logger.warning(f"Failed to read problem description file: {e}")

    logger.debug("Using analysis response as problem description")
    return fallback_response
```

### TESTS
Add to `tests/workflows/implement/test_ci_check.py`:

```python
class TestReadProblemDescription:
    """Tests for _read_problem_description function."""

    def test_empty_file_uses_fallback(self, tmp_path: Path) -> None:
        """Empty temp file should return fallback response."""
        from mcp_coder.workflows.implement.core import _read_problem_description

        temp_file = tmp_path / ".ci_problem_description.md"
        temp_file.write_text("")  # Empty file

        result = _read_problem_description(temp_file, "fallback content")

        assert result == "fallback content"
        assert not temp_file.exists()  # File should be deleted

    def test_whitespace_only_file_uses_fallback(self, tmp_path: Path) -> None:
        """File with only whitespace should return fallback response."""
        from mcp_coder.workflows.implement.core import _read_problem_description

        temp_file = tmp_path / ".ci_problem_description.md"
        temp_file.write_text("   \n\t\n  ")  # Whitespace only

        result = _read_problem_description(temp_file, "fallback content")

        assert result == "fallback content"
        assert not temp_file.exists()

    def test_file_with_content_returns_content(self, tmp_path: Path) -> None:
        """File with content should return that content."""
        from mcp_coder.workflows.implement.core import _read_problem_description

        temp_file = tmp_path / ".ci_problem_description.md"
        temp_file.write_text("Problem: test failed")

        result = _read_problem_description(temp_file, "fallback content")

        assert result == "Problem: test failed"
        assert not temp_file.exists()

    def test_missing_file_uses_fallback(self, tmp_path: Path) -> None:
        """Missing temp file should return fallback response."""
        from mcp_coder.workflows.implement.core import _read_problem_description

        temp_file = tmp_path / ".ci_problem_description.md"
        # Don't create the file

        result = _read_problem_description(temp_file, "fallback content")

        assert result == "fallback content"
```

---

## Verification

1. Run tests: `pytest tests/workflows/implement/test_ci_check.py -v`
2. Run pylint: verify no disables needed for refactored functions
3. Run mypy: verify type annotations are correct
4. All tests should pass

---

## Quality Checklist

- [ ] Fix commit_sha field lookup
- [ ] Change branch check log level to ERROR
- [ ] Create CIFixConfig dataclass
- [ ] Extract _run_ci_analysis() helper
- [ ] Extract _run_ci_fix() helper
- [ ] Simplify _run_ci_analysis_and_fix() 
- [ ] Remove pylint disables
- [ ] Update _get_failed_jobs_summary type annotation
- [ ] Add short SHA to CI log messages
- [ ] Update _read_problem_description for empty file handling
- [ ] Add tests for _read_problem_description edge cases
- [ ] Run pylint and fix any issues
- [ ] Run pytest and fix any failing tests
- [ ] Run mypy and fix any type errors

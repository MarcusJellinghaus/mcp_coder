# Step 1: Pure functions + updated types (TDD)

> **Ref:** See `pr_info/steps/summary.md` for full context.

## WHERE
- **Test:** `tests/utils/github_operations/test_ci_results_manager_status.py`
- **Source:** `src/mcp_coder/utils/github_operations/ci_results_manager.py`

## WHAT — Tests first

Add two new test classes at the end of the test file:

### `TestFilterRunsByHeadSha`
```python
def test_empty_input_returns_empty_list() -> None
def test_all_runs_same_sha_returns_all() -> None
def test_mixed_shas_returns_only_latest() -> None
def test_caps_at_max_runs() -> None
```

### `TestAggregateConclusion`
```python
def test_empty_input_returns_not_configured() -> None
def test_all_success_returns_success() -> None
def test_one_failure_among_successes_returns_failure() -> None
def test_no_failures_one_in_progress_returns_pending() -> None
def test_cancelled_treated_as_failure() -> None
```

Each test calls the pure function directly with plain dicts (no mocks needed).

## WHAT — Source changes

### 1. Update `JobData` TypedDict
Add one field:
```python
class JobData(TypedDict):
    id: int
    run_id: int  # NEW — links job back to its workflow run
    name: str
    # ... rest unchanged
```

### 2. Add `filter_runs_by_head_sha` (module-level function)
```python
def filter_runs_by_head_sha(
    runs: List[Any], max_runs: int = 25
) -> List[Any]:
```
**Algorithm:**
```
if not runs: return []
target_sha = runs[0].head_sha
filtered = [r for r in runs if r.head_sha == target_sha]
return filtered[:max_runs]
```

### 3. Add `aggregate_conclusion` (module-level function)
```python
def aggregate_conclusion(
    runs: List[Any],
) -> tuple[Optional[str], str]:
    """Returns (conclusion, status) tuple."""
```
**Algorithm:**
```
if not runs: return (None, "not_configured")
conclusions = [r.conclusion for r in runs]
statuses = [r.status for r in runs]
if any(c == "failure" or c == "cancelled" for c in conclusions):
    return ("failure", "completed")
if any(s in ("in_progress", "queued", "pending") for s in statuses):
    return (None, "in_progress")
if all(c == "success" for c in conclusions):
    return ("success", "completed")
return (None, "in_progress")  # defensive fallback
```

### 4. Update `__all__` exports
Add `filter_runs_by_head_sha` and `aggregate_conclusion`.

## HOW — Integration
- Both functions are pure (no API calls, no class methods)
- Imported directly from module in tests
- No decorator changes needed

## DATA — Return values
- `filter_runs_by_head_sha`: `List[Any]` (PyGithub WorkflowRun objects, or mock objects in tests)
- `aggregate_conclusion`: `tuple[Optional[str], str]` — `(conclusion, status)`

## LLM Prompt
```
Read pr_info/steps/summary.md for context, then implement Step 1 from pr_info/steps/step_1.md.

Write tests FIRST in tests/utils/github_operations/test_ci_results_manager_status.py,
then implement the source changes in src/mcp_coder/utils/github_operations/ci_results_manager.py.

Add `run_id: int` to `JobData`. Add `filter_runs_by_head_sha()` and `aggregate_conclusion()`
as module-level pure functions. Update `__all__`. Run tests to verify.
```

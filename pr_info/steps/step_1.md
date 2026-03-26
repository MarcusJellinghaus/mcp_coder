# Step 1: MLflowLogger infrastructure — step tracking and step-aware metrics

> **Context:** See `pr_info/steps/summary.md` for the full design.
> This step adds the foundational infrastructure that steps 2–3 build on.

## LLM Prompt

```
Implement step 1 of issue #593 (see pr_info/steps/summary.md and pr_info/steps/step_1.md).

Add step-tracking infrastructure to MLflowLogger: a _run_step_count dict,
a current_step() method, and a step parameter on log_metrics().
Write tests first (TDD), then implement, then run all three code quality checks.
```

## WHERE

- `tests/llm/test_mlflow_logger.py` — new test class `TestStepTracking`
- `src/mcp_coder/llm/mlflow_logger.py` — `MLflowLogger` class

## WHAT — Tests (write first)

Add class `TestStepTracking` with these tests:

```python
def test_current_step_returns_zero_when_no_active_run(self) -> None:
    """current_step() returns 0 when no run is active."""

def test_current_step_returns_zero_for_new_run(self) -> None:
    """current_step() returns 0 for a freshly started run."""

def test_current_step_increments_after_advance(self) -> None:
    """After _advance_step(), current_step() returns 1."""

def test_step_persists_across_end_and_resume(self) -> None:
    """Step count persists when a run is ended and resumed via session_id."""

def test_new_run_starts_at_step_zero(self) -> None:
    """A brand new run (different session) starts at step 0."""

def test_end_run_without_session_cleans_step_count(self) -> None:
    """Ending a run without session_id removes the step count entry."""
```

Update existing `TestMLflowLogger.test_log_metrics` to verify backward compatibility
(no `step` param → calls `mlflow.log_metrics` as before).

Add test:

```python
def test_log_metrics_with_step_uses_log_metric(self) -> None:
    """When step is provided, each metric is logged via mlflow.log_metric(key, value, step=step)."""
```

## WHAT — Implementation

### 1. `__init__` — add `_run_step_count`

```python
self._run_step_count: dict[str, int] = {}
```

### 2. `current_step()` method

```python
def current_step(self) -> int:
    """Return the current step index for the active run (0 if no run or first step)."""
    if not self.active_run_id:
        return 0
    return self._run_step_count.get(self.active_run_id, 0)
```

### 3. `_advance_step()` method

```python
def _advance_step(self) -> None:
    """Increment the step counter for the active run."""
    if self.active_run_id:
        self._run_step_count[self.active_run_id] = self.current_step() + 1
```

### 4. `log_metrics()` — add optional `step` parameter

**Signature:**
```python
def log_metrics(self, metrics: Dict[str, float], step: int | None = None) -> None:
```

**Algorithm (pseudocode):**
```
filter metrics to numeric values only
if step is None:
    mlflow.log_metrics(numeric_metrics)          # existing behavior
else:
    for key, value in numeric_metrics:
        mlflow.log_metric(key, value, step=step) # per-metric with step
```

### 5. `end_run()` — clean up step count when run won't be resumed

In the existing `end_run()` method, when `session_id is None` (run won't be resumed),
delete the entry from `_run_step_count` to prevent unbounded growth:

```python
if session_id is None and self.active_run_id in self._run_step_count:
    del self._run_step_count[self.active_run_id]
```

## DATA

- `_run_step_count`: `dict[str, int]` — maps `run_id` → next step index
- `current_step()` returns `int` (0-based)
- `log_metrics(..., step=N)` calls `mlflow.log_metric(k, v, step=N)` per metric

## HOW — Integration

No callers change in this step. `log_conversation()` and `log_conversation_artifacts()`
are updated in step 2. This step only adds infrastructure and verifies it works.

## Commit

```
fix(mlflow): add step tracking infrastructure to MLflowLogger (#593)
```

# Step 1: New `mlflow_db_utils.py` — `TrackingStats` dataclass and `query_sqlite_tracking()`

## Context
See [summary.md](./summary.md) for full architectural overview.

This step creates the new `mlflow_db_utils.py` module in isolation, fully tested before any other file touches it. It has no dependencies on MLflow, only stdlib `sqlite3` and `dataclasses`.

---

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_1.md.

Implement step 1: create src/mcp_coder/llm/mlflow_db_utils.py with a TrackingStats dataclass
and query_sqlite_tracking() function, plus its unit tests in tests/llm/test_mlflow_db_utils.py.

Follow TDD: write the tests first, then implement to make them pass.
Do not modify any existing files in this step.
Run pytest tests/llm/test_mlflow_db_utils.py, pylint, and mypy to confirm all checks pass.
```

---

## WHERE

| Item | Path |
|------|------|
| New source module | `src/mcp_coder/llm/mlflow_db_utils.py` |
| New test file | `tests/llm/test_mlflow_db_utils.py` |

No existing files are modified in this step.

---

## WHAT

### `TrackingStats` dataclass

```python
@dataclass
class TrackingStats:
    run_count: int                    # total runs matching source tag + experiment
    last_run_time: datetime | None    # UTC datetime of most recent run_count run, or None
    test_prompt_logged: bool          # True if a run exists with start_time >= since
```

### `query_sqlite_tracking()` function

```python
def query_sqlite_tracking(
    db_path: str,
    experiment_name: str,
    since: datetime | None = None,
) -> TrackingStats:
    """Query an MLflow SQLite database for tracking statistics.

    Uses raw sqlite3 only — no MLflow import.

    Args:
        db_path: Absolute path to the SQLite .db file (tilde already expanded by caller).
        experiment_name: MLflow experiment name to filter runs by.
        since: UTC datetime; if provided, test_prompt_logged is True when a
               run with start_time >= since exists.

    Returns:
        TrackingStats with run_count, last_run_time, test_prompt_logged.
        Returns TrackingStats(0, None, False) if the DB has no matching data.

    Raises:
        sqlite3.Error: If the database file is corrupt or schema is unexpected.
    """
```

---

## HOW

### Module location
`mlflow_db_utils.py` lives in `src/mcp_coder/llm/` alongside `mlflow_logger.py` and `mlflow_metrics.py`. It is a plain module — no `__init__.py` changes needed for `mlflow_logger.py` to import it in Step 2.

### Imports (source module)
```python
import sqlite3
from dataclasses import dataclass
from datetime import datetime
```
**No MLflow import.** This is the architectural constraint: `mlflow_logger.py` already imports `mlflow`; if `mlflow_db_utils.py` also imported `mlflow` it would be redundant and risk circular issues.

### Imports (test file)
```python
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
import pytest
from mcp_coder.llm.mlflow_db_utils import TrackingStats, query_sqlite_tracking
```

---

## ALGORITHM

```
open sqlite3 connection to db_path (read-only via uri mode)
join: experiments → runs on experiment_id, filtered by experiment name
join: runs → tags on run_uuid, filtered by tag key="mlflow.source.name", value="mcp-coder"
COUNT(*) and MAX(start_time) → run_count, last_run_epoch_ms
if since provided: query same join with WHERE start_time >= since_epoch_ms → test_prompt_logged
convert last_run_epoch_ms (int, ms since epoch) → datetime (UTC)
return TrackingStats(run_count, last_run_time, test_prompt_logged)
```

---

## DATA

### MLflow SQLite schema (relevant tables)

```
experiments(experiment_id, name, ...)
runs(run_uuid, experiment_id, start_time, ...)   -- start_time: ms since epoch (int)
tags(run_uuid, key, value)                        -- key="mlflow.source.name", value="mcp-coder"
```

### Return value
```python
TrackingStats(
    run_count=42,
    last_run_time=datetime(2026, 3, 20, 14, 30, tzinfo=timezone.utc),
    test_prompt_logged=True,
)
```

### Edge cases
- DB file does not exist → caller's responsibility (checked in `verify_mlflow()`); `sqlite3.Error` will propagate
- Experiment not found in DB → `run_count=0, last_run_time=None, test_prompt_logged=False`
- No runs with `mlflow.source.name=mcp-coder` → same zero-result case
- `since=None` → `test_prompt_logged=False` always (no timestamp to filter against)

---

## TESTS

### Test file: `tests/llm/test_mlflow_db_utils.py`

Tests create a real SQLite DB in `tmp_path` using raw `sqlite3` (the same schema MLflow uses), so the tests have zero dependency on MLflow being installed.

**Test classes and cases:**

```
TestTrackingStats
  test_dataclass_fields           — TrackingStats has run_count, last_run_time, test_prompt_logged

TestQuerySqliteTracking
  test_empty_db_returns_zeros     — no experiments/runs → (0, None, False)
  test_experiment_not_found       — experiment exists but wrong name → (0, None, False)
  test_counts_mcp_coder_runs      — 3 runs with correct tag → run_count=3
  test_ignores_other_source_tags  — run with tag value="other-tool" → not counted
  test_last_run_time_is_utc       — last_run_time is timezone-aware UTC datetime
  test_since_none_prompt_false    — since=None → test_prompt_logged=False
  test_since_before_run_true      — since set before run start_time → test_prompt_logged=True
  test_since_after_run_false      — since set after run start_time → test_prompt_logged=False
  test_since_exact_boundary_true  — since == run start_time → test_prompt_logged=True
```

### Helper in test file
```python
def _make_test_db(tmp_path: Path, runs: list[dict]) -> Path:
    """Create a minimal MLflow-schema SQLite DB with given runs.
    Each run dict: {start_time_ms, source_name, experiment_name}
    Returns path to .db file.
    """
```
This helper creates the exact tables MLflow uses (`experiments`, `runs`, `tags`) so tests are self-contained.

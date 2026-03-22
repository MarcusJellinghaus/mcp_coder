# Step 2: Update `verify_mlflow()` — `since=` parameter and `tracking_data` DB check

## Context
See [summary.md](./summary.md) for full architectural overview.

This step wires `mlflow_db_utils.py` (from Step 1) into `verify_mlflow()`. It adds the `since=` parameter, the `tracking_data` result key for SQLite backends, and the `"tracking_data"` label map entry. No changes to `execute_verify()` yet — that is Step 3.

---

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_2.md.

Implement step 2: update verify_mlflow() in src/mcp_coder/llm/mlflow_logger.py to accept
a since= parameter and add a tracking_data result key for SQLite backends by calling
query_sqlite_tracking() from mlflow_db_utils.py.
Also add "tracking_data" to _LABEL_MAP in src/mcp_coder/cli/commands/verify.py.

Follow TDD: extend tests/llm/test_mlflow_verify.py with new test cases first,
then implement the changes.
Run pytest tests/llm/test_mlflow_verify.py, pylint, and mypy to confirm all checks pass.
```

---

## WHERE

| Item | Path |
|------|------|
| Modified source | `src/mcp_coder/llm/mlflow_logger.py` |
| Modified source | `src/mcp_coder/cli/commands/verify.py` (one-line `_LABEL_MAP` addition) |
| Modified tests | `tests/llm/test_mlflow_verify.py` |

---

## WHAT

### Updated `verify_mlflow()` signature

```python
def verify_mlflow(since: datetime | None = None) -> dict[str, Any]:
    """Verify MLflow installation, configuration, and connectivity.

    Args:
        since: UTC datetime captured before the test prompt was sent.
               When provided and the backend is SQLite, the DB is queried
               to confirm a run with start_time >= since was logged.
               When None, tracking_data shows stats only (no prompt confirmation).

    Returns:
        Dict with keys: installed, enabled, and when enabled:
        tracking_uri, connection, experiment, artifact_location, tracking_data, overall_ok.
    """
```

### New `tracking_data` result key

Added to the result dict in three scenarios:

**SQLite backend, file exists, `since` provided:**
```python
{"ok": True,  "value": "42 runs, last: 2026-03-20 14:30 (test prompt logged)"}
{"ok": False, "value": "3 runs, last: 2026-03-20 14:30 (test prompt NOT logged)"}
```

**SQLite backend, file exists, `since=None`:**
```python
{"ok": True, "value": "42 runs, last: 2026-03-20 14:30"}
```

**MLflow disabled (installed but not enabled):**
```python
{"ok": None, "value": "skipped (MLflow disabled)"}
```

**HTTP backend or SQLite file not yet created:**
No `tracking_data` key added (existing behaviour preserved).

---

## HOW

### Import added to `mlflow_logger.py`
```python
# mlflow_logger.py already has: from datetime import datetime
# Only add timezone to the existing import:
from datetime import datetime, timezone  # ← add timezone to existing import
from .mlflow_db_utils import query_sqlite_tracking
```

### One-line change in `verify.py` `_LABEL_MAP`
```python
# MLflow section
"installed": "MLflow installed",
"enabled": "MLflow enabled",
"tracking_uri": "Tracking URI",
"connection": "Connection",
"experiment": "Experiment",
"artifact_location": "Artifact location",
"tracking_data": "Tracking data",          # ← ADD THIS LINE
```

### Integration point in `verify_mlflow()`

The `tracking_data` logic is inserted in two places:

1. **Disabled branch** (after `result["enabled"] = {"ok": False, "value": "disabled"}`):
```python
result["tracking_data"] = {"ok": None, "value": "skipped (MLflow disabled)"}
result["overall_ok"] = True
return result
```

2. **After the existing `tracking_uri` SQLite check** (when `uri.startswith("sqlite:///")`  and `tracking_uri["ok"] is True`):
```python
db_path = os.path.expanduser(config.tracking_uri[len("sqlite:///"):])
stats = query_sqlite_tracking(db_path, config.experiment_name, since)
result["tracking_data"] = _format_tracking_data(stats, since)
```

### New private helper `_format_tracking_data()`

```python
def _format_tracking_data(
    stats: TrackingStats,
    since: datetime | None,
) -> dict[str, Any]:
    """Format TrackingStats into a verify result entry."""
```

This keeps `verify_mlflow()` readable. The helper is tested indirectly through `verify_mlflow()` tests, which is sufficient.

---

## ALGORITHM

```
# Inside verify_mlflow(), after tracking_uri check for SQLite:
# Guard: Only query the SQLite DB when tracking_uri["ok"] is True.
db_path = expand_user(strip_sqlite_prefix(config.tracking_uri))
stats = query_sqlite_tracking(db_path, config.experiment_name, since)

last_str = format(stats.last_run_time, "%Y-%m-%d %H:%M") if last_run_time else "never"
base_value = f"{stats.run_count} runs, last: {last_str}"

if since is None:
    return {"ok": True, "value": base_value}
elif stats.test_prompt_logged:
    return {"ok": True, "value": f"{base_value} (test prompt logged)"}
else:
    return {"ok": False, "value": f"{base_value} (test prompt NOT logged)"}
```

### `overall_ok` update

The existing check:
```python
check_keys = ["tracking_uri", "connection", "experiment", "artifact_location"]
result["overall_ok"] = all(result.get(k, {}).get("ok", True) for k in check_keys)
```
Extend to include `tracking_data`:
```python
check_keys = ["tracking_uri", "connection", "experiment", "artifact_location", "tracking_data"]
```
Since `tracking_data` is only present when SQLite is active and the file exists, the `get(k, {}).get("ok", True)` default (`True` for missing key) means HTTP and missing-file cases are unaffected.

---

## DATA

### `_format_tracking_data()` return type
```python
dict[str, Any]  # always has "ok" (bool | None) and "value" (str)
```

### Updated `verify_mlflow()` return shape (SQLite, enabled, since provided)
```python
{
    "installed":        {"ok": True,  "value": "version 2.x.y"},
    "enabled":          {"ok": True,  "value": "(config.toml)"},
    "tracking_uri":     {"ok": True,  "value": "sqlite:///~/mlflow.db (file exists)"},
    "connection":       {"ok": True,  "value": "local backend"},
    "experiment":       {"ok": True,  "value": '"my-exp" (will be created on first use)'},
    "artifact_location":{"ok": True,  "value": "not configured (using default)"},
    "tracking_data":    {"ok": True,  "value": "42 runs, last: 2026-03-20 14:30 (test prompt logged)"},
    "overall_ok": True,
}
```

---

## TESTS

### New test cases to add to `tests/llm/test_mlflow_verify.py`

New class `TestVerifyMlflowTrackingData`:

```
test_tracking_data_skipped_when_disabled
    — disabled branch → tracking_data key present with ok=None, "skipped (MLflow disabled)"

test_tracking_data_sqlite_no_since
    — SQLite, file exists, since=None → tracking_data ok=True, value has run count, no prompt mention

test_tracking_data_sqlite_prompt_logged
    — SQLite, file exists, since provided, test_prompt_logged=True → ok=True, "(test prompt logged)"

test_tracking_data_sqlite_prompt_not_logged
    — SQLite, file exists, since provided, test_prompt_logged=False → ok=False, overall_ok=False

test_tracking_data_not_present_for_http
    — HTTP backend → no "tracking_data" key in result

test_tracking_data_not_present_when_db_missing
    — SQLite URI but file does not exist (tracking_uri ok=False) → no "tracking_data" key
```

### Mocking strategy
Patch `mcp_coder.llm.mlflow_logger.query_sqlite_tracking` to return a `TrackingStats` — keeps these as pure unit tests with no real SQLite DB or MLflow required.

```python
@patch("mcp_coder.llm.mlflow_logger.query_sqlite_tracking")
@patch("mcp_coder.llm.mlflow_logger.load_mlflow_config")
@patch("mcp_coder.llm.mlflow_logger.is_mlflow_available", return_value=True)
def test_tracking_data_sqlite_prompt_logged(
    _mock_avail, mock_config, mock_query, tmp_path
):
    db = tmp_path / "mlflow.db"
    db.touch()
    mock_config.return_value = MLflowConfig(
        enabled=True,
        tracking_uri=f"sqlite:///{db}",
        experiment_name="my-exp",
    )
    mock_query.return_value = TrackingStats(
        run_count=5,
        last_run_time=datetime(2026, 3, 20, 14, 30, tzinfo=timezone.utc),
        test_prompt_logged=True,
    )
    since = datetime(2026, 3, 20, 14, 0, tzinfo=timezone.utc)
    result = verify_mlflow(since=since)
    assert result["tracking_data"]["ok"] is True
    assert "test prompt logged" in result["tracking_data"]["value"]
    assert result["overall_ok"] is True
```

### Existing tests
All existing tests in `test_mlflow_verify.py` call `verify_mlflow()` with no arguments — the new `since=None` default means all pass without modification.

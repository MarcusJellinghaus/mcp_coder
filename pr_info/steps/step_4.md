# Step 4: Add `verify_mlflow()` Domain Function

> **Context:** Read `pr_info/steps/summary.md` first.

## Goal

Add `verify_mlflow()` to `llm/mlflow_logger.py`. It checks MLflow installation,
config, connectivity, experiment, and artifact location. Returns a structured dict.

## Tests First

### WHERE: `tests/llm/test_mlflow_verify.py` (new)

```python
class TestVerifyMlflow:
    """Tests for verify_mlflow() domain function."""

    def test_mlflow_not_installed(self) -> None:
        """When MLflow not importable, return informational result."""
        with patch("mcp_coder.llm.mlflow_logger.is_mlflow_available", return_value=False):
            result = verify_mlflow()
        assert result["installed"]["ok"] is False
        assert result["overall_ok"] is True  # informational, not a failure

    @patch("mcp_coder.llm.mlflow_logger.load_mlflow_config")
    @patch("mcp_coder.llm.mlflow_logger.is_mlflow_available", return_value=True)
    def test_mlflow_installed_but_disabled(self, mock_avail, mock_config) -> None:
        mock_config.return_value = MLflowConfig(enabled=False)
        result = verify_mlflow()
        assert result["installed"]["ok"] is True
        assert result["enabled"]["ok"] is False  # just shows status, not failure
        assert result["overall_ok"] is True

    @patch("mcp_coder.llm.mlflow_logger.load_mlflow_config")
    @patch("mcp_coder.llm.mlflow_logger.is_mlflow_available", return_value=True)
    def test_mlflow_enabled_sqlite_valid(self, mock_avail, mock_config, tmp_path) -> None:
        db_path = tmp_path / "mlflow.db"
        db_path.touch()
        mock_config.return_value = MLflowConfig(
            enabled=True,
            tracking_uri=f"sqlite:///{db_path}",
            experiment_name="test-exp",
        )
        result = verify_mlflow()
        assert result["tracking_uri"]["ok"] is True

    def test_mlflow_enabled_sqlite_missing_db(self, ...) -> None:
        ...  # DB file doesn't exist → tracking_uri.ok=False

    def test_mlflow_enabled_invalid_uri(self, ...) -> None:
        ...  # validate_tracking_uri raises → tracking_uri.ok=False

    def test_mlflow_enabled_http_reachable(self, ...) -> None:
        ...  # Mock MLflow SDK → connection.ok=True

    def test_mlflow_enabled_http_unreachable(self, ...) -> None:
        ...  # Mock MLflow SDK raises → connection.ok=False

    def test_mlflow_enabled_http_timeout(self, ...) -> None:
        ...  # 10s timeout scenario

    def test_artifact_location_writable(self, tmp_path, ...) -> None:
        ...  # Directory exists and writable → ok=True

    def test_artifact_location_not_exists(self, ...) -> None:
        ...  # Directory doesn't exist → ok=False

    def test_experiment_exists(self, ...) -> None:
        ...  # Mock get_experiment_by_name returns experiment

    def test_experiment_not_found(self, ...) -> None:
        ...  # Mock get_experiment_by_name returns None
```

## Implementation

### WHERE: `src/mcp_coder/llm/mlflow_logger.py` (add function)

**WHAT:**
```python
def verify_mlflow() -> dict[str, Any]:
```

Add to existing `__all__`:
```python
__all__ = ["MLflowLogger", "is_mlflow_available", "verify_mlflow"]
```

**ALGORITHM:**
```
1. Check is_mlflow_available() → installed entry; if False, return early
2. Get MLflow version via importlib.metadata.version("mlflow")
3. Load config via load_mlflow_config() → enabled entry
4. If not enabled: return early (overall_ok=True, informational)
5. Validate tracking_uri format, check URI-specific reachability
6. For HTTP URIs: MLflow SDK probe with 10s timeout
7. Check experiment_name exists, check artifact_location writable
8. Return dict
```

**DATA — Return structure:**
```python
{
    "installed":          {"ok": bool, "value": "version 2.18.0" | "not installed"},
    "enabled":            {"ok": bool, "value": "(config.toml)" | "disabled"},
    # --- below only present when enabled=True ---
    "tracking_uri":       {"ok": bool, "value": str, "error": str|None},
    "connection":         {"ok": bool, "value": "tracking server reachable" | error},
    "experiment":         {"ok": bool, "value": '"name" (exists)' | '"name" (not found)'},
    "artifact_location":  {"ok": bool, "value": "path (writable)" | "path (not writable/missing)"},
    "overall_ok":         bool,
}
```

**HOW — MLflow version:**
```python
from importlib.metadata import version as pkg_version
mlflow_version = pkg_version("mlflow")
```

**HOW — URI-specific reachability checks:**
```python
def _check_tracking_uri(uri: str) -> dict:
    # Validate format first
    try:
        validate_tracking_uri(uri)
    except ValueError as e:
        return {"ok": False, "value": uri, "error": str(e)}

    if uri.startswith("sqlite:///"):
        path = uri[len("sqlite:///"):]
        path = os.path.expanduser(path)
        exists = os.path.exists(path)
        return {"ok": exists, "value": f"{uri} ({'file exists' if exists else 'file NOT found'})"}

    if uri.startswith(("http://", "https://")):
        return {"ok": True, "value": uri}  # connectivity checked separately via SDK

    if uri.startswith("file://"):
        path = uri[len("file://"):]
        if path.startswith("/") and os.name == "nt":
            path = path[1:]  # strip leading / on Windows
        exists = os.path.isdir(path)
        return {"ok": exists, "value": f"{uri} ({'exists' if exists else 'NOT found'})"}

    return {"ok": True, "value": uri}
```

**HOW — MLflow SDK probe for HTTP URIs (10s timeout):**
```python
def _probe_mlflow_connection(uri: str, experiment_name: str) -> tuple[dict, dict]:
    """Returns (connection_entry, experiment_entry)."""
    import mlflow
    import signal  # or threading.Timer on Windows

    mlflow.set_tracking_uri(uri)
    try:
        experiment = mlflow.get_experiment_by_name(experiment_name)
        conn = {"ok": True, "value": "tracking server reachable"}
        if experiment:
            exp = {"ok": True, "value": f'"{experiment_name}" (exists)'}
        else:
            exp = {"ok": False, "value": f'"{experiment_name}" (not found)'}
        return conn, exp
    except Exception as e:
        conn = {"ok": False, "value": f"unreachable: {e}"}
        exp = {"ok": False, "value": f'"{experiment_name}" (could not check)'}
        return conn, exp
```

> **Timeout:** Use `threading.Timer` to interrupt the SDK call after 10 seconds
> (cross-platform, works on Windows unlike `signal.alarm`).

**HOW — Artifact location check:**
```python
def _check_artifact_location(path: str | None) -> dict:
    if not path:
        return {"ok": True, "value": "not configured (using default)"}
    expanded = os.path.expanduser(path)
    abs_path = os.path.abspath(expanded)
    if not os.path.isdir(abs_path):
        return {"ok": False, "value": f"{path} (directory NOT found)"}
    if os.access(abs_path, os.W_OK):
        return {"ok": True, "value": f"{path} (writable)"}
    return {"ok": False, "value": f"{path} (not writable)"}
```

**HOW — `overall_ok` logic:**
```python
# overall_ok=True when:
#   - mlflow not installed (informational)
#   - mlflow installed but not enabled (informational)
#   - mlflow enabled and all probes pass
# overall_ok=False when:
#   - mlflow enabled but: bad URI, unreachable, experiment not found
```

## Checklist

- [ ] `verify_mlflow()` returns structured dict
- [ ] Works when MLflow not installed (graceful, `overall_ok=True`)
- [ ] Works when MLflow disabled (informational, `overall_ok=True`)
- [ ] Validates tracking URI format
- [ ] Checks SQLite file existence
- [ ] Checks HTTP connectivity via MLflow SDK with 10s timeout
- [ ] Checks file:// directory existence
- [ ] Checks experiment existence
- [ ] Checks artifact location writable
- [ ] All tests pass with mocked MLflow and config

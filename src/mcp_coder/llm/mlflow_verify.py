"""MLflow verification helpers for installation, configuration, and connectivity.

This module provides standalone verification functions that check MLflow
availability, configuration validity, and backend connectivity without touching
the MLflowLogger class.
"""

import os
import sqlite3
from datetime import datetime
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as pkg_version
from typing import Any

from ..config.mlflow_config import validate_tracking_uri
from ..utils import load_mlflow_config
from .mlflow_db_utils import TrackingStats, query_sqlite_tracking
from .mlflow_logger import is_mlflow_available  # one-way sibling import, no cycle


def _check_tracking_uri(uri: str) -> dict[str, Any]:
    """Validate tracking URI format and check URI-specific reachability.

    Returns:
        Dict with 'ok' (bool) and 'value' (str) keys indicating validation result.
    """
    try:
        validate_tracking_uri(uri)
    except ValueError as e:
        return {"ok": False, "value": uri, "error": str(e)}

    if uri.startswith("sqlite:///"):
        path = uri[len("sqlite:///") :]
        path = os.path.expanduser(path)
        exists = os.path.exists(path)
        return {
            "ok": exists,
            "value": f"{uri} ({'file exists' if exists else 'file NOT found'})",
        }

    if uri.startswith(("http://", "https://")):
        return {"ok": True, "value": uri}  # connectivity checked separately via SDK

    if uri.startswith("file://"):
        path = uri[len("file://") :]
        if path.startswith("/") and os.name == "nt":
            # file:///C:/path → /C:/path after prefix strip; remove leading /
            # so os.path.isdir sees "C:/path" instead of "/C:/path"
            path = path[1:]
        exists = os.path.isdir(path)
        return {
            "ok": exists,
            "value": f"{uri} ({'exists' if exists else 'NOT found'})",
        }

    return {"ok": True, "value": uri}


def _probe_mlflow_connection(
    uri: str, experiment_name: str
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Probe MLflow server connectivity and experiment existence.

    No timeout applied — user can Ctrl+C if the server is unreachable.

    Returns:
        Tuple of (connection_entry, experiment_entry) dicts, each with
        'ok' (bool) and 'value' (str) keys.
    """
    import mlflow  # pylint: disable=import-error

    mlflow.set_tracking_uri(uri)
    try:
        experiment = mlflow.get_experiment_by_name(experiment_name)
        conn: dict[str, Any] = {"ok": True, "value": "tracking server reachable"}
        if experiment:
            exp: dict[str, Any] = {
                "ok": True,
                "value": f'"{experiment_name}" (exists)',
            }
        else:
            exp = {
                "ok": False,
                "value": f'"{experiment_name}" (not found)',
            }
        return conn, exp
    except (
        Exception
    ) as e:  # pylint: disable=broad-exception-caught  # mlflow graceful-degradation — optional dependency
        conn = {"ok": False, "value": f"unreachable: {e}"}
        exp = {"ok": False, "value": f'"{experiment_name}" (could not check)'}
        return conn, exp


def _check_artifact_location(path: str | None) -> dict[str, Any]:
    """Check if artifact location directory exists and is writable.

    Returns:
        Dict with 'ok' (bool) and 'value' (str) keys indicating check result.
    """
    if not path:
        return {"ok": True, "value": "not configured (using default)"}
    expanded = os.path.expanduser(path)
    abs_path = os.path.abspath(expanded)
    if not os.path.isdir(abs_path):
        return {"ok": False, "value": f"{path} (directory NOT found)"}
    if os.access(abs_path, os.W_OK):
        return {"ok": True, "value": f"{path} (writable)"}
    return {"ok": False, "value": f"{path} (not writable)"}


def _format_tracking_data(
    stats: TrackingStats,
    since: datetime | None,
) -> dict[str, Any]:
    """Format TrackingStats into a verify result entry.

    Args:
        stats: Tracking statistics from SQLite query.
        since: UTC cutoff for confirming test prompt was logged.

    Returns:
        Dict with 'ok' and 'value' keys for the verify result.
    """
    if stats.last_run_time is not None:
        last_str = stats.last_run_time.strftime("%Y-%m-%d %H:%M")
    else:
        last_str = "never"
    base_value = f"{stats.run_count} runs, last: {last_str}"

    if since is None:
        return {"ok": True, "value": base_value}
    if stats.test_prompt_logged:
        return {"ok": True, "value": f"{base_value} (test prompt logged)"}
    return {"ok": False, "value": f"{base_value} (test prompt NOT logged)"}


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

    overall_ok semantics:
        True  = no action needed (not installed, disabled, or all checks pass)
        False = misconfigured and needs fixing (enabled but broken)
    """
    result: dict[str, Any] = {}

    # 1. Check installation
    if not is_mlflow_available():
        result["installed"] = {"ok": False, "value": "not installed"}
        result["overall_ok"] = True  # informational, not a failure
        return result

    # 2. Get MLflow version
    try:
        mlflow_version = pkg_version("mlflow")
    except PackageNotFoundError:
        mlflow_version = "unknown"
    result["installed"] = {"ok": True, "value": f"version {mlflow_version}"}

    # 3. Load config
    config = load_mlflow_config()
    if not config.enabled:
        result["enabled"] = {"ok": False, "value": "disabled"}
        result["tracking_data"] = {"ok": None, "value": "skipped (MLflow disabled)"}
        result["overall_ok"] = True  # informational, not a failure
        return result

    result["enabled"] = {"ok": True, "value": "(config.toml)"}

    # 4. Validate tracking URI
    if config.tracking_uri:
        result["tracking_uri"] = _check_tracking_uri(config.tracking_uri)
    else:
        result["tracking_uri"] = {"ok": True, "value": "not configured (using default)"}

    # 5. For HTTP URIs: probe MLflow SDK connection and experiment
    if config.tracking_uri and config.tracking_uri.startswith(("http://", "https://")):
        conn, exp = _probe_mlflow_connection(
            config.tracking_uri, config.experiment_name
        )
        result["connection"] = conn
        result["experiment"] = exp
    else:
        # For non-HTTP URIs, connection check is implicit in URI check
        result["connection"] = {"ok": True, "value": "local backend"}
        result["experiment"] = {
            "ok": True,
            "value": f'"{config.experiment_name}" (will be created on first use)',
        }

    # 6. Check artifact location
    result["artifact_location"] = _check_artifact_location(config.artifact_location)

    # 7. Query SQLite tracking data when backend is SQLite and file exists
    uri = config.tracking_uri or ""
    tracking_uri_entry = result.get("tracking_uri", {})
    if uri.startswith("sqlite:///") and tracking_uri_entry.get("ok") is True:
        db_path = os.path.expanduser(uri[len("sqlite:///") :])
        try:
            stats = query_sqlite_tracking(db_path, config.experiment_name, since)
            result["tracking_data"] = _format_tracking_data(stats, since)
        except sqlite3.Error as e:
            result["tracking_data"] = {"ok": False, "value": f"query failed: {e}"}

    # overall_ok: True when all checks pass, False when any enabled check fails
    check_keys = [
        "tracking_uri",
        "connection",
        "experiment",
        "artifact_location",
        "tracking_data",
    ]
    result["overall_ok"] = all(result.get(k, {}).get("ok", True) for k in check_keys)

    return result

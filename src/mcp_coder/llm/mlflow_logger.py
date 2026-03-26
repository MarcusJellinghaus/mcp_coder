"""MLflow logging for LLM conversations with graceful fallback.

This module provides optional MLflow logging that gracefully handles
cases where MLflow is not installed or configured.
"""

import json
import logging
import os
import sqlite3
import tempfile
from collections import OrderedDict
from datetime import datetime, timezone
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as pkg_version
from typing import Any, Dict, Optional

from ..config import MLflowConfig
from ..config.mlflow_config import validate_tracking_uri
from ..utils import load_mlflow_config
from .mlflow_db_utils import TrackingStats, query_sqlite_tracking

try:
    from .mlflow_metrics import ConversationMetrics
except ImportError:
    ConversationMetrics = None  # type: ignore


logger = logging.getLogger(__name__)

__all__ = [
    "MLflowLogger",
    "is_mlflow_available",
    "verify_mlflow",
]

# Global flag to track MLflow availability (cached after first check)
_mlflow_available: Optional[bool] = None


def is_mlflow_available() -> bool:
    """Check if MLflow is available for import.

    Returns:
        True if MLflow can be imported, False otherwise

    Note:
        Result is cached after first call for performance.
    """
    global _mlflow_available  # pylint: disable=global-statement  # module-level singleton

    if _mlflow_available is None:
        try:
            import mlflow  # noqa: F401  # type: ignore[import-untyped,import-not-found]  # pylint: disable=import-error,unused-import

            _mlflow_available = True
            logger.debug("MLflow is available")
        except ImportError:
            _mlflow_available = False
            logger.debug("MLflow is not installed")

    return _mlflow_available


class MLflowLogger:
    """MLflow logger with graceful fallback when MLflow is unavailable.

    This logger handles all MLflow operations with comprehensive error handling,
    ensuring that the main application continues to work even if MLflow fails.
    """

    _MAX_SESSION_MAP_SIZE: int = 100

    def __init__(self, config: Optional[MLflowConfig] = None):
        """Initialize MLflow logger.

        Args:
            config: MLflow configuration. If None, loads from config.toml
        """
        self.config = config or load_mlflow_config()
        self.active_run_id: Optional[str] = None
        self._mlflow_module: Any = None
        self._session_run_map: OrderedDict[str, str] = OrderedDict()
        self._run_step_count: dict[str, int] = {}

        # Only initialize MLflow if it's available and enabled
        if self.config.enabled and is_mlflow_available():
            try:
                self._initialize_mlflow()
            except (
                Exception
            ) as e:  # pylint: disable=broad-exception-caught  # mlflow graceful-degradation — optional dependency
                logger.warning(f"Failed to initialize MLflow: {e}")
                self.config.enabled = False  # Disable to prevent further attempts

    def _initialize_mlflow(self) -> None:
        """Initialize MLflow tracking and experiment."""
        try:
            import mlflow  # pylint: disable=import-error

            self._mlflow_module = mlflow

            # Set tracking URI if specified
            if self.config.tracking_uri:
                uri = self.config.tracking_uri
                # Check if URI already has a scheme (file://, http://, sqlite://, etc.)
                if "://" in uri:
                    # For SQLite URIs, expand ~ in the path portion
                    if uri.startswith("sqlite:///"):
                        path_part = uri[len("sqlite:///") :]
                        if "~" in path_part:
                            expanded_path = os.path.expanduser(path_part)
                            # Convert Windows backslashes to forward slashes
                            expanded_path = expanded_path.replace("\\", "/")
                            tracking_uri = f"sqlite:///{expanded_path}"
                        else:
                            tracking_uri = uri
                    else:
                        # Other URIs (http://, file://) use as-is
                        tracking_uri = uri
                else:
                    # Plain path - expand ~ and convert to file URI
                    expanded_path = os.path.expanduser(uri)
                    abs_path = os.path.abspath(expanded_path)
                    # Convert to file URI format
                    if os.name == "nt":  # Windows
                        tracking_uri = "file:///" + abs_path.replace("\\", "/")
                    else:
                        tracking_uri = "file://" + abs_path
                mlflow.set_tracking_uri(tracking_uri)
                logger.debug(
                    f"MLflow tracking URI set to: {tracking_uri} (from {self.config.tracking_uri})"
                )

            # Set or create experiment with optional artifact location
            try:
                # If artifact_location is specified, create/get experiment with that location
                if self.config.artifact_location:
                    # Expand ~ and convert to absolute path
                    artifact_root = os.path.expanduser(self.config.artifact_location)
                    artifact_root = os.path.abspath(artifact_root)

                    # Convert to file:// URI format for MLflow
                    if os.name == "nt":  # Windows
                        artifact_uri = "file:///" + artifact_root.replace("\\", "/")
                    else:
                        artifact_uri = "file://" + artifact_root

                    # Get or create experiment with specified artifact location
                    experiment = mlflow.get_experiment_by_name(
                        self.config.experiment_name
                    )
                    if experiment is None:
                        # Create new experiment with artifact location
                        mlflow.create_experiment(
                            self.config.experiment_name, artifact_location=artifact_uri
                        )
                        logger.debug(
                            f"Created MLflow experiment '{self.config.experiment_name}' "
                            f"with artifact_location: {artifact_uri}"
                        )
                    else:
                        logger.debug(
                            f"Using existing MLflow experiment '{self.config.experiment_name}' "
                            f"(artifact_location: {experiment.artifact_location})"
                        )
                    mlflow.set_experiment(self.config.experiment_name)
                else:
                    # Use default artifact location
                    mlflow.set_experiment(self.config.experiment_name)
                    logger.debug(
                        f"MLflow experiment set to: {self.config.experiment_name}"
                    )
            except (
                Exception
            ) as e:  # pylint: disable=broad-exception-caught  # mlflow graceful-degradation — optional dependency
                logger.warning(
                    f"Failed to set MLflow experiment '{self.config.experiment_name}': {e}"
                )

        except (
            Exception
        ) as e:  # pylint: disable=broad-exception-caught  # mlflow graceful-degradation — optional dependency
            logger.error(f"Failed to initialize MLflow: {e}")
            raise

    def has_session(self, session_id: str) -> bool:
        """Check if a session_id is in the session map.

        Args:
            session_id: The Claude session ID to look up

        Returns:
            True if the session is known, False otherwise
        """
        return session_id in self._session_run_map

    def current_step(self) -> int:
        """Return the current step index for the active run (0 if no run or first step)."""
        if not self.active_run_id:
            return 0
        return self._run_step_count.get(self.active_run_id, 0)

    def _advance_step(self) -> None:
        """Increment the step counter for the active run."""
        if self.active_run_id:
            self._run_step_count[self.active_run_id] = self.current_step() + 1

    def start_run(
        self,
        session_id: Optional[str] = None,
        run_name: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None,
    ) -> Optional[str]:
        """Start an MLflow run for conversation tracking.

        Args:
            session_id: Optional Claude session ID; if known, resumes the existing run
            run_name: Optional name for the run (used only when creating a new run)
            tags: Optional tags to add to the run (used only when creating a new run)

        Returns:
            Run ID if successful, None if MLflow unavailable or disabled
        """
        if not self._is_enabled():
            return None

        try:
            import mlflow  # pylint: disable=import-error

            # Resume existing run when session is known
            if session_id is not None and session_id in self._session_run_map:
                if self.active_run_id is not None:
                    logger.warning(
                        f"start_run called with active run {self.active_run_id}; "
                        "ending it before resuming session run"
                    )
                    mlflow.end_run()
                    self.active_run_id = None
                run = mlflow.start_run(run_id=self._session_run_map[session_id])
                self.active_run_id = run.info.run_id
                logger.debug(f"Resumed MLflow run: {self.active_run_id}")
                return self.active_run_id

            # Generate run name if not provided
            if not run_name:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                run_name = f"conversation_{timestamp}"

            # Start the run
            run = mlflow.start_run(run_name=run_name)
            self.active_run_id = run.info.run_id

            # Add default tags
            default_tags = {
                "mlflow.source.name": "mcp-coder",
                "conversation.timestamp": datetime.now().isoformat(),
            }
            if tags:
                default_tags.update(tags)

            mlflow.set_tags(default_tags)
            logger.debug(f"Started MLflow run: {self.active_run_id}")
            return self.active_run_id

        except (
            Exception
        ) as e:  # pylint: disable=broad-exception-caught  # mlflow graceful-degradation — optional dependency
            logger.warning(f"Failed to start MLflow run: {e}")
            return None

    def log_params(self, params: Dict[str, Any]) -> None:
        """Log parameters to the current MLflow run.

        Args:
            params: Parameters to log
        """
        if not self._is_enabled() or not self.active_run_id:
            return

        try:
            import mlflow  # pylint: disable=import-error

            # Convert all values to strings for MLflow compatibility
            str_params = {k: str(v) for k, v in params.items() if v is not None}
            mlflow.log_params(str_params)
            logger.debug(f"Logged {len(str_params)} parameters to MLflow")

        except (
            Exception
        ) as e:  # pylint: disable=broad-exception-caught  # mlflow graceful-degradation — optional dependency
            logger.warning(f"Failed to log parameters to MLflow: {e}")

    def log_metrics(
        self, metrics: Dict[str, float], step: Optional[int] = None
    ) -> None:
        """Log metrics to the current MLflow run.

        Args:
            metrics: Metrics to log (must be numeric)
            step: Optional step index for time-series metrics
        """
        if not self._is_enabled() or not self.active_run_id:
            return

        try:
            import mlflow  # pylint: disable=import-error

            # Filter to only numeric values
            numeric_metrics = {}
            for k, v in metrics.items():
                try:
                    numeric_metrics[k] = float(v)
                except (TypeError, ValueError):
                    logger.debug(f"Skipping non-numeric metric '{k}': {v}")

            if numeric_metrics:
                if step is None:
                    mlflow.log_metrics(numeric_metrics)
                else:
                    for key, value in numeric_metrics.items():
                        mlflow.log_metric(key, value, step=step)
                logger.debug(f"Logged {len(numeric_metrics)} metrics to MLflow")

        except (
            Exception
        ) as e:  # pylint: disable=broad-exception-caught  # mlflow graceful-degradation — optional dependency
            logger.warning(f"Failed to log metrics to MLflow: {e}")

    def log_artifact(self, content: str, filename: str) -> None:
        """Log a text artifact to the current MLflow run.

        Args:
            content: Content to log
            filename: Name of the artifact file
        """
        if not self._is_enabled() or not self.active_run_id:
            return

        try:
            import mlflow  # pylint: disable=import-error

            # Create temporary directory and file with the correct name
            temp_dir = tempfile.mkdtemp()
            temp_path = os.path.join(temp_dir, filename)

            try:
                # Write content to file with proper name
                with open(temp_path, "w", encoding="utf-8") as f:
                    f.write(content)

                # Log the file to MLflow
                mlflow.log_artifact(temp_path, "conversation_data")
                logger.debug(f"Logged artifact '{filename}' to MLflow")
            finally:
                # Clean up temporary file and directory
                try:
                    os.unlink(temp_path)
                    os.rmdir(temp_dir)
                except OSError:
                    pass

        except (
            Exception
        ) as e:  # pylint: disable=broad-exception-caught  # mlflow graceful-degradation — optional dependency
            logger.warning(f"Failed to log artifact '{filename}' to MLflow: {e}")

    def _log_step_params_and_artifacts(
        self,
        step: int,
        prompt: str,
        response_data: Dict[str, Any],
        metadata: Dict[str, Any],
    ) -> None:
        """Log step params and artifacts shared by conversation logging methods.

        Logs stable params at step 0, plus step-prefixed all_params, prompt,
        and conversation artifacts. Does NOT advance the step counter.

        Args:
            step: Current step index
            prompt: The user prompt
            response_data: LLM response data
            metadata: Additional metadata
        """
        # Stable params only at step 0
        if step == 0:
            stable_params = {
                "model": metadata.get("model", "unknown"),
                "provider": response_data.get("provider", "unknown"),
                "working_directory": metadata.get("working_directory"),
            }
            self.log_params(stable_params)

        # All param values as step artifact
        all_params = {
            "model": metadata.get("model", "unknown"),
            "provider": response_data.get("provider", "unknown"),
            "working_directory": metadata.get("working_directory"),
            "branch_name": metadata.get("branch_name"),
            "step_name": metadata.get("step_name"),
            "prompt_length": len(prompt),
        }
        self.log_artifact(
            json.dumps(all_params, indent=2, default=str),
            f"step_{step}_all_params.json",
        )

        # Step-prefixed artifacts
        self.log_artifact(prompt, f"step_{step}_prompt.txt")
        conversation_data = {
            "prompt": prompt,
            "response_data": response_data,
            "metadata": metadata,
        }
        self.log_artifact(
            json.dumps(conversation_data, indent=2, default=str),
            f"step_{step}_conversation.json",
        )

    def log_conversation(
        self,
        prompt: str,
        response_data: Dict[str, Any],
        metadata: Dict[str, Any],
    ) -> None:
        """Log a complete conversation to MLflow with step-aware metrics.

        Args:
            prompt: The user prompt
            response_data: LLM response data
            metadata: Additional metadata
        """
        if not self._is_enabled():
            return

        try:
            step = self.current_step()
            session_info = response_data.get("raw_response", {}).get("session_info", {})

            self._log_step_params_and_artifacts(step, prompt, response_data, metadata)

            # Collect all numeric metrics
            numeric_metrics: Dict[str, float] = {
                "prompt_length": float(len(prompt)),
            }
            if "duration_ms" in response_data:
                numeric_metrics["duration_ms"] = float(response_data["duration_ms"])
            if "cost_usd" in response_data:
                numeric_metrics["cost_usd"] = float(response_data["cost_usd"])

            # Usage metrics
            if isinstance(session_info, dict):
                usage = session_info.get("usage", {})
                if isinstance(usage, dict):
                    for key, value in usage.items():
                        if isinstance(value, (int, float)):
                            numeric_metrics[f"usage_{key}"] = float(value)

            # Performance metrics
            if ConversationMetrics is not None:
                try:
                    metrics_calculator = ConversationMetrics()
                    perf_metrics = metrics_calculator.extract_performance_metrics(
                        response_data
                    )
                    numeric_metrics.update(perf_metrics)
                except (
                    Exception
                ) as e:  # pylint: disable=broad-exception-caught  # mlflow graceful-degradation — optional dependency
                    logger.debug(f"Failed to calculate performance metrics: {e}")

            self.log_metrics(numeric_metrics, step=step)
            self._advance_step()

        except (
            Exception
        ) as e:  # pylint: disable=broad-exception-caught  # mlflow graceful-degradation — optional dependency
            logger.warning(f"Failed to log conversation to MLflow: {e}")

    def log_error_metrics(
        self, error: Exception, duration_ms: Optional[int] = None
    ) -> None:
        """Log error-specific metrics to MLflow.

        Args:
            error: The exception that occurred
            duration_ms: Duration before error occurred
        """
        if not self._is_enabled() or not self.active_run_id:
            return

        try:
            # Basic error metrics
            error_metrics = {"has_error": 1.0}
            if duration_ms is not None:
                error_metrics["error_duration_ms"] = float(duration_ms)

            # Advanced error metrics if available
            if ConversationMetrics is not None:
                try:
                    metrics_calculator = ConversationMetrics()
                    advanced_error_metrics = metrics_calculator.get_error_metrics(
                        error, duration_ms
                    )
                    error_metrics.update(advanced_error_metrics)
                except (
                    Exception
                ) as e:  # pylint: disable=broad-exception-caught  # mlflow graceful-degradation — optional dependency
                    logger.debug(f"Failed to calculate advanced error metrics: {e}")

            self.log_metrics(error_metrics, step=self.current_step())
            self._advance_step()

        except (
            Exception
        ) as e:  # pylint: disable=broad-exception-caught  # mlflow graceful-degradation — optional dependency
            logger.warning(f"Failed to log error metrics to MLflow: {e}")

    def log_conversation_artifacts(
        self,
        prompt: str,
        response_data: Dict[str, Any],
        metadata: Dict[str, Any],
    ) -> None:
        """Log prompt params and artifacts for a conversation (no metrics).

        Args:
            prompt: The user prompt
            response_data: LLM response data
            metadata: Additional metadata
        """
        if not self._is_enabled() or not self.active_run_id:
            return

        step = self.current_step()
        self._log_step_params_and_artifacts(step, prompt, response_data, metadata)
        self._advance_step()

    def end_run(
        self, status: str = "FINISHED", session_id: Optional[str] = None
    ) -> None:
        """End the current MLflow run.

        Args:
            status: Run status (FINISHED, FAILED, KILLED)
            session_id: Optional Claude session ID; if provided, stores session→run mapping
        """
        if not self._is_enabled() or not self.active_run_id:
            return

        try:
            import mlflow  # pylint: disable=import-error

            # Clean up step count when run won't be resumed
            if session_id is None and self.active_run_id in self._run_step_count:
                del self._run_step_count[self.active_run_id]

            # Store session→run mapping with LRU eviction before clearing run_id
            if session_id is not None:
                self._session_run_map.pop(session_id, None)  # reset LRU order
                self._session_run_map[session_id] = self.active_run_id
                if len(self._session_run_map) > self._MAX_SESSION_MAP_SIZE:
                    _, evicted_run_id = self._session_run_map.popitem(last=False)
                    self._run_step_count.pop(evicted_run_id, None)  # evict LRU

            mlflow.end_run(status=status)
            logger.debug(f"Ended MLflow run: {self.active_run_id}")
            self.active_run_id = None

        except (
            Exception
        ) as e:  # pylint: disable=broad-exception-caught  # mlflow graceful-degradation — optional dependency
            logger.warning(f"Failed to end MLflow run: {e}")
            self.active_run_id = None  # Clear anyway to prevent stuck state

    def _is_enabled(self) -> bool:
        """Check if MLflow logging is enabled and available.

        Returns:
            True if MLflow is enabled in config and available for import.
        """
        return self.config.enabled and is_mlflow_available()


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


# Singleton instance for global use
_global_logger: Optional[MLflowLogger] = None


def get_mlflow_logger() -> MLflowLogger:
    """Get the global MLflow logger instance.

    Returns:
        Global MLflowLogger instance (created on first call)
    """
    global _global_logger  # pylint: disable=global-statement  # module-level singleton
    if _global_logger is None:
        config = load_mlflow_config()  # Explicitly load config to satisfy tests
        _global_logger = MLflowLogger(config)
    return _global_logger

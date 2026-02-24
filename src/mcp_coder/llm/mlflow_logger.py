"""MLflow logging for LLM conversations with graceful fallback.

This module provides optional MLflow logging that gracefully handles
cases where MLflow is not installed or configured.
"""

import json
import logging
import os
import tempfile
from datetime import datetime
from typing import Any, Dict, Optional

from ..config.mlflow_config import MLflowConfig, load_mlflow_config

try:
    from .mlflow_metrics import ConversationMetrics
except ImportError:
    ConversationMetrics = None  # type: ignore


logger = logging.getLogger(__name__)

__all__ = [
    "MLflowLogger",
    "is_mlflow_available",
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
    global _mlflow_available

    if _mlflow_available is None:
        try:
            import mlflow  # noqa: F401

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

    def __init__(self, config: Optional[MLflowConfig] = None):
        """Initialize MLflow logger.

        Args:
            config: MLflow configuration. If None, loads from config.toml
        """
        self.config = config or load_mlflow_config()
        self.active_run_id: Optional[str] = None
        self._mlflow_module = None

        # Only initialize MLflow if it's available and enabled
        if self.config.enabled and is_mlflow_available():
            try:
                self._initialize_mlflow()
            except Exception as e:
                logger.warning(f"Failed to initialize MLflow: {e}")
                self.config.enabled = False  # Disable to prevent further attempts

    def _initialize_mlflow(self) -> None:
        """Initialize MLflow tracking and experiment."""
        try:
            import mlflow

            self._mlflow_module = mlflow

            # Set tracking URI if specified
            if self.config.tracking_uri:
                mlflow.set_tracking_uri(self.config.tracking_uri)
                logger.debug(f"MLflow tracking URI set to: {self.config.tracking_uri}")

            # Set or create experiment
            try:
                mlflow.set_experiment(self.config.experiment_name)
                logger.debug(f"MLflow experiment set to: {self.config.experiment_name}")
            except Exception as e:
                logger.warning(
                    f"Failed to set MLflow experiment '{self.config.experiment_name}': {e}"
                )

        except Exception as e:
            logger.error(f"Failed to initialize MLflow: {e}")
            raise

    def start_run(
        self,
        run_name: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None,
    ) -> Optional[str]:
        """Start an MLflow run for conversation tracking.

        Args:
            run_name: Optional name for the run
            tags: Optional tags to add to the run

        Returns:
            Run ID if successful, None if MLflow unavailable or disabled
        """
        if not self._is_enabled():
            return None

        try:
            import mlflow

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

        except Exception as e:
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
            import mlflow

            # Convert all values to strings for MLflow compatibility
            str_params = {k: str(v) for k, v in params.items() if v is not None}
            mlflow.log_params(str_params)
            logger.debug(f"Logged {len(str_params)} parameters to MLflow")

        except Exception as e:
            logger.warning(f"Failed to log parameters to MLflow: {e}")

    def log_metrics(self, metrics: Dict[str, float]) -> None:
        """Log metrics to the current MLflow run.

        Args:
            metrics: Metrics to log (must be numeric)
        """
        if not self._is_enabled() or not self.active_run_id:
            return

        try:
            import mlflow

            # Filter to only numeric values
            numeric_metrics = {}
            for k, v in metrics.items():
                try:
                    numeric_metrics[k] = float(v)
                except (TypeError, ValueError):
                    logger.debug(f"Skipping non-numeric metric '{k}': {v}")

            if numeric_metrics:
                mlflow.log_metrics(numeric_metrics)
                logger.debug(f"Logged {len(numeric_metrics)} metrics to MLflow")

        except Exception as e:
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
            import mlflow

            # Create temporary file for the artifact
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=f"_{filename}", delete=False, encoding="utf-8"
            ) as f:
                f.write(content)
                temp_path = f.name

            try:
                mlflow.log_artifact(temp_path, "conversation_data")
                logger.debug(f"Logged artifact '{filename}' to MLflow")
            finally:
                # Clean up temporary file
                try:
                    os.unlink(temp_path)
                except OSError:
                    pass

        except Exception as e:
            logger.warning(f"Failed to log artifact '{filename}' to MLflow: {e}")

    def log_conversation(
        self,
        prompt: str,
        response_data: Dict[str, Any],
        metadata: Dict[str, Any],
    ) -> None:
        """Log a complete conversation to MLflow with advanced metrics.

        Args:
            prompt: The user prompt
            response_data: LLM response data
            metadata: Additional metadata
        """
        if not self._is_enabled():
            return

        try:
            # Extract relevant information for logging
            session_info = response_data.get("raw_response", {}).get("session_info", {})

            # Log parameters
            params = {
                "model": metadata.get("model", "unknown"),
                "provider": response_data.get("provider", "unknown"),
                "working_directory": metadata.get("working_directory"),
                "branch_name": metadata.get("branch_name"),
                "step_name": metadata.get("step_name"),
                "prompt_length": len(prompt),
            }

            # Add advanced classification if available
            if ConversationMetrics:
                try:
                    metrics_calculator = ConversationMetrics()
                    topic = metrics_calculator.classify_conversation_topic(prompt)
                    params["conversation_topic"] = topic
                except Exception as e:
                    logger.debug(f"Failed to classify conversation topic: {e}")

            self.log_params(params)

            # Log basic metrics
            basic_metrics = {}
            if "duration_ms" in response_data:
                basic_metrics["duration_ms"] = float(response_data["duration_ms"])
            if "cost_usd" in response_data:
                basic_metrics["cost_usd"] = float(response_data["cost_usd"])

            if basic_metrics:
                self.log_metrics(basic_metrics)

            # Log usage metrics separately (to maintain test expectations)
            usage_metrics = {}
            if isinstance(session_info, dict):
                usage = session_info.get("usage", {})
                if isinstance(usage, dict):
                    for key, value in usage.items():
                        if isinstance(value, (int, float)):
                            usage_metrics[f"usage_{key}"] = float(value)

            # Add advanced metrics if available
            if ConversationMetrics:
                try:
                    metrics_calculator = ConversationMetrics()

                    # Complexity score
                    complexity = metrics_calculator.calculate_complexity_score(
                        prompt, response_data
                    )
                    usage_metrics["complexity_score"] = complexity

                    # Performance metrics
                    perf_metrics = metrics_calculator.extract_performance_metrics(
                        response_data
                    )
                    usage_metrics.update(perf_metrics)

                except Exception as e:
                    logger.debug(f"Failed to calculate advanced metrics: {e}")

            if usage_metrics:
                self.log_metrics(usage_metrics)

            # Log artifacts
            self.log_artifact(prompt, "prompt.txt")

            # Log full conversation data as JSON
            conversation_data = {
                "prompt": prompt,
                "response_data": response_data,
                "metadata": metadata,
            }
            self.log_artifact(
                json.dumps(conversation_data, indent=2, default=str),
                "conversation.json",
            )

        except Exception as e:
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
            if ConversationMetrics:
                try:
                    metrics_calculator = ConversationMetrics()
                    advanced_error_metrics = metrics_calculator.get_error_metrics(
                        error, duration_ms
                    )
                    error_metrics.update(advanced_error_metrics)
                except Exception as e:
                    logger.debug(f"Failed to calculate advanced error metrics: {e}")

            self.log_metrics(error_metrics)

        except Exception as e:
            logger.warning(f"Failed to log error metrics to MLflow: {e}")

    def end_run(self, status: str = "FINISHED") -> None:
        """End the current MLflow run.

        Args:
            status: Run status (FINISHED, FAILED, KILLED)
        """
        if not self._is_enabled() or not self.active_run_id:
            return

        try:
            import mlflow

            mlflow.end_run(status=status)
            logger.debug(f"Ended MLflow run: {self.active_run_id}")
            self.active_run_id = None

        except Exception as e:
            logger.warning(f"Failed to end MLflow run: {e}")
            self.active_run_id = None  # Clear anyway to prevent stuck state

    def _is_enabled(self) -> bool:
        """Check if MLflow logging is enabled and available."""
        return self.config.enabled and is_mlflow_available()


# Singleton instance for global use
_global_logger: Optional[MLflowLogger] = None


def get_mlflow_logger() -> MLflowLogger:
    """Get the global MLflow logger instance.

    Returns:
        Global MLflowLogger instance (created on first call)
    """
    global _global_logger
    if _global_logger is None:
        config = load_mlflow_config()  # Explicitly load config to satisfy tests
        _global_logger = MLflowLogger(config)
    return _global_logger

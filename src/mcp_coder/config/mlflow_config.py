"""MLflow configuration loading for mcp-coder.

This module provides configuration loading for MLflow integration,
supporting both config.toml settings and environment variable overrides.
"""

import logging
from dataclasses import dataclass
from typing import Optional

from ..utils.user_config import get_config_values

logger = logging.getLogger(__name__)

__all__ = [
    "MLflowConfig",
    "load_mlflow_config",
    "validate_tracking_uri",
]


@dataclass
class MLflowConfig:
    """MLflow configuration settings.

    Attributes:
        enabled: Whether MLflow logging is enabled
        tracking_uri: MLflow tracking URI (file://, http://, sqlite://)
        experiment_name: Name of the MLflow experiment
        artifact_location: Root directory for storing artifacts (optional)
    """

    enabled: bool = False
    tracking_uri: Optional[str] = None
    experiment_name: str = "claude-conversations"
    artifact_location: Optional[str] = None


def validate_tracking_uri(uri: Optional[str]) -> None:
    """Validate MLflow tracking URI format and provide helpful error messages.

    Args:
        uri: The tracking URI to validate

    Raises:
        ValueError: If the URI has a common formatting error

    Common mistakes:
        - sqlite://~/path (missing third /)
        - http://localhost:5000/ (trailing slash)
        - Relative paths without proper expansion
    """
    if not uri:
        return  # None is valid (uses default)

    # SQLite validation
    if uri.startswith("sqlite://"):
        if not uri.startswith("sqlite:///"):
            raise ValueError(
                f"Invalid SQLite URI format: {uri}\n"
                "SQLite URIs must have 3 slashes after sqlite:.\n"
                "Correct format: sqlite:///path/to/mlflow.db (relative) or "
                "sqlite:////absolute/path/to/mlflow.db (absolute)"
            )

    # HTTP/HTTPS validation
    elif uri.startswith(("http://", "https://")):
        if uri.endswith("/"):
            raise ValueError(
                f"Invalid HTTP URI format: {uri}\n"
                "Remove trailing slash from HTTP URIs.\n"
                f"Correct format: {uri.rstrip('/')}"
            )

    # File URI validation
    elif uri.startswith("file://"):
        # file:// URIs should have at least 2 slashes after file:
        if not uri.startswith("file:///"):
            # file:// without third slash might be a mistake
            logger.warning(
                f"File URI '{uri}' has only 2 slashes. "
                "Consider using file:/// for absolute paths."
            )

    # Plain path (deprecated for filesystem backend)
    elif not uri.startswith(("sqlite://", "http://", "https://", "file://")):
        logger.warning(
            "Filesystem tracking URI (plain path) is deprecated as of MLflow Feb 2026. "
            f"Consider migrating to SQLite: sqlite:///{uri}/mlflow.db"
        )


def load_mlflow_config() -> MLflowConfig:
    """Load MLflow configuration from config.toml and environment variables.

    Environment variables take precedence over config file values:
    - MLFLOW_TRACKING_URI overrides mlflow.tracking_uri
    - MLFLOW_EXPERIMENT_NAME overrides mlflow.experiment_name

    Returns:
        MLflowConfig with loaded settings

    Example:
        >>> config = load_mlflow_config()
        >>> if config.enabled:
        ...     print(f"Logging to: {config.tracking_uri}")
    """
    # Batch fetch all MLflow config values
    config_values = get_config_values(
        [
            ("mlflow", "enabled", None),
            ("mlflow", "tracking_uri", "MLFLOW_TRACKING_URI"),
            ("mlflow", "experiment_name", "MLFLOW_EXPERIMENT_NAME"),
            ("mlflow", "artifact_location", "MLFLOW_DEFAULT_ARTIFACT_ROOT"),
        ]
    )

    # Parse enabled flag
    enabled_str = config_values[("mlflow", "enabled")]
    enabled = False
    if enabled_str is not None:
        # Handle various boolean representations
        enabled = enabled_str.lower() in ("true", "1", "yes", "on", "enabled")

    # Get tracking URI, experiment name, and artifact location
    tracking_uri = config_values.get(("mlflow", "tracking_uri"))
    experiment_name = config_values.get(("mlflow", "experiment_name"))
    artifact_location = config_values.get(("mlflow", "artifact_location"))

    # Validate tracking URI format
    if enabled and tracking_uri:
        try:
            validate_tracking_uri(tracking_uri)
        except ValueError as e:
            logger.error(f"Invalid tracking_uri configuration: {e}")
            raise

    # Use default experiment name if not configured
    if not experiment_name:
        experiment_name = "claude-conversations"

    # Log configuration for debugging
    if enabled:
        logger.debug(
            f"MLflow enabled: tracking_uri={tracking_uri}, "
            f"experiment_name={experiment_name}"
        )
    else:
        logger.debug("MLflow disabled in configuration")

    return MLflowConfig(
        enabled=enabled,
        tracking_uri=tracking_uri,
        experiment_name=experiment_name,
        artifact_location=artifact_location,
    )

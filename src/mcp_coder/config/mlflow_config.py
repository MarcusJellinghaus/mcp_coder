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
]


@dataclass
class MLflowConfig:
    """MLflow configuration settings.

    Attributes:
        enabled: Whether MLflow logging is enabled
        tracking_uri: MLflow tracking URI (file://, http://, sqlite://)
        experiment_name: Name of the MLflow experiment
    """

    enabled: bool = False
    tracking_uri: Optional[str] = None
    experiment_name: str = "claude-conversations"


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
        ]
    )

    # Parse enabled flag
    enabled_str = config_values[("mlflow", "enabled")]
    enabled = False
    if enabled_str is not None:
        # Handle various boolean representations
        enabled = enabled_str.lower() in ("true", "1", "yes", "on", "enabled")

    # Get tracking URI and experiment name
    tracking_uri = config_values[("mlflow", "tracking_uri")]
    experiment_name = config_values[("mlflow", "experiment_name")]

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
    )

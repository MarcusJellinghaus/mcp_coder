"""MLflow configuration loader for mcp-coder.

This module handles loading MLflow configuration from external sources
(config files and environment variables). It's part of the infrastructure
layer and depends on the foundation layer's MLflowConfig model.

Architecture:
    - config/mlflow_config.py (foundation): Defines WHAT config is
    - utils/mlflow_config_loader.py (infrastructure): Defines HOW to load it
"""

import logging
from typing import Optional

from ..config.mlflow_config import MLflowConfig, validate_tracking_uri
from .user_config import get_config_values

logger = logging.getLogger(__name__)

__all__ = ["load_mlflow_config"]


def load_mlflow_config() -> MLflowConfig:
    """Load MLflow configuration from config.toml and environment variables.

    Environment variables take precedence over config file values:
    - MLFLOW_TRACKING_URI overrides mlflow.tracking_uri
    - MLFLOW_EXPERIMENT_NAME overrides mlflow.experiment_name

    Returns:
        MLflowConfig with loaded settings

    Raises:
        ValueError: If tracking URI format is invalid when MLflow is enabled.

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

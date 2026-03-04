"""MLflow configuration models for mcp-coder.

This module defines the MLflow configuration data structure and validation logic.
It's part of the foundation layer and has no dependencies on infrastructure.

For loading configuration from files/environment variables, see:
    utils.mlflow_config_loader.load_mlflow_config()
"""

import logging
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)

__all__ = [
    "MLflowConfig",
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

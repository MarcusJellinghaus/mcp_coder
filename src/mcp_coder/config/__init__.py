"""Configuration package for MCP Coder.

This package contains configuration files and data used by the MCP Coder system.
"""

from .mlflow_config import MLflowConfig

# Note: load_mlflow_config moved to utils.mlflow_config_loader (infrastructure layer)
# Import from mcp_coder.utils.load_mlflow_config or mcp_coder.utils.mlflow_config_loader

__all__ = [
    "MLflowConfig",
]

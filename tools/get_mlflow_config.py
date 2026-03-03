#!/usr/bin/env python3
"""Helper script to read MLflow tracking_uri from config.toml."""

import os
import sys
from pathlib import Path
from typing import Any, cast


def get_tracking_uri() -> str:
    """Get MLflow tracking URI from config.toml.

    Returns:
        Expanded tracking URI path or default if not found.
        Handles both SQLite URIs (sqlite:///...) and filesystem paths.
    """
    # Get config file path (matches mcp-coder's logic)
    config_path = Path.home() / ".mcp_coder" / "config.toml"

    if not config_path.exists():
        # Return default (SQLite recommended)
        default_path = Path.home() / "mlflow_data" / "mlflow.db"
        return f"sqlite:///{default_path}"

    try:
        # Try using tomllib (Python 3.11+) or tomli
        try:
            import tomllib

            with open(config_path, "rb") as f:
                config = tomllib.load(f)
        except ImportError:
            try:
                import tomli

                with open(config_path, "rb") as f:
                    config = tomli.load(f)
            except ImportError:
                # Fallback: simple text parsing
                return parse_tracking_uri_simple(config_path)

        # Extract tracking_uri from config
        mlflow_config: dict[str, Any] = config.get("mlflow", {})
        tracking_uri: str = cast(
            str, mlflow_config.get("tracking_uri", "sqlite:///~/mlflow_data/mlflow.db")
        )

        # Handle SQLite URIs - expand ~ in the path portion only
        if tracking_uri.startswith("sqlite:///"):
            # Extract the path after sqlite:///
            path_part = tracking_uri[len("sqlite:///") :]
            # Expand ~ and environment variables in the path
            expanded_path = os.path.expanduser(path_part)
            expanded_path = os.path.expandvars(expanded_path)
            # Convert Windows backslashes to forward slashes for SQLite URI
            expanded_path = expanded_path.replace("\\", "/")
            # Reconstruct the URI
            tracking_uri = f"sqlite:///{expanded_path}"
        else:
            # For filesystem paths, expand normally
            tracking_uri = os.path.expanduser(tracking_uri)
            tracking_uri = os.path.expandvars(tracking_uri)

        return tracking_uri

    except Exception as e:
        print(f"Warning: Could not read config.toml: {e}", file=sys.stderr)
        default_path = Path.home() / "mlflow_data" / "mlflow.db"
        return f"sqlite:///{default_path}"


def parse_tracking_uri_simple(config_path: Path) -> str:
    """Simple text-based parser for tracking_uri (fallback).

    Args:
        config_path: Path to config.toml

    Returns:
        Tracking URI or default
    """
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            in_mlflow_section = False
            for line in f:
                line = line.strip()

                # Check for [mlflow] section
                if line == "[mlflow]":
                    in_mlflow_section = True
                    continue

                # Check for another section (exit mlflow section)
                if line.startswith("[") and line != "[mlflow]":
                    in_mlflow_section = False
                    continue

                # Look for tracking_uri in mlflow section
                if in_mlflow_section and line.startswith("tracking_uri"):
                    # Extract value: tracking_uri = "value"
                    parts = line.split("=", 1)
                    if len(parts) == 2:
                        value: str = parts[1].strip().strip('"').strip("'")
                        # Handle SQLite URIs
                        if value.startswith("sqlite:///"):
                            path_part: str = value[len("sqlite:///") :]
                            expanded_path: str = os.path.expanduser(path_part)
                            # Convert Windows backslashes to forward slashes
                            expanded_path = expanded_path.replace("\\", "/")
                            return f"sqlite:///{expanded_path}"
                        else:
                            return os.path.expanduser(value)

        # Not found, return default (SQLite recommended)
        default_path = Path.home() / "mlflow_data" / "mlflow.db"
        return f"sqlite:///{default_path}"

    except Exception:
        default_path = Path.home() / "mlflow_data" / "mlflow.db"
        return f"sqlite:///{default_path}"


if __name__ == "__main__":
    tracking_uri = get_tracking_uri()
    # Ensure forward slashes for URIs (already handled in get_tracking_uri for SQLite)
    # For filesystem paths, convert backslashes
    if not tracking_uri.startswith("sqlite:"):
        tracking_uri = tracking_uri.replace("\\", "/")
    print(tracking_uri)

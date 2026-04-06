"""Project-level configuration reader for pyproject.toml.

This module reads tool configuration from pyproject.toml (project config).
For user-level configuration (API tokens, Jenkins, etc.), see user_config.py
which reads from config.toml.
"""

import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class GitHubInstallConfig:
    """Configuration for GitHub-based package installation."""

    packages: list[str]
    packages_no_deps: list[str]


def get_github_install_config(project_dir: Path) -> GitHubInstallConfig:
    """Read [tool.mcp-coder.install-from-github] from pyproject.toml.

    Args:
        project_dir: Path to directory containing pyproject.toml.

    Returns:
        GitHubInstallConfig with packages and packages_no_deps lists.
    """
    path = project_dir / "pyproject.toml"
    if not path.exists():
        return GitHubInstallConfig(packages=[], packages_no_deps=[])

    try:
        with open(path, "rb") as f:
            data = tomllib.load(f)
    except (tomllib.TOMLDecodeError, OSError):
        return GitHubInstallConfig(packages=[], packages_no_deps=[])

    gh = data.get("tool", {}).get("mcp-coder", {}).get("install-from-github", {})
    return GitHubInstallConfig(
        packages=gh.get("packages", []),
        packages_no_deps=gh.get("packages-no-deps", []),
    )


def get_formatter_config(
    project_dir: Path, filename: str = "pyproject.toml"
) -> dict[str, Any]:
    """Read [tool.black] and [tool.isort] from a TOML config file.

    Args:
        project_dir: Path to directory containing the config file.
        filename: Name of the config file (default: "pyproject.toml").

    Returns:
        Dictionary with "black" and/or "isort" keys mapping to their config dicts.
    """
    path = project_dir / filename
    if not path.exists():
        return {}

    try:
        with open(path, "rb") as f:
            data = tomllib.load(f)
    except (tomllib.TOMLDecodeError, OSError):
        return {}

    tool = data.get("tool", {})
    result: dict[str, Any] = {}
    if "black" in tool:
        result["black"] = tool["black"]
    if "isort" in tool:
        result["isort"] = tool["isort"]
    return result


def check_line_length_conflicts(config: dict[str, Any]) -> str | None:
    """Check for line-length conflicts between black and isort configurations.

    Args:
        config: Dictionary containing formatter configurations.

    Returns:
        Warning message if conflict detected, None otherwise.
    """
    black_config = config.get("black", {})
    isort_config = config.get("isort", {})

    black_length = black_config.get("line-length")
    isort_length = isort_config.get("line_length")

    if black_length is not None and isort_length is not None:
        if black_length != isort_length:
            return (
                f"Line-length conflict detected: "
                f"black line-length={black_length}, "
                f"isort line_length={isort_length}"
            )

    return None

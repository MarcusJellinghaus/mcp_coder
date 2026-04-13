"""Project-level configuration reader for pyproject.toml.

This module reads tool configuration from pyproject.toml (project config).
For user-level configuration (API tokens, Jenkins, etc.), see user_config.py
which reads from config.toml.
"""

import tomllib
from dataclasses import dataclass
from pathlib import Path


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

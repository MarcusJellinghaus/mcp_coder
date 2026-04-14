"""Project-level configuration reader for pyproject.toml.

This module reads tool configuration from pyproject.toml (project config).
For user-level configuration (API tokens, Jenkins, etc.), see user_config.py
which reads from config.toml.
"""

import tomllib
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PromptsConfig:
    """Configuration for system and project prompts."""

    system_prompt: str | None
    project_prompt: str | None
    claude_system_prompt_mode: str


@dataclass(frozen=True)
class GitHubInstallConfig:
    """Configuration for GitHub-based package installation."""

    packages: list[str]
    packages_no_deps: list[str]


def get_prompts_config(project_dir: Path) -> PromptsConfig:
    """Read [tool.mcp-coder.prompts] from pyproject.toml.

    Args:
        project_dir: Path to directory containing pyproject.toml.

    Returns:
        PromptsConfig with prompt paths and mode.
    """
    path = project_dir / "pyproject.toml"
    if not path.exists():
        return PromptsConfig(
            system_prompt=None,
            project_prompt=None,
            claude_system_prompt_mode="append",
        )

    try:
        with open(path, "rb") as f:
            data = tomllib.load(f)
    except (tomllib.TOMLDecodeError, OSError):
        return PromptsConfig(
            system_prompt=None,
            project_prompt=None,
            claude_system_prompt_mode="append",
        )

    prompts = data.get("tool", {}).get("mcp-coder", {}).get("prompts", {})
    return PromptsConfig(
        system_prompt=prompts.get("system-prompt"),
        project_prompt=prompts.get("project-prompt"),
        claude_system_prompt_mode=prompts.get("claude-system-prompt-mode", "append"),
    )


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

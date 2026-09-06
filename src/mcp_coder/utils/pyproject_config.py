"""Project-level configuration reader for pyproject.toml.

This module reads tool configuration from pyproject.toml (project config).
For user-level configuration (API tokens, Jenkins, etc.), see user_config.py
which reads from config.toml.
"""

import logging
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .toml_utils import format_toml_error

logger = logging.getLogger(__name__)

_VALID_PROMPT_MODES = {"append", "replace"}


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


def _load_pyproject(project_dir: Path, *, strict: bool = False) -> dict[str, Any]:
    """Load and parse pyproject.toml from a project directory.

    Args:
        project_dir: Path to directory containing pyproject.toml.
        strict: Raise on a malformed or unreadable file instead of
            returning an empty dict. A missing file is never an error.

    Returns:
        Parsed TOML data, or an empty dict when the file is absent (or
        malformed and strict is False).

    Raises:
        ValueError: If strict is True and the file exists but cannot be
            read or parsed. The message names the file.
    """
    path = project_dir / "pyproject.toml"
    if not path.exists():
        return {}

    try:
        with open(path, "rb") as f:
            data: dict[str, Any] = tomllib.load(f)
            return data
    except tomllib.TOMLDecodeError as e:
        if strict:
            raise ValueError(format_toml_error(path, e)) from e
        return {}
    except OSError as e:
        if strict:
            raise ValueError(f"Error reading {path}\n{e}") from e
        return {}


def get_prompts_config(project_dir: Path) -> PromptsConfig:
    """Read [tool.mcp-coder.prompts] from pyproject.toml.

    Args:
        project_dir: Path to directory containing pyproject.toml.

    Returns:
        PromptsConfig with prompt paths and mode.
    """
    data = _load_pyproject(project_dir)
    prompts = data.get("tool", {}).get("mcp-coder", {}).get("prompts", {})
    mode = prompts.get("claude-system-prompt-mode", "append")
    if mode not in _VALID_PROMPT_MODES:
        logger.warning(
            "Invalid claude-system-prompt-mode '%s' in pyproject.toml; "
            "expected 'append' or 'replace'",
            mode,
        )
    return PromptsConfig(
        system_prompt=prompts.get("system-prompt"),
        project_prompt=prompts.get("project-prompt"),
        claude_system_prompt_mode=mode,
    )


@dataclass(frozen=True)
class ImplementConfig:
    """Configuration for the implement workflow."""

    format_code: bool
    check_type_hints: bool


def get_github_install_config(project_dir: Path) -> GitHubInstallConfig:
    """Read [tool.mcp-coder.install-from-github] from pyproject.toml.

    Args:
        project_dir: Path to directory containing pyproject.toml.

    Returns:
        GitHubInstallConfig with packages and packages_no_deps lists.
    """
    data = _load_pyproject(project_dir)
    gh = data.get("tool", {}).get("mcp-coder", {}).get("install-from-github", {})
    return GitHubInstallConfig(
        packages=gh.get("packages", []),
        packages_no_deps=gh.get("packages-no-deps", []),
    )


def get_implement_config(project_dir: Path) -> ImplementConfig:
    """Read [tool.mcp-coder.implement] from pyproject.toml.

    Args:
        project_dir: Path to directory containing pyproject.toml.

    Returns:
        ImplementConfig with format_code and check_type_hints booleans.
    """
    data = _load_pyproject(project_dir)
    section = data.get("tool", {}).get("mcp-coder", {}).get("implement", {})
    return ImplementConfig(
        format_code=section.get("format_code", False),
        check_type_hints=section.get("check_type_hints", False),
    )


def get_install_extras(project_dir: Path, *, strict: bool = False) -> str | None:
    """Read [tool.mcp-coder.install] extras from pyproject.toml.

    Args:
        project_dir: Path to directory containing pyproject.toml.
        strict: Propagate the ValueError _load_pyproject raises for a
            malformed pyproject.toml instead of returning None.

    Returns:
        The declared extras string, unparsed (e.g. "dev,mlflow"), or None when
        the file, section or key is absent. An explicit empty string is
        returned as "" — the caller distinguishes it from "not declared".
    """
    data = _load_pyproject(project_dir, strict=strict)
    section = data.get("tool", {}).get("mcp-coder", {}).get("install", {})
    extras: str | None = section.get("extras")
    return extras

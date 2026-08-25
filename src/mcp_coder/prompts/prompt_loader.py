"""Prompt loading and resolution for system and project prompts.

Reads prompt configuration from pyproject.toml, resolves file paths,
and loads prompt content. Falls back to shipped defaults when no
custom configuration is provided.
"""

import logging
from pathlib import Path

from mcp_coder.utils.data_files import find_data_file
from mcp_coder.utils.pyproject_config import PromptsConfig, get_prompts_config

logger = logging.getLogger(__name__)

_PACKAGE = "mcp_coder.prompts"
_SYSTEM_PROMPT_FILE = "system-prompt.md"
_PROJECT_PROMPT_FILE = "project-prompt.md"

# Configured paths already warned about, so a long-running workflow logs
# each missing prompt path only once per process.
_warned_paths: set[str] = set()


def _read_shipped_default(filename: str) -> str:
    """Read a shipped default prompt file from the package.

    Returns:
        The prompt file content as a string.
    """
    path = find_data_file(_PACKAGE, filename)
    return path.read_text(encoding="utf-8")


def _resolve_path(configured_path: str | None, project_dir: Path | None) -> Path | None:
    """Resolve a configured prompt path to an existing file, or None.

    Absolute paths are used as-is; relative paths are resolved against
    project_dir.

    Returns:
        The Path of the existing file, or None when the path is not
        configured or does not exist.
    """
    if configured_path is None:
        return None

    path = Path(configured_path)

    if path.is_absolute():
        return path if path.exists() else None

    if project_dir is not None:
        candidate = project_dir / path
        if candidate.exists():
            return candidate

    return None


def is_prompt_configured_but_missing(
    configured_path: str | None, project_dir: Path | None
) -> bool:
    """True when a path is configured but does not resolve to an existing file.

    Returns:
        True when configured_path is set and unresolvable, False otherwise.
    """
    if configured_path is None:
        return False
    return _resolve_path(configured_path, project_dir) is None


def _resolve_and_read(
    configured_path: str | None, project_dir: Path | None
) -> str | None:
    """Resolve a configured prompt path and read its content.

    Logs a WARNING (once per path per process) when a configured path does
    not exist, then falls back to the shipped default by returning None.

    Returns:
        The file content as a string, or None if the path is not configured
        or the file doesn't exist.
    """
    if configured_path is None:
        return None

    path = _resolve_path(configured_path, project_dir)
    if path is None:
        if configured_path not in _warned_paths:
            _warned_paths.add(configured_path)
            logger.warning(
                "Configured prompt path not found: %s - using the shipped default",
                configured_path,
            )
        return None

    return path.read_text(encoding="utf-8")


def load_system_prompt(project_dir: Path | None = None) -> str:
    """Load system prompt content. Falls back to shipped default.

    Returns:
        The system prompt content as a string.
    """
    if project_dir is not None:
        config = get_prompts_config(project_dir)
        content = _resolve_and_read(config.system_prompt, project_dir)
        if content is not None:
            return content
    return _read_shipped_default(_SYSTEM_PROMPT_FILE)


def load_project_prompt(project_dir: Path | None = None) -> str:
    """Load project prompt content. Falls back to shipped default.

    Returns:
        The project prompt content as a string.
    """
    if project_dir is not None:
        config = get_prompts_config(project_dir)
        content = _resolve_and_read(config.project_prompt, project_dir)
        if content is not None:
            return content
    return _read_shipped_default(_PROJECT_PROMPT_FILE)


def load_prompts(
    project_dir: Path | None = None,
) -> tuple[str, str, PromptsConfig]:
    """Load both prompts and config. Main entry point.

    Returns:
        Tuple of (system_prompt, project_prompt, config).
    """
    if project_dir is not None:
        config = get_prompts_config(project_dir)
    else:
        config = PromptsConfig(
            system_prompt=None,
            project_prompt=None,
            claude_system_prompt_mode="append",
        )

    system_content = _resolve_and_read(config.system_prompt, project_dir)
    if system_content is None:
        system_content = _read_shipped_default(_SYSTEM_PROMPT_FILE)

    project_content = _resolve_and_read(config.project_prompt, project_dir)
    if project_content is None:
        project_content = _read_shipped_default(_PROJECT_PROMPT_FILE)

    return system_content, project_content, config


def get_project_prompt_path(project_dir: Path | None = None) -> Path | None:
    """Resolve the project prompt file path (for redundancy detection).

    Returns:
        The resolved Path to the project prompt file, or None when using
        the shipped default.
    """
    if project_dir is None:
        return None

    config = get_prompts_config(project_dir)
    return _resolve_path(config.project_prompt, project_dir)


def claude_md_paths(directory: Path) -> list[Path]:
    """Return the CLAUDE.md candidate paths Claude Code looks for in one directory.

    Not existence-checked - these are candidates, not hits. The order is
    presentational only and must not be treated as a precedence rule.

    Returns:
        [<directory>/CLAUDE.md, <directory>/.claude/CLAUDE.md]
    """
    return [directory / "CLAUDE.md", directory / ".claude" / "CLAUDE.md"]


def is_claude_md(project_prompt_path: Path | None, project_dir: str | None) -> bool:
    """Check if project_prompt points to any known CLAUDE.md location.

    Checks root-level, .claude/ dir, and parent directories up to filesystem root.

    Returns:
        True if the project prompt path resolves to a CLAUDE.md file.
    """
    if project_prompt_path is None or project_dir is None:
        return False

    try:
        resolved = project_prompt_path.resolve()
        project = Path(project_dir).resolve()

        # Check current project dir and all parent directories
        current = project
        while True:
            for candidate in claude_md_paths(current):
                if resolved == candidate.resolve():
                    return True

            parent = current.parent
            if parent == current:
                break
            current = parent
    except OSError:
        return False

    return False

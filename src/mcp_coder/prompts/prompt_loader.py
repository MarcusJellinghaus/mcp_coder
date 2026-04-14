"""Prompt loading and resolution for system and project prompts.

Reads prompt configuration from pyproject.toml, resolves file paths,
and loads prompt content. Falls back to shipped defaults when no
custom configuration is provided.
"""

from pathlib import Path

from mcp_coder.utils.data_files import find_data_file
from mcp_coder.utils.pyproject_config import PromptsConfig, get_prompts_config

_PACKAGE = "mcp_coder.prompts"
_SYSTEM_PROMPT_FILE = "system-prompt.md"
_PROJECT_PROMPT_FILE = "project-prompt.md"


def _read_shipped_default(filename: str) -> str:
    """Read a shipped default prompt file from the package.

    Returns:
        The prompt file content as a string.
    """
    path = find_data_file(_PACKAGE, filename)
    return path.read_text(encoding="utf-8")


def _resolve_and_read(
    configured_path: str | None, project_dir: Path | None
) -> str | None:
    """Resolve a configured prompt path and read its content.

    Returns:
        The file content as a string, or None if the path is not configured
        or the file doesn't exist.
    """
    if configured_path is None:
        return None

    path = Path(configured_path)

    if path.is_absolute():
        if path.exists():
            return path.read_text(encoding="utf-8")
        return None

    if project_dir is not None:
        candidate = project_dir / path
        if candidate.exists():
            return candidate.read_text(encoding="utf-8")

    return None


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
    if config.project_prompt is None:
        return None

    path = Path(config.project_prompt)

    if path.is_absolute():
        return path if path.exists() else None

    candidate = project_dir / path
    return candidate if candidate.exists() else None


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
            # Root-level CLAUDE.md
            if resolved == (current / "CLAUDE.md").resolve():
                return True
            # .claude/CLAUDE.md
            if resolved == (current / ".claude" / "CLAUDE.md").resolve():
                return True

            parent = current.parent
            if parent == current:
                break
            current = parent
    except OSError:
        return False

    return False

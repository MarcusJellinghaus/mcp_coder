"""Tests for prompt_loader module."""

import logging
from pathlib import Path
from unittest.mock import patch

import pytest

from mcp_coder.prompts.prompt_loader import (
    get_project_prompt_path,
    is_claude_md,
    load_project_prompt,
    load_prompts,
    load_system_prompt,
)
from mcp_coder.utils.pyproject_config import get_prompts_config


def test_load_prompts_defaults() -> None:
    """No project_dir → returns shipped defaults (non-empty strings)."""
    system, project, config = load_prompts()
    assert isinstance(system, str)
    assert len(system) > 0
    assert isinstance(project, str)
    assert len(project) > 0
    assert config.system_prompt is None
    assert config.project_prompt is None
    assert config.claude_system_prompt_mode == "append"


def test_load_prompts_no_pyproject(tmp_path: Path) -> None:
    """project_dir exists but no pyproject.toml → shipped defaults."""
    system, project, config = load_prompts(tmp_path)
    assert len(system) > 0
    assert len(project) > 0
    assert config.system_prompt is None
    assert config.project_prompt is None


def test_load_prompts_empty_section(tmp_path: Path) -> None:
    """pyproject.toml exists but no [tool.mcp-coder.prompts] → shipped defaults."""
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text("[tool.mcp-coder]\n", encoding="utf-8")
    system, project, config = load_prompts(tmp_path)
    assert len(system) > 0
    assert len(project) > 0
    assert config.system_prompt is None


def test_load_prompts_custom_system_prompt(tmp_path: Path) -> None:
    """Configured system prompt path resolves correctly."""
    custom = tmp_path / "my-system.md"
    custom.write_text("Custom system prompt", encoding="utf-8")
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        '[tool.mcp-coder.prompts]\nsystem-prompt = "my-system.md"\n',
        encoding="utf-8",
    )
    system, project, config = load_prompts(tmp_path)
    assert system == "Custom system prompt"
    assert len(project) > 0  # falls back to default
    assert config.system_prompt == "my-system.md"


def test_load_prompts_custom_project_prompt(tmp_path: Path) -> None:
    """Configured project prompt path resolves correctly."""
    custom = tmp_path / "my-project.md"
    custom.write_text("Custom project prompt", encoding="utf-8")
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        '[tool.mcp-coder.prompts]\nproject-prompt = "my-project.md"\n',
        encoding="utf-8",
    )
    system, project, config = load_prompts(tmp_path)
    assert len(system) > 0  # falls back to default
    assert project == "Custom project prompt"
    assert config.project_prompt == "my-project.md"


def test_load_prompts_absolute_path(tmp_path: Path) -> None:
    """Absolute path works."""
    custom = tmp_path / "abs-prompt.md"
    custom.write_text("Absolute path prompt", encoding="utf-8")
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        f'[tool.mcp-coder.prompts]\nsystem-prompt = "{custom.as_posix()}"\n',
        encoding="utf-8",
    )
    system, _, _ = load_prompts(tmp_path)
    assert system == "Absolute path prompt"


def test_load_prompts_missing_file_falls_back(tmp_path: Path) -> None:
    """Configured path doesn't exist → shipped default."""
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        '[tool.mcp-coder.prompts]\nsystem-prompt = "nonexistent.md"\n',
        encoding="utf-8",
    )
    system, _, _ = load_prompts(tmp_path)
    assert len(system) > 0
    # Should be the shipped default, not empty


def test_get_prompts_config_defaults(tmp_path: Path) -> None:
    """Missing config returns all-None/default-mode."""
    config = get_prompts_config(tmp_path)
    assert config.system_prompt is None
    assert config.project_prompt is None
    assert config.claude_system_prompt_mode == "append"


def test_get_prompts_config_replace_mode(tmp_path: Path) -> None:
    """claude-system-prompt-mode = 'replace' is parsed correctly."""
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        '[tool.mcp-coder.prompts]\nclaude-system-prompt-mode = "replace"\n',
        encoding="utf-8",
    )
    config = get_prompts_config(tmp_path)
    assert config.claude_system_prompt_mode == "replace"


def test_get_project_prompt_path_default() -> None:
    """Returns None for shipped default (no project_dir)."""
    result = get_project_prompt_path()
    assert result is None


def test_get_project_prompt_path_custom(tmp_path: Path) -> None:
    """Returns resolved Path for custom prompt."""
    custom = tmp_path / "my-project.md"
    custom.write_text("content", encoding="utf-8")
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        '[tool.mcp-coder.prompts]\nproject-prompt = "my-project.md"\n',
        encoding="utf-8",
    )
    result = get_project_prompt_path(tmp_path)
    assert result is not None
    assert result == tmp_path / "my-project.md"


def test_shipped_defaults_exist() -> None:
    """system-prompt.md and project-prompt.md are non-empty and loadable."""
    system = load_system_prompt()
    project = load_project_prompt()
    assert len(system) > 0
    assert "System Prompt" in system or "system" in system.lower()
    assert len(project) > 0
    assert "Project" in project or "project" in project.lower()


def test_is_claude_md_root_level(tmp_path: Path) -> None:
    """Detects root-level CLAUDE.md."""
    claude_md = tmp_path / "CLAUDE.md"
    claude_md.write_text("instructions", encoding="utf-8")
    assert is_claude_md(claude_md, str(tmp_path)) is True


def test_is_claude_md_dot_claude_dir(tmp_path: Path) -> None:
    """Detects .claude/CLAUDE.md."""
    claude_dir = tmp_path / ".claude"
    claude_dir.mkdir()
    claude_md = claude_dir / "CLAUDE.md"
    claude_md.write_text("instructions", encoding="utf-8")
    assert is_claude_md(claude_md, str(tmp_path)) is True


def test_is_claude_md_unrelated_file(tmp_path: Path) -> None:
    """Non-CLAUDE.md file returns False."""
    other = tmp_path / "other.md"
    other.write_text("other", encoding="utf-8")
    assert is_claude_md(other, str(tmp_path)) is False


def test_is_claude_md_none_inputs() -> None:
    """None inputs return False."""
    assert is_claude_md(None, None) is False
    assert is_claude_md(None, "/some/path") is False
    assert is_claude_md(Path("/some/file"), None) is False


def test_is_claude_md_oserror_returns_false() -> None:
    """OSError during resolve() returns False instead of raising."""
    bad_path = Path("/some/broken/symlink")
    with patch.object(Path, "resolve", side_effect=OSError("broken symlink")):
        assert is_claude_md(bad_path, "/some/project") is False


def test_get_prompts_config_warns_on_invalid_mode(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """Invalid claude-system-prompt-mode logs a warning."""
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        '[tool.mcp-coder.prompts]\nclaude-system-prompt-mode = "prepend"\n',
        encoding="utf-8",
    )
    with caplog.at_level(logging.WARNING, logger="mcp_coder.utils.pyproject_config"):
        config = get_prompts_config(tmp_path)
    assert config.claude_system_prompt_mode == "prepend"
    assert "Invalid claude-system-prompt-mode 'prepend'" in caplog.text

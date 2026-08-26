"""Tests for prompt_loader module."""

import logging
from collections.abc import Iterator
from pathlib import Path
from unittest.mock import patch

import pytest

from mcp_coder.constants import PROMPTS_FILE_PATH
from mcp_coder.prompt_manager import get_prompt
from mcp_coder.prompts import prompt_loader
from mcp_coder.prompts.prompt_loader import (
    get_project_prompt_path,
    is_claude_md,
    is_prompt_configured_but_missing,
    load_project_prompt,
    load_prompts,
    load_system_prompt,
)
from mcp_coder.utils.pyproject_config import get_prompts_config

_LOADER_LOGGER = "mcp_coder.prompts.prompt_loader"


@pytest.fixture(autouse=True)
def _clear_prompt_warning_cache() -> Iterator[None]:
    """Isolate the module-level warn-once cache from test ordering."""
    prompt_loader._warned_paths.clear()
    yield
    prompt_loader._warned_paths.clear()


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


def _loader_warnings(caplog: pytest.LogCaptureFixture) -> list[logging.LogRecord]:
    """Collect WARNING records emitted by the prompt loader.

    Returns:
        The matching log records, in emission order.
    """
    return [
        record
        for record in caplog.records
        if record.name == _LOADER_LOGGER and record.levelno == logging.WARNING
    ]


def _write_prompts_config(tmp_path: Path, body: str) -> None:
    """Write a [tool.mcp-coder.prompts] section into tmp_path/pyproject.toml."""
    (tmp_path / "pyproject.toml").write_text(
        f"[tool.mcp-coder.prompts]\n{body}",
        encoding="utf-8",
    )


def test_existing_configured_prompt_logs_no_warning(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """A configured path that exists is used and logs nothing."""
    custom = tmp_path / "my-system.md"
    custom.write_text("Custom system prompt", encoding="utf-8")
    _write_prompts_config(tmp_path, 'system-prompt = "my-system.md"\n')

    with caplog.at_level(logging.WARNING, logger=_LOADER_LOGGER):
        system, _, _ = load_prompts(tmp_path)

    assert system == "Custom system prompt"
    assert _loader_warnings(caplog) == []


def test_missing_configured_prompt_warns_and_falls_back(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """A missing configured path warns once and still returns the default."""
    _write_prompts_config(tmp_path, 'system-prompt = "nonexistent.md"\n')

    with caplog.at_level(logging.WARNING, logger=_LOADER_LOGGER):
        system, _, _ = load_prompts(tmp_path)

    assert len(system) > 0
    warnings = _loader_warnings(caplog)
    assert len(warnings) == 1
    assert "nonexistent.md" in warnings[0].getMessage()


def test_missing_configured_prompt_warns_only_once_per_path(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """Reading the same missing path twice still logs exactly one WARNING."""
    _write_prompts_config(tmp_path, 'system-prompt = "nonexistent.md"\n')

    with caplog.at_level(logging.WARNING, logger=_LOADER_LOGGER):
        load_prompts(tmp_path)
        load_prompts(tmp_path)

    assert len(_loader_warnings(caplog)) == 1


def test_two_missing_paths_warn_separately(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """Distinct missing paths each get their own WARNING."""
    _write_prompts_config(
        tmp_path,
        'system-prompt = "missing-system.md"\nproject-prompt = "missing-project.md"\n',
    )

    with caplog.at_level(logging.WARNING, logger=_LOADER_LOGGER):
        load_prompts(tmp_path)

    messages = [record.getMessage() for record in _loader_warnings(caplog)]
    assert len(messages) == 2
    assert any("missing-system.md" in message for message in messages)
    assert any("missing-project.md" in message for message in messages)


def test_load_system_prompt_absolute_missing_path_warns(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """An absolute configured path that does not exist warns and falls back."""
    missing = tmp_path / "absent" / "system.md"
    _write_prompts_config(tmp_path, f'system-prompt = "{missing.as_posix()}"\n')

    with caplog.at_level(logging.WARNING, logger=_LOADER_LOGGER):
        system = load_system_prompt(tmp_path)

    assert len(system) > 0
    assert len(_loader_warnings(caplog)) == 1


def test_load_project_prompt_relative_path_resolves(tmp_path: Path) -> None:
    """A project-relative configured path resolves through the shared resolver."""
    nested = tmp_path / "docs"
    nested.mkdir()
    (nested / "project.md").write_text("Relative project prompt", encoding="utf-8")
    _write_prompts_config(tmp_path, 'project-prompt = "docs/project.md"\n')

    assert load_project_prompt(tmp_path) == "Relative project prompt"


def test_get_project_prompt_path_missing_file(tmp_path: Path) -> None:
    """Configured-but-missing project prompt still resolves to None."""
    _write_prompts_config(tmp_path, 'project-prompt = "nonexistent.md"\n')
    assert get_project_prompt_path(tmp_path) is None


def test_get_project_prompt_path_absolute(tmp_path: Path) -> None:
    """An absolute configured project prompt resolves to that Path."""
    custom = tmp_path / "abs-project.md"
    custom.write_text("content", encoding="utf-8")
    _write_prompts_config(tmp_path, f'project-prompt = "{custom.as_posix()}"\n')

    assert get_project_prompt_path(tmp_path) == custom


def test_get_project_prompt_path_unconfigured(tmp_path: Path) -> None:
    """No configured project prompt returns None even with a project_dir."""
    assert get_project_prompt_path(tmp_path) is None


def test_is_prompt_configured_but_missing_unconfigured() -> None:
    """No configured path is never 'missing'."""
    assert is_prompt_configured_but_missing(None, None) is False
    assert is_prompt_configured_but_missing(None, Path("/some/project")) is False


def test_is_prompt_configured_but_missing_relative(tmp_path: Path) -> None:
    """A relative path is missing when absent and present when it exists."""
    assert is_prompt_configured_but_missing("prompt.md", tmp_path) is True

    (tmp_path / "prompt.md").write_text("content", encoding="utf-8")
    assert is_prompt_configured_but_missing("prompt.md", tmp_path) is False


def test_is_prompt_configured_but_missing_absolute(tmp_path: Path) -> None:
    """An absolute path is checked directly, regardless of project_dir."""
    custom = tmp_path / "abs.md"
    assert is_prompt_configured_but_missing(custom.as_posix(), None) is True

    custom.write_text("content", encoding="utf-8")
    assert is_prompt_configured_but_missing(custom.as_posix(), None) is False


def test_is_prompt_configured_but_missing_does_not_warn(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """The predicate is silent - only the read path warns."""
    with caplog.at_level(logging.WARNING, logger=_LOADER_LOGGER):
        assert is_prompt_configured_but_missing("nonexistent.md", tmp_path) is True

    assert _loader_warnings(caplog) == []


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


def test_review_reviewer_sections_load() -> None:
    """Both reviewer sections load as non-empty prompts."""
    impl_reviewer = get_prompt(str(PROMPTS_FILE_PATH), "Review Implementation Reviewer")
    plan_reviewer = get_prompt(str(PROMPTS_FILE_PATH), "Review Plan Reviewer")
    assert len(impl_reviewer.strip()) > 0
    assert len(plan_reviewer.strip()) > 0


def test_review_supervisor_section_loads() -> None:
    """The shared supervisor section loads as a non-empty prompt."""
    supervisor = get_prompt(str(PROMPTS_FILE_PATH), "Review Supervisor")
    assert len(supervisor.strip()) > 0


def test_review_reviewer_sections_contain_issue_number_placeholder() -> None:
    """Both reviewer prompts carry the {issue_number} substitution placeholder."""
    impl_reviewer = get_prompt(str(PROMPTS_FILE_PATH), "Review Implementation Reviewer")
    plan_reviewer = get_prompt(str(PROMPTS_FILE_PATH), "Review Plan Reviewer")
    assert "{issue_number}" in impl_reviewer
    assert "{issue_number}" in plan_reviewer


def test_review_implementation_reviewer_contains_base_branch_placeholder() -> None:
    """The implementation reviewer prompt carries the {base_branch} placeholder."""
    impl_reviewer = get_prompt(str(PROMPTS_FILE_PATH), "Review Implementation Reviewer")
    assert "{base_branch}" in impl_reviewer


def test_review_supervisor_declares_json_decision_contract() -> None:
    """The supervisor prompt documents the fenced-JSON verdict contract."""
    supervisor = get_prompt(str(PROMPTS_FILE_PATH), "Review Supervisor")
    assert "dismiss" in supervisor
    assert "tasks" in supervisor
    assert "escalate" in supervisor

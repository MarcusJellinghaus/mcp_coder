"""Unit tests for the least-privilege rebase permissions and settings file."""

import json
from pathlib import Path

import pytest

from mcp_coder.workflows.rebase_permissions import (
    REBASE_LLM_PERMISSIONS,
    rebase_settings_file,
)


def test_allow_list_is_non_empty_list() -> None:
    """The permissions.allow entry must be a non-empty list."""
    allow = REBASE_LLM_PERMISSIONS["permissions"]["allow"]
    assert isinstance(allow, list)
    assert len(allow) > 0


def test_allow_list_has_no_bash_grants() -> None:
    """Non-interactive sessions load no Bash tool, so Bash grants are dead."""
    allow = REBASE_LLM_PERMISSIONS["permissions"]["allow"]
    assert all(not entry.startswith("Bash(") for entry in allow)


def test_allow_list_contains_mcp_tools() -> None:
    """The MCP git/file/check tools the session actually uses stay granted."""
    allow = REBASE_LLM_PERMISSIONS["permissions"]["allow"]
    for entry in (
        "mcp__mcp-workspace__git",
        "mcp__mcp-workspace__get_base_branch",
        "mcp__mcp-workspace__read_file",
        "mcp__mcp-workspace__save_file",
        "mcp__mcp-workspace__edit_file",
        "mcp__mcp-workspace__delete_this_file",
        "mcp__mcp-tools-py__run_format_code",
        "mcp__mcp-tools-py__run_pylint_check",
        "mcp__mcp-tools-py__run_pytest_check",
        "mcp__mcp-tools-py__run_mypy_check",
    ):
        assert entry in allow


def test_allow_list_excludes_reference_project_tools() -> None:
    """Least privilege: no reference-project tools are granted."""
    allow = REBASE_LLM_PERMISSIONS["permissions"]["allow"]
    assert all("reference" not in entry for entry in allow)


def test_allow_list_excludes_push() -> None:
    """Python performs the force-push; the LLM gets no push grant."""
    allow = REBASE_LLM_PERMISSIONS["permissions"]["allow"]
    assert all("push" not in entry for entry in allow)


def test_allow_list_excludes_uv_lock() -> None:
    """Lockfile handling is out of scope for this repo."""
    allow = REBASE_LLM_PERMISSIONS["permissions"]["allow"]
    assert all("uv lock" not in entry for entry in allow)


def test_allow_list_excludes_move_file() -> None:
    """Conflict resolution edits in place; no move_file grant."""
    allow = REBASE_LLM_PERMISSIONS["permissions"]["allow"]
    assert "mcp__mcp-workspace__move_file" not in allow


class TestRebaseSettingsFile:
    """Test the rebase_settings_file context manager."""

    def test_default_temp_file_exists_inside_block_and_is_removed(self) -> None:
        """The temp file holds the constant inside the block and is gone after."""
        with rebase_settings_file() as path:
            settings_path = Path(path)
            assert settings_path.is_absolute()
            assert settings_path.suffix == ".json"
            assert settings_path.exists()
            with settings_path.open(encoding="utf-8") as handle:
                assert json.load(handle) == REBASE_LLM_PERMISSIONS

        assert not settings_path.exists()

    def test_temp_file_removed_when_body_raises(self) -> None:
        """The temp file is deleted even if the with-body raises."""
        captured: list[Path] = []
        with pytest.raises(RuntimeError, match="boom"):
            with rebase_settings_file() as path:
                captured.append(Path(path))
                raise RuntimeError("boom")

        assert len(captured) == 1
        assert not captured[0].exists()

    def test_override_yielded_unchanged_and_not_deleted(self, tmp_path: Path) -> None:
        """An override path is passed through and left in place."""
        override = tmp_path / "custom.json"
        override.write_text("{}", encoding="utf-8")

        with rebase_settings_file(str(override)) as path:
            assert path == str(override)

        assert override.exists()

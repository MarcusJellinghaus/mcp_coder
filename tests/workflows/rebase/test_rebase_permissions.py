"""Unit tests for the least-privilege rebase settings and settings file."""

import json
from collections.abc import Iterator
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.workflows.rebase_permissions import (
    rebase_settings,
    rebase_settings_file,
)

_PATCH_PERMS = "mcp_coder.workflows.rebase_permissions.llm_permissions"

_PYTHON_PERMS = [
    "mcp__mcp-tools-py__run_pylint_check",
    "mcp__mcp-tools-py__run_pytest_check",
    "mcp__mcp-tools-py__run_mypy_check",
]
_COMMAND_PERMS = ["Bash(npm test)", "Bash(npm run lint)"]


@pytest.fixture(name="python_perms")
def fixture_python_perms() -> Iterator[MagicMock]:
    """Patch ``llm_permissions`` with a Python-style toolkit's grants."""
    with patch(_PATCH_PERMS, return_value=list(_PYTHON_PERMS)) as mock_perms:
        yield mock_perms


@pytest.fixture(name="command_perms")
def fixture_command_perms() -> Iterator[MagicMock]:
    """Patch ``llm_permissions`` with a ``command``-style toolkit's grants."""
    with patch(_PATCH_PERMS, return_value=list(_COMMAND_PERMS)) as mock_perms:
        yield mock_perms


def _allow(settings: dict[str, object]) -> list[str]:
    permissions = settings["permissions"]
    assert isinstance(permissions, dict)
    allow = permissions["allow"]
    assert isinstance(allow, list)
    return allow


@pytest.mark.usefixtures("python_perms")
class TestRebaseSettingsPython:
    """A Python-style toolkit contributes its MCP check tools."""

    def test_toolkit_check_tools_allowed(self, tmp_path: Path) -> None:
        """The toolkit's non-Bash grants are in the allowlist."""
        allow = _allow(rebase_settings(tmp_path, "rebase"))
        for entry in _PYTHON_PERMS:
            assert entry in allow

    def test_workspace_tools_allowed(self, tmp_path: Path) -> None:
        """The fixed mcp-workspace git/file tools stay granted."""
        allow = _allow(rebase_settings(tmp_path, "rebase"))
        for entry in (
            "mcp__mcp-workspace__git",
            "mcp__mcp-workspace__get_base_branch",
            "mcp__mcp-workspace__read_file",
            "mcp__mcp-workspace__save_file",
            "mcp__mcp-workspace__edit_file",
            "mcp__mcp-workspace__delete_this_file",
        ):
            assert entry in allow

    def test_no_run_format_code(self, tmp_path: Path) -> None:
        """Formatting runs after each fix turn; the LLM gets no format grant."""
        allow = _allow(rebase_settings(tmp_path, "rebase"))
        assert "mcp__mcp-tools-py__run_format_code" not in allow

    def test_servers_derived_from_prefixes(self, tmp_path: Path) -> None:
        """enabledMcpjsonServers lists mcp-workspace plus the toolkit's servers."""
        settings = rebase_settings(tmp_path, "rebase")
        assert settings["enabledMcpjsonServers"] == ["mcp-workspace", "mcp-tools-py"]
        assert settings["enableAllProjectMcpServers"] is True

    def test_no_duplicates(self, tmp_path: Path) -> None:
        """Each permission appears once."""
        allow = _allow(rebase_settings(tmp_path, "rebase"))
        assert len(allow) == len(set(allow))

    def test_excludes_reference_push_uv_lock_move_file(self, tmp_path: Path) -> None:
        """Least privilege: no reference, push, uv lock or move_file grants."""
        allow = _allow(rebase_settings(tmp_path, "rebase"))
        assert all("reference" not in entry for entry in allow)
        assert all("push" not in entry for entry in allow)
        assert all("uv lock" not in entry for entry in allow)
        assert "mcp__mcp-workspace__move_file" not in allow


@pytest.mark.usefixtures("command_perms")
class TestRebaseSettingsCommand:
    """A ``command``-style toolkit has only Bash grants."""

    def test_allow_list_has_no_bash_grants(self, tmp_path: Path) -> None:
        """Bash grants reach fix turns via --allowedTools, not the settings."""
        allow = _allow(rebase_settings(tmp_path, "rebase_automated"))
        assert all(not entry.startswith("Bash(") for entry in allow)
        assert all("mcp-tools-py" not in entry for entry in allow)
        assert "mcp__mcp-workspace__git" in allow

    def test_servers_workspace_only(self, tmp_path: Path) -> None:
        """Only mcp-workspace is enabled."""
        settings = rebase_settings(tmp_path, "rebase_automated")
        assert settings["enabledMcpjsonServers"] == ["mcp-workspace"]


@pytest.mark.parametrize("entry", ["rebase", "rebase_automated"])
def test_entry_forwarded_with_claude_provider(
    tmp_path: Path, python_perms: MagicMock, entry: str
) -> None:
    """The binding entry is forwarded to llm_permissions with provider claude."""
    rebase_settings(tmp_path, entry)
    python_perms.assert_called_once_with(tmp_path, "claude", entry)


class TestRebaseSettingsFile:
    """Test the rebase_settings_file context manager."""

    @pytest.mark.usefixtures("python_perms")
    def test_default_temp_file_exists_inside_block_and_is_removed(
        self, tmp_path: Path
    ) -> None:
        """The temp file holds the generated settings and is gone after."""
        expected = rebase_settings(tmp_path, "rebase")
        with rebase_settings_file(tmp_path, "rebase") as path:
            settings_path = Path(path)
            assert settings_path.is_absolute()
            assert settings_path.suffix == ".json"
            assert settings_path.exists()
            with settings_path.open(encoding="utf-8") as handle:
                assert json.load(handle) == expected

        assert not settings_path.exists()

    @pytest.mark.usefixtures("python_perms")
    def test_temp_file_removed_when_body_raises(self, tmp_path: Path) -> None:
        """The temp file is deleted even if the with-body raises."""
        captured: list[Path] = []
        with pytest.raises(RuntimeError, match="boom"):
            with rebase_settings_file(tmp_path, "rebase_automated") as path:
                captured.append(Path(path))
                raise RuntimeError("boom")

        assert len(captured) == 1
        assert not captured[0].exists()

    def test_override_yielded_unchanged_and_not_deleted(self, tmp_path: Path) -> None:
        """An override path is passed through, left in place, no toolkit read."""
        override = tmp_path / "custom.json"
        override.write_text("{}", encoding="utf-8")

        with patch(_PATCH_PERMS) as mock_perms:
            with rebase_settings_file(tmp_path, "rebase", str(override)) as path:
                assert path == str(override)

        mock_perms.assert_not_called()
        assert override.exists()

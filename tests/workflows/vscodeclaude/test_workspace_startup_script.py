"""Test startup script generation for VSCode Claude workspace.

The startup script is now a thin launcher that bootstraps into
``session_setup``; all orchestration lives in the serialized ``SessionSpec``
(``.vscodeclaude_session.json``) written alongside it. These tests therefore
assert on the launcher filename/mode/error paths and on the written spec
(via ``read_session_spec`` + the ``session_setup`` argv builders), not on any
generated shell orchestration (which no longer exists).
"""

import stat
import sys
from pathlib import Path
from typing import Any

import pytest

from mcp_coder.workflows.vscodeclaude.session_setup import (
    build_claude_argv,
    build_step_argv,
)
from mcp_coder.workflows.vscodeclaude.types import read_session_spec
from mcp_coder.workflows.vscodeclaude.workspace import create_startup_script


def _seed_mcp_config(tmp_path: Path, system: str) -> None:
    """Write the platform-appropriate MCP config file into tmp_path."""
    filenames = {
        "Windows": ".mcp.json",
        "Darwin": ".mcp.macos.json",
        "Linux": ".mcp.linux.json",
    }
    (tmp_path / filenames[system]).write_text("{}", encoding="utf-8")


class TestCreateStartupScript:
    """Windows launcher + spec generation."""

    def test_returns_bat_filename(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        mock_vscodeclaude_config: None,
    ) -> None:
        """Windows produces a .vscodeclaude_start.bat launcher."""
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.workspace.platform.system",
            lambda: "Windows",
        )

        script_path = create_startup_script(
            folder_path=tmp_path,
            issue_number=123,
            issue_title="Test issue",
            status="status-07:code-review",
            repo_name="test-repo",
            issue_url="https://github.com/test/repo/issues/123",
            is_intervention=False,
        )

        assert script_path.name == ".vscodeclaude_start.bat"

    def test_writes_session_spec_alongside_launcher(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        mock_vscodeclaude_config: None,
    ) -> None:
        """A .vscodeclaude_session.json spec is written next to the launcher."""
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.workspace.platform.system",
            lambda: "Windows",
        )

        create_startup_script(
            folder_path=tmp_path,
            issue_number=123,
            issue_title="Test issue",
            status="status-07:code-review",
            repo_name="test-repo",
            issue_url="https://github.com/test/repo/issues/123",
            is_intervention=False,
        )

        assert (tmp_path / ".vscodeclaude_session.json").exists()
        spec = read_session_spec(tmp_path)
        assert spec.issue_number == 123
        assert spec.title == "Test issue"
        assert spec.repo == "test-repo"
        assert spec.status == "status-07:code-review"
        assert spec.mcp_config == ".mcp.json"
        assert spec.is_intervention is False

    def test_single_command_spec(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        mock_vscodeclaude_config: None,
    ) -> None:
        """Single-command status records exactly one command in the spec."""
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.workspace.platform.system",
            lambda: "Windows",
        )

        create_startup_script(
            folder_path=tmp_path,
            issue_number=123,
            issue_title="Test issue",
            status="status-07:code-review",
            repo_name="test-repo",
            issue_url="https://github.com/test/repo/issues/123",
            is_intervention=False,
        )

        spec = read_session_spec(tmp_path)
        assert spec.commands == ["/implementation_review_supervisor"]
        # The single interactive claude launch carries the command + issue.
        argv = build_claude_argv(spec, prompt=f"{spec.commands[0]} {spec.issue_number}")
        assert "/implementation_review_supervisor 123" in argv

    def test_multi_command_spec(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        mock_vscodeclaude_config: None,
    ) -> None:
        """Multi-command status records every command in order in the spec."""
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.workspace.platform.system",
            lambda: "Windows",
        )

        # status-01:created has commands=["/issue_analyse", "/discuss"]
        create_startup_script(
            folder_path=tmp_path,
            issue_number=123,
            issue_title="Test issue",
            status="status-01:created",
            repo_name="test-repo",
            issue_url="https://github.com/test/repo/issues/123",
            is_intervention=False,
        )

        spec = read_session_spec(tmp_path)
        assert spec.commands == ["/issue_analyse", "/discuss"]
        # First step is automated with session-id capture.
        first = build_step_argv(
            spec, spec.commands[0], session_id=None, issue_number=spec.issue_number
        )
        assert "--output-format" in first
        assert "/issue_analyse 123" in first

    def test_custom_timeout_recorded_in_spec(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        mock_vscodeclaude_config: None,
    ) -> None:
        """Timeout parameter is stored in the spec."""
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.workspace.platform.system",
            lambda: "Windows",
        )

        create_startup_script(
            folder_path=tmp_path,
            issue_number=123,
            issue_title="Test issue",
            status="status-01:created",
            repo_name="test-repo",
            issue_url="https://github.com/test/repo/issues/123",
            is_intervention=False,
            timeout=600,
        )

        assert read_session_spec(tmp_path).timeout == 600

    def test_intervention_spec_flag(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        mock_vscodeclaude_config: None,
    ) -> None:
        """Intervention mode sets is_intervention on the spec."""
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.workspace.platform.system",
            lambda: "Windows",
        )

        create_startup_script(
            folder_path=tmp_path,
            issue_number=123,
            issue_title="Test issue",
            status="status-06:implementing",
            repo_name="test-repo",
            issue_url="https://github.com/test/repo/issues/123",
            is_intervention=True,
        )

        assert read_session_spec(tmp_path).is_intervention is True

    def test_empty_commands_spec(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Config with empty commands list records an empty commands spec."""
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.workspace.platform.system",
            lambda: "Windows",
        )

        empty_cmd_configs: dict[str, dict[str, Any]] = {
            "status-empty": {
                "emoji": "\U0001f4cb",
                "display_name": "EMPTY",
                "stage_short": "emp",
                "commands": [],
            },
        }
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.workspace.get_vscodeclaude_config",
            empty_cmd_configs.get,
        )

        create_startup_script(
            folder_path=tmp_path,
            issue_number=1,
            issue_title="Empty test",
            status="status-empty",
            repo_name="test-repo",
            issue_url="https://github.com/test/repo/issues/1",
            is_intervention=False,
        )

        assert read_session_spec(tmp_path).commands == []

    def test_three_command_spec(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Three-command config records all three commands in order."""
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.workspace.platform.system",
            lambda: "Windows",
        )

        three_cmd_configs: dict[str, dict[str, Any]] = {
            "status-triple": {
                "emoji": "\U0001f527",
                "display_name": "TRIPLE",
                "stage_short": "tri",
                "commands": ["/step_one", "/step_two", "/step_three"],
            },
        }
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.workspace.get_vscodeclaude_config",
            three_cmd_configs.get,
        )

        create_startup_script(
            folder_path=tmp_path,
            issue_number=99,
            issue_title="Triple test",
            status="status-triple",
            repo_name="test-repo",
            issue_url="https://github.com/test/repo/issues/99",
            is_intervention=False,
        )

        assert read_session_spec(tmp_path).commands == [
            "/step_one",
            "/step_two",
            "/step_three",
        ]

    def test_invalid_commands_type_raises_error(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Config with non-list commands raises ValueError."""
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.workspace.platform.system",
            lambda: "Windows",
        )

        bad_configs: dict[str, dict[str, Any]] = {
            "status-bad": {
                "emoji": "\U0001f4cb",
                "display_name": "BAD",
                "stage_short": "bad",
                "commands": "/single_string",
            },
        }
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.workspace.get_vscodeclaude_config",
            bad_configs.get,
        )

        with pytest.raises(ValueError, match="Invalid commands config"):
            create_startup_script(
                folder_path=tmp_path,
                issue_number=1,
                issue_title="Bad test",
                status="status-bad",
                repo_name="test-repo",
                issue_url="https://github.com/test/repo/issues/1",
                is_intervention=False,
            )

    def test_invalid_commands_element_raises_error(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Config with non-string elements in commands raises ValueError."""
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.workspace.platform.system",
            lambda: "Windows",
        )

        bad_configs: dict[str, dict[str, Any]] = {
            "status-bad": {
                "emoji": "\U0001f4cb",
                "display_name": "BAD",
                "stage_short": "bad",
                "commands": ["/valid", 123],
            },
        }
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.workspace.get_vscodeclaude_config",
            bad_configs.get,
        )

        with pytest.raises(ValueError, match="Invalid commands config"):
            create_startup_script(
                folder_path=tmp_path,
                issue_number=1,
                issue_title="Bad test",
                status="status-bad",
                repo_name="test-repo",
                issue_url="https://github.com/test/repo/issues/1",
                is_intervention=False,
            )

    def test_unresolved_install_path_raises_runtimeerror(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        mock_vscodeclaude_config: None,
    ) -> None:
        """When the mcp-coder install path can't be found, RuntimeError is raised."""
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.workspace.platform.system",
            lambda: "Windows",
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.workspace.get_mcp_coder_install_path",
            lambda: None,
        )

        with pytest.raises(RuntimeError, match="install path could not be determined"):
            create_startup_script(
                folder_path=tmp_path,
                issue_number=1,
                issue_title="Test",
                status="status-07:code-review",
                repo_name="test-repo",
                issue_url="https://github.com/test/repo/issues/1",
                is_intervention=False,
            )


class TestCreateStartupScriptPOSIX:
    """POSIX-specific tests for launcher + spec generation (Darwin / Linux)."""

    @pytest.mark.parametrize("system", ["Darwin", "Linux"])
    def test_filename_is_sh(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        mock_vscodeclaude_config: None,
        system: str,
    ) -> None:
        """POSIX produces .vscodeclaude_start.sh."""
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.workspace.platform.system",
            lambda: system,
        )
        _seed_mcp_config(tmp_path, system)

        script_path = create_startup_script(
            folder_path=tmp_path,
            issue_number=123,
            issue_title="Test issue",
            status="status-07:code-review",
            repo_name="test-repo",
            issue_url="https://github.com/test/repo/issues/123",
            is_intervention=False,
        )

        assert script_path.name == ".vscodeclaude_start.sh"

    @pytest.mark.parametrize("system", ["Darwin", "Linux"])
    def test_shebang_is_bash(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        mock_vscodeclaude_config: None,
        system: str,
    ) -> None:
        """First line of the POSIX launcher is the bash shebang."""
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.workspace.platform.system",
            lambda: system,
        )
        _seed_mcp_config(tmp_path, system)

        script_path = create_startup_script(
            folder_path=tmp_path,
            issue_number=1,
            issue_title="Test",
            status="status-07:code-review",
            repo_name="test-repo",
            issue_url="https://github.com/test/repo/issues/1",
            is_intervention=False,
        )

        content = script_path.read_text(encoding="utf-8")
        assert content.splitlines()[0] == "#!/usr/bin/env bash"

    @pytest.mark.parametrize(
        "system,expected_mcp_config",
        [
            ("Darwin", ".mcp.macos.json"),
            ("Linux", ".mcp.linux.json"),
        ],
    )
    def test_spec_mcp_config_per_platform(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        mock_vscodeclaude_config: None,
        system: str,
        expected_mcp_config: str,
    ) -> None:
        """The spec carries the platform-specific MCP config filename."""
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.workspace.platform.system",
            lambda: system,
        )
        _seed_mcp_config(tmp_path, system)

        create_startup_script(
            folder_path=tmp_path,
            issue_number=123,
            issue_title="Test issue",
            status="status-01:created",
            repo_name="test-repo",
            issue_url="https://github.com/test/repo/issues/123",
            is_intervention=False,
        )

        assert read_session_spec(tmp_path).mcp_config == expected_mcp_config

    @pytest.mark.skipif(
        sys.platform == "win32",
        reason="Windows ignores chmod(0o755) for the executable bit on regular files",
    )
    @pytest.mark.parametrize("system", ["Darwin", "Linux"])
    def test_executable_bit_set(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        mock_vscodeclaude_config: None,
        system: str,
    ) -> None:
        """Generated POSIX launcher has the user-executable bit set."""
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.workspace.platform.system",
            lambda: system,
        )
        _seed_mcp_config(tmp_path, system)

        script_path = create_startup_script(
            folder_path=tmp_path,
            issue_number=1,
            issue_title="Test",
            status="status-07:code-review",
            repo_name="test-repo",
            issue_url="https://github.com/test/repo/issues/1",
            is_intervention=False,
        )

        assert script_path.stat().st_mode & stat.S_IXUSR

    def test_missing_mcp_config_raises_filenotfound_darwin(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        mock_vscodeclaude_config: None,
    ) -> None:
        """Darwin without .mcp.macos.json raises FileNotFoundError naming the file."""
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.workspace.platform.system",
            lambda: "Darwin",
        )
        # Deliberately do NOT create .mcp.macos.json

        with pytest.raises(FileNotFoundError, match=r"\.mcp\.macos\.json"):
            create_startup_script(
                folder_path=tmp_path,
                issue_number=1,
                issue_title="Test",
                status="status-07:code-review",
                repo_name="test-repo",
                issue_url="https://github.com/test/repo/issues/1",
                is_intervention=False,
            )

    @pytest.mark.parametrize("system", ["Darwin", "Linux"])
    def test_intervention_spec_posix(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        mock_vscodeclaude_config: None,
        system: str,
    ) -> None:
        """Intervention mode on POSIX writes an .sh launcher and flags the spec."""
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.workspace.platform.system",
            lambda: system,
        )
        _seed_mcp_config(tmp_path, system)

        script_path = create_startup_script(
            folder_path=tmp_path,
            issue_number=1,
            issue_title="Test",
            status="status-06:implementing",
            repo_name="test-repo",
            issue_url="https://github.com/test/repo/issues/1",
            is_intervention=True,
        )

        assert script_path.name == ".vscodeclaude_start.sh"
        assert read_session_spec(tmp_path).is_intervention is True


class TestMcpConfigFlagsFullMatrix:
    """Every generated ``claude`` launch must carry the MCP config flags.

    Without ``--mcp-config <file> --strict-mcp-config``, Claude falls back to
    default ``.mcp.json`` discovery, which is Windows-only (issue #965). The
    flags are now produced by ``build_claude_argv`` from the spec's
    ``mcp_config`` field, so the matrix asserts on that argv.
    """

    @pytest.mark.parametrize(
        "system,expected_mcp_config",
        [
            ("Windows", ".mcp.json"),
            ("Darwin", ".mcp.macos.json"),
            ("Linux", ".mcp.linux.json"),
        ],
    )
    def test_single_command_has_flags(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        mock_vscodeclaude_config: None,
        system: str,
        expected_mcp_config: str,
    ) -> None:
        """Single-command spec yields a claude argv with the flag pair."""
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.workspace.platform.system",
            lambda: system,
        )
        _seed_mcp_config(tmp_path, system)

        create_startup_script(
            folder_path=tmp_path,
            issue_number=123,
            issue_title="Test",
            status="status-07:code-review",
            repo_name="test-repo",
            issue_url="https://github.com/test/repo/issues/123",
            is_intervention=False,
        )

        spec = read_session_spec(tmp_path)
        argv = build_claude_argv(spec, prompt="/x 123")
        assert "--mcp-config" in argv
        assert expected_mcp_config in argv
        assert "--strict-mcp-config" in argv

    @pytest.mark.parametrize(
        "system,expected_mcp_config",
        [
            ("Windows", ".mcp.json"),
            ("Darwin", ".mcp.macos.json"),
            ("Linux", ".mcp.linux.json"),
        ],
    )
    def test_intervention_has_flags(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        mock_vscodeclaude_config: None,
        system: str,
        expected_mcp_config: str,
    ) -> None:
        """Intervention spec yields a bare claude argv with the flag pair."""
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.workspace.platform.system",
            lambda: system,
        )
        _seed_mcp_config(tmp_path, system)

        create_startup_script(
            folder_path=tmp_path,
            issue_number=1,
            issue_title="Test",
            status="status-06:implementing",
            repo_name="test-repo",
            issue_url="https://github.com/test/repo/issues/1",
            is_intervention=True,
        )

        spec = read_session_spec(tmp_path)
        argv = build_claude_argv(spec)
        assert "--mcp-config" in argv
        assert expected_mcp_config in argv
        assert "--strict-mcp-config" in argv

"""Tests for cross-platform MCP server binary verification."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from mcp_coder.utils.mcp_verification import (
    MCP_SERVER_NAMES,
    ClaudeMCPStatus,
    MCPServerInfo,
    _exe_name,
    get_bin_dir,
    parse_claude_mcp_list,
    verify_mcp_servers,
)
from mcp_coder.utils.subprocess_runner import CommandResult


class TestGetBinDir:
    """Tests for get_bin_dir()."""

    @pytest.mark.parametrize(
        ("platform", "expected_subdir"),
        [
            ("win32", "Scripts"),
            ("linux", "bin"),
            ("darwin", "bin"),
        ],
    )
    def test_get_bin_dir(
        self,
        monkeypatch: pytest.MonkeyPatch,
        platform: str,
        expected_subdir: str,
    ) -> None:
        monkeypatch.setattr(sys, "platform", platform)
        result = get_bin_dir("/some/venv")
        assert result == Path("/some/venv") / expected_subdir


class TestExeName:
    """Tests for _exe_name()."""

    @pytest.mark.parametrize(
        ("platform", "expected_suffix"),
        [
            ("win32", "tool.exe"),
            ("linux", "tool"),
            ("darwin", "tool"),
        ],
    )
    def test_exe_name(
        self,
        monkeypatch: pytest.MonkeyPatch,
        platform: str,
        expected_suffix: str,
    ) -> None:
        monkeypatch.setattr(sys, "platform", platform)
        assert _exe_name("tool") == expected_suffix


class TestVerifyMcpServers:
    """Tests for verify_mcp_servers()."""

    def _create_fake_executables(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> Path:
        """Create fake executables in a temporary bin dir."""
        monkeypatch.setattr(sys, "platform", "linux")
        bin_dir = tmp_path / "bin"
        bin_dir.mkdir()
        for name in MCP_SERVER_NAMES:
            (bin_dir / name).touch()
        return bin_dir

    def _patch_runner(
        self, monkeypatch: pytest.MonkeyPatch, result: CommandResult
    ) -> None:
        monkeypatch.setattr(
            "mcp_coder.utils.mcp_verification.execute_command",
            lambda *_a, **_kw: result,
        )

    def test_verify_mcp_servers_success(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        self._create_fake_executables(tmp_path, monkeypatch)
        self._patch_runner(
            monkeypatch,
            CommandResult(return_code=0, stdout="1.0.0\n", stderr="", timed_out=False),
        )

        results = verify_mcp_servers(tmp_path)

        assert len(results) == len(MCP_SERVER_NAMES)
        for info in results:
            assert isinstance(info, MCPServerInfo)
            assert info.version == "1.0.0"
            assert info.name in MCP_SERVER_NAMES

    def test_verify_mcp_servers_missing_binary(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(sys, "platform", "linux")
        bin_dir = tmp_path / "bin"
        bin_dir.mkdir()

        with pytest.raises(FileNotFoundError, match="not found in"):
            verify_mcp_servers(tmp_path)

    def test_verify_mcp_servers_version_capture(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        self._create_fake_executables(tmp_path, monkeypatch)
        self._patch_runner(
            monkeypatch,
            CommandResult(return_code=0, stdout="2.3.1\n", stderr="", timed_out=False),
        )

        results = verify_mcp_servers(tmp_path)

        assert results[0].version == "2.3.1"

    def test_verify_mcp_servers_passes_30s_timeout(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        self._create_fake_executables(tmp_path, monkeypatch)
        captured_kwargs: dict[str, object] = {}

        def _capture(*_a: object, **kwargs: object) -> CommandResult:
            captured_kwargs.update(kwargs)
            return CommandResult(
                return_code=0, stdout="1.0.0\n", stderr="", timed_out=False
            )

        monkeypatch.setattr(
            "mcp_coder.utils.mcp_verification.execute_command", _capture
        )
        verify_mcp_servers(tmp_path)
        assert captured_kwargs.get("timeout_seconds") == 30

    @pytest.mark.parametrize(
        ("result", "match"),
        [
            pytest.param(
                CommandResult(
                    return_code=1,
                    stdout="",
                    stderr="",
                    timed_out=True,
                    execution_error="Process timed out after 30 seconds",
                ),
                "timed out after 30s",
                id="timeout",
            ),
            pytest.param(
                CommandResult(
                    return_code=1,
                    stdout="",
                    stderr="",
                    timed_out=False,
                    execution_error="OSError: permission denied",
                ),
                "Failed to invoke",
                id="launch_error",
            ),
            pytest.param(
                CommandResult(
                    return_code=1, stdout="", stderr="error occurred", timed_out=False
                ),
                "exited with code 1",
                id="nonzero_exit",
            ),
        ],
    )
    def test_verify_mcp_servers_version_failure_raises(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        result: CommandResult,
        match: str,
    ) -> None:
        self._create_fake_executables(tmp_path, monkeypatch)
        self._patch_runner(monkeypatch, result)
        with pytest.raises(RuntimeError, match=match):
            verify_mcp_servers(tmp_path)


# --- Sample claude mcp list output ---
_SAMPLE_OUTPUT = """\
Checking MCP server health...

claude.ai Gmail: https://gmail.mcp.claude.com/mcp - ! Needs authentication
mcp-tools-py: C:\\venv\\Scripts\\mcp-tools-py.exe --project-dir . - ✓ Connected
mcp-workspace: C:\\venv\\Scripts\\mcp-workspace.exe --project-dir . - ✓ Connected
"""

_SAMPLE_OUTPUT_MIXED = """\
Checking MCP server health...

mcp-tools-py: C:\\venv\\Scripts\\mcp-tools-py.exe --project-dir . - ✓ Connected
mcp-workspace: C:\\venv\\Scripts\\mcp-workspace.exe --project-dir . - ✗ Failed to start
"""


class TestClaudeMCPStatus:
    """Tests for ClaudeMCPStatus dataclass."""

    def test_claude_mcp_status_fields(self) -> None:
        status = ClaudeMCPStatus(name="mcp-tools-py", status_text="Connected", ok=True)
        assert status.name == "mcp-tools-py"
        assert status.status_text == "Connected"
        assert status.ok is True

        # Verify frozen
        with pytest.raises(AttributeError):
            status.name = "other"  # type: ignore[misc]

    def test_claude_mcp_status_ok_true_when_connected(self) -> None:
        status = ClaudeMCPStatus(name="mcp-tools-py", status_text="Connected", ok=True)
        assert status.ok is True

    def test_claude_mcp_status_ok_false_when_not_connected(self) -> None:
        status = ClaudeMCPStatus(
            name="mcp-tools-py", status_text="Failed to start", ok=False
        )
        assert status.ok is False


class TestParseClaudeMcpList:
    """Tests for parse_claude_mcp_list()."""

    def _make_result(
        self,
        stdout: str = "",
        return_code: int = 0,
        timed_out: bool = False,
    ) -> CommandResult:
        return CommandResult(
            return_code=return_code,
            stdout=stdout,
            stderr="",
            timed_out=timed_out,
        )

    def test_parses_connected_servers(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            "mcp_coder.utils.mcp_verification.execute_command",
            lambda *_a, **_kw: self._make_result(stdout=_SAMPLE_OUTPUT),
        )

        result = parse_claude_mcp_list(
            env_vars={"PATH": "/usr/bin"}, claude_executable="/usr/bin/claude"
        )

        assert result is not None
        assert len(result) == 2
        assert all(s.ok for s in result)
        names = {s.name for s in result}
        assert names == {"mcp-tools-py", "mcp-workspace"}

    def test_parses_failed_server(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            "mcp_coder.utils.mcp_verification.execute_command",
            lambda *_a, **_kw: self._make_result(stdout=_SAMPLE_OUTPUT_MIXED),
        )

        result = parse_claude_mcp_list(
            env_vars={"PATH": "/usr/bin"}, claude_executable="/usr/bin/claude"
        )

        assert result is not None
        by_name = {s.name: s for s in result}
        assert by_name["mcp-tools-py"].ok is True
        assert by_name["mcp-workspace"].ok is False
        assert by_name["mcp-workspace"].status_text == "Failed to start"

    def test_filters_to_known_servers_only(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            "mcp_coder.utils.mcp_verification.execute_command",
            lambda *_a, **_kw: self._make_result(stdout=_SAMPLE_OUTPUT),
        )

        result = parse_claude_mcp_list(env_vars={}, claude_executable="/usr/bin/claude")

        assert result is not None
        names = {s.name for s in result}
        assert names == {"mcp-tools-py", "mcp-workspace"}

    def test_returns_none_when_claude_not_found(self) -> None:
        result = parse_claude_mcp_list(env_vars={}, claude_executable=None)

        assert result is None

    def test_returns_none_on_nonzero_exit(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            "mcp_coder.utils.mcp_verification.execute_command",
            lambda *_a, **_kw: self._make_result(return_code=1),
        )

        result = parse_claude_mcp_list(env_vars={}, claude_executable="/usr/bin/claude")

        assert result is None

    def test_returns_none_on_timeout(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            "mcp_coder.utils.mcp_verification.execute_command",
            lambda *_a, **_kw: self._make_result(timed_out=True),
        )

        result = parse_claude_mcp_list(env_vars={}, claude_executable="/usr/bin/claude")

        assert result is None

    def test_returns_none_on_exception(self, monkeypatch: pytest.MonkeyPatch) -> None:
        def _raise(*_a: object, **_kw: object) -> None:
            raise OSError("boom")

        monkeypatch.setattr(
            "mcp_coder.utils.mcp_verification.execute_command",
            _raise,
        )

        result = parse_claude_mcp_list(env_vars={}, claude_executable="/usr/bin/claude")

        assert result is None

    def test_skips_preamble_and_empty_lines(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        output = "Checking MCP server health...\n\n\n"
        monkeypatch.setattr(
            "mcp_coder.utils.mcp_verification.execute_command",
            lambda *_a, **_kw: self._make_result(stdout=output),
        )

        result = parse_claude_mcp_list(env_vars={}, claude_executable="/usr/bin/claude")

        assert result is not None
        assert len(result) == 0

    def test_unparseable_lines_skipped_gracefully(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        output = "some garbage\n!!!\nmcp-tools-py: /exe - ✓ Connected\n"
        monkeypatch.setattr(
            "mcp_coder.utils.mcp_verification.execute_command",
            lambda *_a, **_kw: self._make_result(stdout=output),
        )

        result = parse_claude_mcp_list(env_vars={}, claude_executable="/usr/bin/claude")

        assert result is not None
        assert len(result) == 1
        assert result[0].name == "mcp-tools-py"

    def test_env_vars_passed_to_subprocess(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        captured_kwargs: dict[str, object] = {}

        def _capture(*_a: object, **kwargs: object) -> CommandResult:
            captured_kwargs.update(kwargs)
            return self._make_result(stdout="")

        monkeypatch.setattr(
            "mcp_coder.utils.mcp_verification.execute_command",
            _capture,
        )

        env = {"MY_VAR": "hello"}
        parse_claude_mcp_list(env_vars=env, claude_executable="/usr/bin/claude")

        assert captured_kwargs.get("env") == env

    def test_mcp_config_path_in_command(self, monkeypatch: pytest.MonkeyPatch) -> None:
        captured_args: list[object] = []

        def _capture(*args: object, **_kw: object) -> CommandResult:
            captured_args.extend(args)
            return self._make_result(stdout="")

        monkeypatch.setattr(
            "mcp_coder.utils.mcp_verification.execute_command",
            _capture,
        )

        parse_claude_mcp_list(
            env_vars={},
            mcp_config_path="custom.json",
            claude_executable="/usr/bin/claude",
        )

        # First arg is the command list
        command = captured_args[0]
        assert isinstance(command, list)
        assert "--mcp-config" in command
        idx = command.index("--mcp-config")
        assert command[idx + 1] == "custom.json"

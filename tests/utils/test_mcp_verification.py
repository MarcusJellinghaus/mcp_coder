"""Tests for cross-platform MCP server binary verification."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from mcp_coder.utils.mcp_verification import (
    MCP_SERVER_NAMES,
    MCPServerInfo,
    _exe_name,
    get_bin_dir,
    verify_mcp_servers,
)


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

    def test_verify_mcp_servers_success(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        self._create_fake_executables(tmp_path, monkeypatch)

        fake_proc = MagicMock()
        fake_proc.returncode = 0
        fake_proc.stdout = "1.0.0\n"
        fake_proc.stderr = ""
        monkeypatch.setattr(subprocess, "run", lambda *_a, **_kw: fake_proc)

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

        fake_proc = MagicMock()
        fake_proc.returncode = 0
        fake_proc.stdout = "2.3.1\n"
        fake_proc.stderr = ""
        monkeypatch.setattr(subprocess, "run", lambda *_a, **_kw: fake_proc)

        results = verify_mcp_servers(tmp_path)

        assert results[0].version == "2.3.1"

    def test_verify_mcp_servers_version_nonzero_raises(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        self._create_fake_executables(tmp_path, monkeypatch)

        fake_proc = MagicMock()
        fake_proc.returncode = 1
        fake_proc.stdout = ""
        fake_proc.stderr = "error occurred"
        monkeypatch.setattr(subprocess, "run", lambda *_a, **_kw: fake_proc)

        with pytest.raises(RuntimeError, match="exited with code 1"):
            verify_mcp_servers(tmp_path)

    def test_verify_mcp_servers_subprocess_oserror_raises(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        self._create_fake_executables(tmp_path, monkeypatch)

        def _raise_oserror(*_a: object, **_kw: object) -> None:
            raise OSError("permission denied")

        monkeypatch.setattr(subprocess, "run", _raise_oserror)

        with pytest.raises(RuntimeError, match="Failed to invoke"):
            verify_mcp_servers(tmp_path)

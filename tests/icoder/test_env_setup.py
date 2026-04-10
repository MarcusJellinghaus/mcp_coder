"""Tests for icoder/env_setup.py — RuntimeInfo + environment setup."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import pytest

from mcp_coder.icoder.env_setup import RuntimeInfo, setup_icoder_environment
from mcp_coder.utils.mcp_verification import MCPServerInfo


@pytest.fixture()
def _clear_mcp_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Remove all MCP_CODER_* env vars for test isolation."""
    for key in ("MCP_CODER_VENV_PATH", "MCP_CODER_VENV_DIR", "MCP_CODER_PROJECT_DIR"):
        monkeypatch.delenv(key, raising=False)


@pytest.fixture()
def fake_venv(tmp_path: Path) -> Path:
    """Create a fake venv with bin/Scripts dir and fake MCP binaries."""
    venv_root = tmp_path / "tool_env"
    subdir = "Scripts" if sys.platform == "win32" else "bin"
    bin_dir = venv_root / subdir
    bin_dir.mkdir(parents=True)
    # Create fake MCP server binaries
    ext = ".exe" if sys.platform == "win32" else ""
    for name in ("mcp-tools-py", "mcp-workspace"):
        (bin_dir / f"{name}{ext}").touch()
    return venv_root


_FAKE_MCP_SERVERS = [
    MCPServerInfo(name="mcp-tools-py", path=Path("/fake/mcp-tools-py"), version="1.0"),
    MCPServerInfo(
        name="mcp-workspace", path=Path("/fake/mcp-workspace"), version="2.0"
    ),
]


@pytest.fixture()
def _mock_externals(
    monkeypatch: pytest.MonkeyPatch,
    fake_venv: Path,
) -> None:
    """Mock prepare_llm_environment, verify_mcp_servers, metadata.version, and claude."""
    subdir = "Scripts" if sys.platform == "win32" else "bin"
    bin_dir = fake_venv / subdir
    monkeypatch.setattr(
        "mcp_coder.icoder.env_setup.prepare_llm_environment",
        lambda project_dir: {
            "MCP_CODER_VENV_PATH": str(bin_dir),
            "MCP_CODER_VENV_DIR": str(fake_venv),
            "MCP_CODER_PROJECT_DIR": str(project_dir),
        },
    )
    monkeypatch.setattr(
        "mcp_coder.icoder.env_setup.verify_mcp_servers",
        lambda _root: _FAKE_MCP_SERVERS,
    )
    monkeypatch.setattr(
        "mcp_coder.icoder.env_setup.importlib.metadata.version",
        lambda _pkg: "0.42.0",
    )
    monkeypatch.setattr(
        "mcp_coder.icoder.env_setup._get_claude_code_version",
        lambda: "1.2.3",
    )


@pytest.mark.usefixtures("_clear_mcp_env", "_mock_externals")
class TestSetupIcoderEnvironment:
    """Tests for setup_icoder_environment()."""

    def test_setup_returns_runtime_info(self, tmp_path: Path) -> None:
        """Verify all RuntimeInfo fields are populated."""
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        (project_dir / ".venv").mkdir()

        info = setup_icoder_environment(project_dir)

        assert isinstance(info, RuntimeInfo)
        assert info.mcp_coder_version == "0.42.0"
        assert (
            info.python_version
            == f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        )
        assert info.claude_code_version == "1.2.3"
        assert info.project_dir == str(project_dir)
        assert info.mcp_servers == _FAKE_MCP_SERVERS
        assert "MCP_CODER_VENV_PATH" in info.env_vars
        assert "MCP_CODER_VENV_DIR" in info.env_vars
        assert "MCP_CODER_PROJECT_DIR" in info.env_vars

    def test_tool_env_uses_detected_venv(self, tmp_path: Path, fake_venv: Path) -> None:
        """tool_env_path should equal the detected venv from prepare_llm_environment."""
        project_dir = tmp_path / "project"
        project_dir.mkdir()

        info = setup_icoder_environment(project_dir)

        assert info.tool_env_path == str(fake_venv)

    def test_project_venv_found(self, tmp_path: Path) -> None:
        """When project_dir/.venv exists, project_venv_path points to it."""
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        venv_dir = project_dir / ".venv"
        venv_dir.mkdir()

        info = setup_icoder_environment(project_dir)

        assert info.project_venv_path == str(venv_dir)

    def test_project_venv_fallback(
        self, tmp_path: Path, fake_venv: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """No .venv → fallback to sys.prefix with INFO log."""
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        # No .venv created

        with caplog.at_level(logging.INFO, logger="mcp_coder.icoder.env_setup"):
            info = setup_icoder_environment(project_dir)

        assert info.project_venv_path == str(fake_venv)
        assert any("No project .venv found" in msg for msg in caplog.messages)

    def test_env_vars_always_contain_all_three_keys(self, tmp_path: Path) -> None:
        """With no pre-set vars, all three MCP_CODER_* keys present."""
        project_dir = tmp_path / "project"
        project_dir.mkdir()

        info = setup_icoder_environment(project_dir)

        expected_keys = {
            "MCP_CODER_VENV_PATH",
            "MCP_CODER_VENV_DIR",
            "MCP_CODER_PROJECT_DIR",
        }
        assert expected_keys == set(info.env_vars.keys())

    def test_mcp_servers_verified(self, tmp_path: Path) -> None:
        """mcp_servers in RuntimeInfo comes from verify_mcp_servers."""
        project_dir = tmp_path / "project"
        project_dir.mkdir()

        info = setup_icoder_environment(project_dir)

        assert info.mcp_servers == _FAKE_MCP_SERVERS
        assert len(info.mcp_servers) == 2

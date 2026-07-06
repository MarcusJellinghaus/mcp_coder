"""Test that the session spec separates the mcp-coder install dir from the CWD.

Historically the generated .bat baked shell logic that could confuse the
mcp-coder executable location with the session folder (via
``MCP_CODER_PROJECT_DIR``). The launcher is now a one-liner and the session
directory is the runtime ``%CD%``/``$PWD``; the only path the launcher carries
is the coordinator's ``mcp_coder_install_path``. These tests pin that the spec
records the install dir explicitly and that it points at a real ``install.py``
under that dir — not at the session folder.
"""

from pathlib import Path

import pytest

from mcp_coder.workflows.vscodeclaude.session_setup import build_install_argv
from mcp_coder.workflows.vscodeclaude.types import read_session_spec
from mcp_coder.workflows.vscodeclaude.workspace import create_startup_script


class TestStartupScriptMCPCoderPath:
    """The spec carries the coordinator install dir distinct from the CWD."""

    def test_spec_records_explicit_install_path(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        mock_vscodeclaude_config: None,
    ) -> None:
        """An explicit mcp_coder_install_path is stored on the spec verbatim."""
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.workspace.platform.system",
            lambda: "Windows",
        )

        install_dir = tmp_path / "mcp-coder-install"
        (install_dir / "tools").mkdir(parents=True)
        (install_dir / "tools" / "install.py").write_text("", encoding="utf-8")

        session_folder = tmp_path / "session_folder"
        session_folder.mkdir()

        create_startup_script(
            folder_path=session_folder,
            issue_number=123,
            issue_title="Test Issue",
            status="status-01:created",
            repo_name="test-repo",
            issue_url="https://github.com/owner/repo/issues/123",
            is_intervention=False,
            timeout=30,
            mcp_coder_install_path=install_dir,
        )

        spec = read_session_spec(session_folder)
        # The install dir is stored explicitly and is NOT the session folder.
        assert spec.mcp_coder_install_path == str(install_dir)
        assert spec.mcp_coder_install_path != str(session_folder)

    def test_install_argv_points_at_install_dir_not_session_folder(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        mock_vscodeclaude_config: None,
    ) -> None:
        """install.py argv resolves under the install dir, with the CWD as target."""
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.workspace.platform.system",
            lambda: "Windows",
        )

        install_dir = tmp_path / "mcp-coder-install"
        (install_dir / "tools").mkdir(parents=True)
        (install_dir / "tools" / "install.py").write_text("", encoding="utf-8")

        session_folder = tmp_path / "mcp_session_123"
        session_folder.mkdir()

        create_startup_script(
            folder_path=session_folder,
            issue_number=123,
            issue_title="Test Issue",
            status="status-01:created",
            repo_name="test-repo",
            issue_url="https://github.com/owner/repo/issues/123",
            is_intervention=False,
            timeout=30,
            mcp_coder_install_path=install_dir,
        )

        spec = read_session_spec(session_folder)
        argv = build_install_argv(spec, session_folder)

        # The install script itself lives under the install dir.
        assert spec.install_script_path == str(install_dir / "tools" / "install.py")
        # The install target (positional + --local-path) is the session CWD.
        assert str(session_folder) in argv

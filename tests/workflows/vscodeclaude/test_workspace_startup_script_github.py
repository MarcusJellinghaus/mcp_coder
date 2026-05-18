"""Test how create_startup_script propagates skip_github_install.

GitHub override semantics themselves (which packages, --refresh, no-deps,
etc.) live inside ``tools/install.py`` and are covered by that script's
own tests + the ``vscodeclaude-template-install`` CI job. Here we only
verify that the vscodeclaude template **delegates** to the install
script and threads the user-facing ``--no-install-from-github`` flag
through as ``--skip-overrides``.
"""

from pathlib import Path

import pytest

from mcp_coder.workflows.vscodeclaude.workspace import create_startup_script


def _write_mcp_config(tmp_path: Path, system: str) -> None:
    """Drop the mcp_config file POSIX create_startup_script requires."""
    name = ".mcp.linux.json" if system == "Linux" else ".mcp.macos.json"
    (tmp_path / name).write_text("{}", encoding="utf-8")


class TestInstallEnvDelegationWindows:
    """Windows-side template delegation contract."""

    def test_default_calls_install_env_without_skip_overrides(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        mock_vscodeclaude_config: None,
    ) -> None:
        """Without skip_github_install, install-env is called with overrides on."""
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.workspace.platform.system",
            lambda: "Windows",
        )

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
        assert "install.py" in content
        assert "--source local" in content
        assert "--use-sync" in content
        assert "--skip-overrides" not in content

    def test_skip_github_install_adds_skip_overrides_flag(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        mock_vscodeclaude_config: None,
    ) -> None:
        """skip_github_install=True appends --skip-overrides to install-env call."""
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.workspace.platform.system",
            lambda: "Windows",
        )

        script_path = create_startup_script(
            folder_path=tmp_path,
            issue_number=1,
            issue_title="Test",
            status="status-07:code-review",
            repo_name="test-repo",
            issue_url="https://github.com/test/repo/issues/1",
            is_intervention=False,
            skip_github_install=True,
        )

        content = script_path.read_text(encoding="utf-8")
        assert "install.py" in content
        assert "--source local" in content
        assert "--skip-overrides" in content


class TestInstallEnvDelegationPosix:
    """POSIX-side template delegation contract (parity with Windows)."""

    @pytest.mark.parametrize("system", ["Darwin", "Linux"])
    def test_default_calls_install_env_without_skip_overrides(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        mock_vscodeclaude_config: None,
        system: str,
    ) -> None:
        """Without skip_github_install, install-env is called with overrides on."""
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.workspace.platform.system",
            lambda: system,
        )
        _write_mcp_config(tmp_path, system)

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
        assert "install.py" in content
        assert "--source local" in content
        assert "--use-sync" in content
        assert "--skip-overrides" not in content

    @pytest.mark.parametrize("system", ["Darwin", "Linux"])
    def test_skip_github_install_adds_skip_overrides_flag(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        mock_vscodeclaude_config: None,
        system: str,
    ) -> None:
        """skip_github_install=True appends --skip-overrides on POSIX too."""
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.workspace.platform.system",
            lambda: system,
        )
        _write_mcp_config(tmp_path, system)

        script_path = create_startup_script(
            folder_path=tmp_path,
            issue_number=1,
            issue_title="Test",
            status="status-07:code-review",
            repo_name="test-repo",
            issue_url="https://github.com/test/repo/issues/1",
            is_intervention=False,
            skip_github_install=True,
        )

        content = script_path.read_text(encoding="utf-8")
        assert "install.py" in content
        assert "--source local" in content
        assert "--skip-overrides" in content

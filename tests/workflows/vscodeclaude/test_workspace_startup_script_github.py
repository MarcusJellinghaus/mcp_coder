"""Test how create_startup_script propagates skip_github_install.

GitHub override semantics themselves (which packages, --refresh, no-deps,
etc.) live inside ``tools/install.py`` and are covered by that script's
own tests + the ``vscodeclaude-template-install`` CI job. Here we only
verify that ``create_startup_script`` records the user-facing
``--no-install-from-github`` flag on the spec and that
``session_setup.build_install_argv`` threads it through as
``--skip-overrides``.
"""

from pathlib import Path

import pytest

from mcp_coder.workflows.vscodeclaude.session_setup import build_install_argv
from mcp_coder.workflows.vscodeclaude.types import read_session_spec
from mcp_coder.workflows.vscodeclaude.workspace import create_startup_script


def _write_mcp_config(tmp_path: Path, system: str) -> None:
    """Drop the mcp_config file POSIX create_startup_script requires."""
    name = ".mcp.linux.json" if system == "Linux" else ".mcp.macos.json"
    (tmp_path / name).write_text("{}", encoding="utf-8")


class TestInstallEnvDelegationWindows:
    """Windows-side spec + install-argv delegation contract."""

    def test_default_omits_skip_overrides(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        mock_vscodeclaude_config: None,
    ) -> None:
        """Without skip_github_install, overrides stay on (no --skip-overrides)."""
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.workspace.platform.system",
            lambda: "Windows",
        )

        create_startup_script(
            folder_path=tmp_path,
            issue_number=1,
            issue_title="Test",
            status="status-07:code-review",
            repo_name="test-repo",
            issue_url="https://github.com/test/repo/issues/1",
            is_intervention=False,
        )

        spec = read_session_spec(tmp_path)
        assert spec.skip_github_install is False
        assert "--skip-overrides" not in build_install_argv(spec, tmp_path)

    def test_skip_github_install_adds_skip_overrides_flag(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        mock_vscodeclaude_config: None,
    ) -> None:
        """skip_github_install=True is recorded and yields --skip-overrides."""
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.workspace.platform.system",
            lambda: "Windows",
        )

        create_startup_script(
            folder_path=tmp_path,
            issue_number=1,
            issue_title="Test",
            status="status-07:code-review",
            repo_name="test-repo",
            issue_url="https://github.com/test/repo/issues/1",
            is_intervention=False,
            skip_github_install=True,
        )

        spec = read_session_spec(tmp_path)
        assert spec.skip_github_install is True
        assert "--skip-overrides" in build_install_argv(spec, tmp_path)


class TestInstallEnvDelegationPosix:
    """POSIX-side spec + install-argv delegation contract (parity with Windows)."""

    @pytest.mark.parametrize("system", ["Darwin", "Linux"])
    def test_default_omits_skip_overrides(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        mock_vscodeclaude_config: None,
        system: str,
    ) -> None:
        """Without skip_github_install, overrides stay on (no --skip-overrides)."""
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.workspace.platform.system",
            lambda: system,
        )
        _write_mcp_config(tmp_path, system)

        create_startup_script(
            folder_path=tmp_path,
            issue_number=1,
            issue_title="Test",
            status="status-07:code-review",
            repo_name="test-repo",
            issue_url="https://github.com/test/repo/issues/1",
            is_intervention=False,
        )

        spec = read_session_spec(tmp_path)
        assert spec.skip_github_install is False
        assert "--skip-overrides" not in build_install_argv(spec, tmp_path)

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

        create_startup_script(
            folder_path=tmp_path,
            issue_number=1,
            issue_title="Test",
            status="status-07:code-review",
            repo_name="test-repo",
            issue_url="https://github.com/test/repo/issues/1",
            is_intervention=False,
            skip_github_install=True,
        )

        spec = read_session_spec(tmp_path)
        assert spec.skip_github_install is True
        assert "--skip-overrides" in build_install_argv(spec, tmp_path)


class TestSkipGithubInstallRoundTrip:
    """End-to-end: workspace.py -> spec JSON -> session_setup -> install argv.

    A single on-disk chain proving the ``skip_github_install`` flag survives
    serialization and reaches the install.py argv (or is absent by default).
    """

    def test_skip_github_install_true_round_trips_to_skip_overrides(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        mock_vscodeclaude_config: None,
    ) -> None:
        """create_startup_script(..., skip_github_install=True) -> --skip-overrides."""
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.workspace.platform.system",
            lambda: "Windows",
        )

        create_startup_script(
            folder_path=tmp_path,
            issue_number=42,
            issue_title="Round trip",
            status="status-07:code-review",
            repo_name="test-repo",
            issue_url="https://github.com/test/repo/issues/42",
            is_intervention=False,
            skip_github_install=True,
        )

        spec = read_session_spec(tmp_path)
        argv = build_install_argv(spec, tmp_path)
        assert "--skip-overrides" in argv

    def test_default_round_trips_without_skip_overrides(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        mock_vscodeclaude_config: None,
    ) -> None:
        """Default (overrides on) -> install argv omits --skip-overrides."""
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.workspace.platform.system",
            lambda: "Windows",
        )

        create_startup_script(
            folder_path=tmp_path,
            issue_number=42,
            issue_title="Round trip",
            status="status-07:code-review",
            repo_name="test-repo",
            issue_url="https://github.com/test/repo/issues/42",
            is_intervention=False,
        )

        spec = read_session_spec(tmp_path)
        argv = build_install_argv(spec, tmp_path)
        assert "--skip-overrides" not in argv

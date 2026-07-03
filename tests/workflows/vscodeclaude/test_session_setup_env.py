"""Tests for the pure helpers in ``session_setup`` (env, argv, banner)."""

import os
import sys
from pathlib import Path

import pytest

from mcp_coder.workflows.vscodeclaude import session_setup
from mcp_coder.workflows.vscodeclaude.session_setup import (
    build_claude_argv,
    build_install_argv,
    build_step_argv,
    build_subprocess_env,
    render_banner,
)
from mcp_coder.workflows.vscodeclaude.types import SessionSpec


def _make_spec(
    *,
    commands: list[str] | None = None,
    skip_github_install: bool = False,
    is_intervention: bool = False,
    mcp_config: str = ".mcp.json",
    timeout: int = 300,
) -> SessionSpec:
    return SessionSpec(
        issue_number=123,
        title="Fix the bug",
        repo="owner/repo",
        status="status-07:code-review",
        issue_url="https://github.com/owner/repo/issues/123",
        emoji="🔧",
        commands=commands if commands is not None else ["mcp-coder implement"],
        timeout=timeout,
        mcp_config=mcp_config,
        install_script_path="/coord/tools/install.py",
        mcp_coder_install_path="/coord",
        skip_github_install=skip_github_install,
        is_intervention=is_intervention,
    )


@pytest.mark.parametrize(
    ("platform", "bin_name"),
    [("win32", "Scripts"), ("linux", "bin")],
)
class TestBuildSubprocessEnv:
    """``build_subprocess_env`` overlays the MCP vars on a full env copy."""

    def test_all_mcp_vars_are_cwd_derived(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        platform: str,
        bin_name: str,
    ) -> None:
        """The four MCP vars point at CWD-derived paths."""
        monkeypatch.setattr(sys, "platform", platform)
        spec = _make_spec()
        env = build_subprocess_env(spec, tmp_path)

        assert env["MCP_CODER_PROJECT_DIR"] == str(tmp_path)
        assert env["MCP_CODER_VENV_DIR"] == str(tmp_path / ".venv")
        assert env["VIRTUAL_ENV"] == str(tmp_path / ".venv")
        assert Path(env["MCP_CODER_VENV_PATH"]).name == bin_name

    def test_virtual_env_matches_project_venv(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        platform: str,
        bin_name: str,
    ) -> None:
        """VIRTUAL_ENV equals ``<cwd>/.venv`` (the uv-sync target)."""
        monkeypatch.setattr(sys, "platform", platform)
        env = build_subprocess_env(_make_spec(), tmp_path)
        assert env["VIRTUAL_ENV"] == str(tmp_path / ".venv")

    def test_pinned_flags(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        platform: str,
        bin_name: str,
    ) -> None:
        """MCP_TIMEOUT and UV_GIT_SHALLOW carry the pinned values."""
        monkeypatch.setattr(sys, "platform", platform)
        env = build_subprocess_env(_make_spec(), tmp_path)
        assert env["MCP_TIMEOUT"] == "30000"
        assert env["UV_GIT_SHALLOW"] == "0"

    def test_path_prepends_coder_then_project_bin(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        platform: str,
        bin_name: str,
    ) -> None:
        """PATH starts with the coder venv bin, then the project venv bin."""
        monkeypatch.setattr(sys, "platform", platform)
        env = build_subprocess_env(_make_spec(), tmp_path)
        parts = env["PATH"].split(os.pathsep)

        assert parts[0] == env["MCP_CODER_VENV_PATH"]
        assert Path(parts[1]).name == bin_name
        assert Path(parts[1]).parent == tmp_path / ".venv"

    def test_preexisting_key_survives(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        platform: str,
        bin_name: str,
    ) -> None:
        """A pre-existing env key is preserved by the full-env copy."""
        monkeypatch.setattr(sys, "platform", platform)
        monkeypatch.setenv("USERPROFILE", "/home/tester")
        env = build_subprocess_env(_make_spec(), tmp_path)
        assert env["USERPROFILE"] == "/home/tester"


class TestBuildInstallArgv:
    """``build_install_argv`` mirrors the retired shell install flags."""

    def test_exact_flags(self, tmp_path: Path) -> None:
        """The provisioning argv carries the canonical flags in order."""
        argv = build_install_argv(_make_spec(), tmp_path)
        assert argv[1] == "/coord/tools/install.py"
        assert argv[2] == str(tmp_path)
        assert "--source" in argv and "local" in argv
        assert "--local-path" in argv
        assert "--extras" in argv and "dev" in argv
        assert "--use-sync" in argv
        assert "--refresh" in argv

    def test_skip_overrides_present_when_skip_github_install(
        self, tmp_path: Path
    ) -> None:
        """``--skip-overrides`` appears iff ``skip_github_install`` is set."""
        with_skip = build_install_argv(_make_spec(skip_github_install=True), tmp_path)
        without_skip = build_install_argv(
            _make_spec(skip_github_install=False), tmp_path
        )
        assert "--skip-overrides" in with_skip
        assert "--skip-overrides" not in without_skip


class TestBuildStepArgv:
    """``build_step_argv`` distinguishes first step from resume step."""

    def test_first_step_captures_session_id(self) -> None:
        """First step (session_id None) prompts ``<cmd> <issue>`` + captures id."""
        argv = build_step_argv(
            _make_spec(),
            "mcp-coder implement",
            session_id=None,
            issue_number=123,
        )
        assert "mcp-coder implement 123" in argv
        assert "--output-format" in argv
        assert "session-id" in argv
        assert "--session-id" not in argv
        assert argv[argv.index("--llm-method") + 1] == "claude"

    def test_resume_step_uses_session_id(self) -> None:
        """Resume step prompts bare ``<cmd>`` and passes ``--session-id``."""
        argv = build_step_argv(
            _make_spec(),
            "mcp-coder commit",
            session_id="abc-123",
            issue_number=123,
        )
        assert "mcp-coder commit" in argv
        assert "123" not in " ".join(argv).replace("abc-123", "")
        assert "--session-id" in argv
        assert argv[argv.index("--session-id") + 1] == "abc-123"
        assert "--output-format" not in argv

    def test_config_and_timeout_present(self) -> None:
        """Both steps forward ``--mcp-config`` and ``--timeout``."""
        argv = build_step_argv(
            _make_spec(mcp_config=".mcp.linux.json", timeout=600),
            "cmd",
            session_id=None,
            issue_number=1,
        )
        assert argv[argv.index("--mcp-config") + 1] == ".mcp.linux.json"
        assert argv[argv.index("--timeout") + 1] == "600"


class TestBuildClaudeArgv:
    """``build_claude_argv`` covers intervention / one-command / resume shapes."""

    def test_intervention_is_bare(self) -> None:
        """No prompt yields a bare ``claude`` call (intervention)."""
        argv = build_claude_argv(_make_spec())
        assert argv == [
            "claude",
            "--mcp-config",
            ".mcp.json",
            "--strict-mcp-config",
        ]

    def test_single_command_has_prompt_no_resume(self) -> None:
        """A prompt without a session id appends the prompt, no ``--resume``."""
        argv = build_claude_argv(_make_spec(), prompt="mcp-coder implement 123")
        assert "--resume" not in argv
        assert argv[-1] == "mcp-coder implement 123"

    def test_resume_has_resume_and_prompt(self) -> None:
        """A prompt with a session id resumes then appends the prompt."""
        argv = build_claude_argv(
            _make_spec(), prompt="mcp-coder commit", session_id="abc-123"
        )
        assert argv[argv.index("--resume") + 1] == "abc-123"
        assert argv[-1] == "mcp-coder commit"

    def test_strict_mcp_config_always_present(self) -> None:
        """``--strict-mcp-config`` is present in every shape."""
        assert "--strict-mcp-config" in build_claude_argv(_make_spec())
        assert "--strict-mcp-config" in build_claude_argv(_make_spec(), prompt="x")
        assert "--strict-mcp-config" in build_claude_argv(
            _make_spec(), prompt="x", session_id="id"
        )


class TestRenderBanner:
    """``render_banner`` emits the banner and conditional intervention warning."""

    def test_contains_banner_fields(self) -> None:
        """The banner echoes emoji, issue, title, repo, status, and URL."""
        banner = render_banner(_make_spec())
        assert "🔧" in banner
        assert "123" in banner
        assert "Fix the bug" in banner
        assert "owner/repo" in banner
        assert "status-07:code-review" in banner
        assert "https://github.com/owner/repo/issues/123" in banner

    def test_normal_spec_has_no_warning(self) -> None:
        """A non-intervention spec omits the intervention warning."""
        banner = render_banner(_make_spec(is_intervention=False))
        assert "INTERVENTION MODE" not in banner

    def test_intervention_spec_appends_warning(self) -> None:
        """An intervention spec appends the ``!! INTERVENTION MODE`` warning."""
        banner = render_banner(_make_spec(is_intervention=True))
        assert "INTERVENTION MODE - Automation may be running elsewhere" in banner
        assert "No automated analysis will run." in banner


def test_venv_bin_dir_platform_specific(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """``_venv_bin_dir`` returns ``Scripts`` on win32 and ``bin`` elsewhere."""
    monkeypatch.setattr(sys, "platform", "win32")
    assert session_setup._venv_bin_dir(tmp_path).name == "Scripts"
    monkeypatch.setattr(sys, "platform", "linux")
    assert session_setup._venv_bin_dir(tmp_path).name == "bin"

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
        mcp_coder_install_path="/coord",
        skip_github_install=skip_github_install,
        is_intervention=is_intervention,
    )


def _make_venv_python(cwd: Path, platform: str, bin_name: str) -> None:
    """Create the interpreter file of ``<cwd>/.venv`` for ``platform``."""
    name = "python.exe" if platform == "win32" else "python"
    bin_dir = cwd / ".venv" / bin_name
    bin_dir.mkdir(parents=True)
    (bin_dir / name).write_text("", encoding="utf-8")


@pytest.mark.parametrize(
    ("platform", "bin_name"),
    [("win32", "Scripts"), ("linux", "bin")],
)
class TestBuildSubprocessEnv:
    """``build_subprocess_env`` overlays the MCP vars on a full env copy."""

    def test_mcp_vars(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        platform: str,
        bin_name: str,
    ) -> None:
        """Project dir is CWD; venv dir and bin name the tool venv."""
        monkeypatch.setattr(sys, "platform", platform)
        spec = _make_spec()
        env = build_subprocess_env(spec, tmp_path)

        assert env["MCP_CODER_PROJECT_DIR"] == str(tmp_path)
        assert env["MCP_CODER_VENV_DIR"] == str(Path("/coord") / ".venv")
        assert env["MCP_CODER_VENV_PATH"] == str(Path("/coord") / ".venv" / bin_name)

    def test_project_venv_with_interpreter_is_overlaid(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        platform: str,
        bin_name: str,
    ) -> None:
        """An interpreter in ``<cwd>/.venv`` sets VIRTUAL_ENV and PATH."""
        monkeypatch.setattr(sys, "platform", platform)
        monkeypatch.setenv("PATH", "rest")
        _make_venv_python(tmp_path, platform, bin_name)
        env = build_subprocess_env(_make_spec(), tmp_path)

        assert env["VIRTUAL_ENV"] == str(tmp_path / ".venv")
        assert env["PATH"].split(os.pathsep) == [
            env["MCP_CODER_VENV_PATH"],
            str(tmp_path / ".venv" / bin_name),
            "rest",
        ]

    def test_no_project_venv_drops_inherited_virtual_env(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        platform: str,
        bin_name: str,
    ) -> None:
        """Without a venv interpreter: no VIRTUAL_ENV, PATH has coder bin only."""
        monkeypatch.setattr(sys, "platform", platform)
        monkeypatch.setenv("PATH", "rest")
        monkeypatch.setenv("VIRTUAL_ENV", "/inherited/venv")
        env = build_subprocess_env(_make_spec(), tmp_path)

        assert "VIRTUAL_ENV" not in env
        assert env["PATH"].split(os.pathsep) == [env["MCP_CODER_VENV_PATH"], "rest"]

    def test_with_project_venv_false_skips_overlay(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        platform: str,
        bin_name: str,
    ) -> None:
        """``with_project_venv=False`` ignores an existing project venv."""
        monkeypatch.setattr(sys, "platform", platform)
        monkeypatch.setenv("PATH", "rest")
        monkeypatch.setenv("VIRTUAL_ENV", "/inherited/venv")
        _make_venv_python(tmp_path, platform, bin_name)
        env = build_subprocess_env(_make_spec(), tmp_path, with_project_venv=False)

        assert "VIRTUAL_ENV" not in env
        assert env["PATH"].split(os.pathsep) == [env["MCP_CODER_VENV_PATH"], "rest"]

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
    """``build_install_argv`` calls ``mcp-coder setup``."""

    def test_exact_flags(self, tmp_path: Path) -> None:
        """The setup argv carries the canonical flags in order."""
        argv = build_install_argv(_make_spec(), tmp_path)
        assert Path(argv[0]).stem == "mcp-coder"
        assert argv[1:] == ["setup", "--project-dir", str(tmp_path), "--refresh"]

    def test_skip_overrides_present_when_skip_github_install(
        self, tmp_path: Path
    ) -> None:
        """``--skip-overrides`` appears iff ``skip_github_install`` is set."""
        with_skip = build_install_argv(_make_spec(skip_github_install=True), tmp_path)
        without_skip = build_install_argv(
            _make_spec(skip_github_install=False), tmp_path
        )
        assert with_skip[-1] == "--skip-overrides"
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

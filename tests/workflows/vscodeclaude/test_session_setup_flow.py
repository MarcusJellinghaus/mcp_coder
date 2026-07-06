"""Flow tests for ``session_setup`` orchestration + ``main``.

Every impure call funnels through ``session_setup.subprocess.run``, patched at a
single point via ``_FakeRun``. Tests assert ordered argv, env propagation,
session-id threading, non-fatal middle steps, and ``main``'s graceful exit-0.
"""

import subprocess
from pathlib import Path
from typing import Any

import pytest

from mcp_coder.workflows.vscodeclaude import session_setup
from mcp_coder.workflows.vscodeclaude.types import (
    SessionSpec,
    write_session_spec,
)

_MCP_VARS = (
    "MCP_CODER_VENV_PATH",
    "MCP_CODER_PROJECT_DIR",
    "MCP_CODER_VENV_DIR",
    "VIRTUAL_ENV",
)


def _make_spec(
    *,
    commands: list[str] | None = None,
    is_intervention: bool = False,
    skip_github_install: bool = False,
) -> SessionSpec:
    return SessionSpec(
        issue_number=123,
        title="Fix the bug",
        repo="owner/repo",
        status="status-07:code-review",
        issue_url="https://github.com/owner/repo/issues/123",
        emoji="🔧",
        commands=commands if commands is not None else ["mcp-coder implement"],
        timeout=300,
        mcp_config=".mcp.json",
        install_script_path="/coord/tools/install.py",
        mcp_coder_install_path="/coord",
        skip_github_install=skip_github_install,
        is_intervention=is_intervention,
    )


class _FakeRun:
    """Recording stand-in for ``subprocess.run``.

    Records ``(argv, kwargs)`` per call and returns a ``CompletedProcess`` whose
    stdout is ``stdout`` and whose returncode comes from ``returncodes`` (keyed
    by 0-based call index, defaulting to 0).
    """

    def __init__(
        self,
        *,
        stdout: str = "sid-abc\n",
        stderr: str = "",
        returncodes: dict[int, int] | None = None,
    ) -> None:
        self.calls: list[tuple[list[str], dict[str, Any]]] = []
        self._stdout = stdout
        self._stderr = stderr
        self._returncodes = returncodes or {}

    def __call__(
        self, argv: list[str], **kwargs: Any
    ) -> "subprocess.CompletedProcess[str]":
        index = len(self.calls)
        self.calls.append((list(argv), kwargs))
        return subprocess.CompletedProcess(
            argv,
            self._returncodes.get(index, 0),
            stdout=self._stdout,
            stderr=self._stderr,
        )

    def argvs(self) -> list[list[str]]:
        return [argv for argv, _ in self.calls]


# String target avoids typed attribute access on the module's re-exported
# ``subprocess`` (mypy ``no-implicit-reexport``) while patching the single
# impure symbol.
_RUN_TARGET = "mcp_coder.workflows.vscodeclaude.session_setup.subprocess.run"


def _patch_run(monkeypatch: pytest.MonkeyPatch, fake: _FakeRun) -> _FakeRun:
    monkeypatch.setattr(_RUN_TARGET, fake)
    return fake


def _is_install(argv: list[str]) -> bool:
    return "/coord/tools/install.py" in argv


def _is_claude(argv: list[str]) -> bool:
    return argv[0] == "claude"


def _is_prompt(argv: list[str]) -> bool:
    return "prompt" in argv and not _is_claude(argv)


@pytest.fixture()
def fake_run(monkeypatch: pytest.MonkeyPatch) -> _FakeRun:
    return _patch_run(monkeypatch, _FakeRun())


class TestOrchestrateIntervention:
    """Intervention specs launch a single bare ``claude``."""

    def test_single_bare_claude_no_prompt(self, fake_run: _FakeRun) -> None:
        session_setup.orchestrate(
            _make_spec(is_intervention=True), Path("/proj"), {"X": "1"}
        )
        assert len(fake_run.calls) == 1
        argv = fake_run.argvs()[0]
        assert _is_claude(argv)
        assert "--strict-mcp-config" in argv
        assert not any(_is_prompt(a) for a in fake_run.argvs())

    def test_banner_includes_intervention_warning(
        self, capsys: pytest.CaptureFixture[str], tmp_path: Path, fake_run: _FakeRun
    ) -> None:
        write_session_spec(tmp_path, _make_spec(is_intervention=True))
        session_setup.run_session(tmp_path)
        out = capsys.readouterr().out
        assert "INTERVENTION MODE" in out

    def test_normal_banner_omits_warning(
        self, capsys: pytest.CaptureFixture[str], tmp_path: Path, fake_run: _FakeRun
    ) -> None:
        write_session_spec(tmp_path, _make_spec(is_intervention=False))
        session_setup.run_session(tmp_path)
        out = capsys.readouterr().out
        assert "INTERVENTION MODE" not in out


class TestOrchestrateCommandShapes:
    """0/1/multi command shapes drive the expected subprocess sequence."""

    def test_zero_commands_only_venv(self, fake_run: _FakeRun) -> None:
        session_setup.orchestrate(_make_spec(commands=[]), Path("/proj"), {})
        assert fake_run.calls == []

    def test_one_command_single_interactive_claude(self, fake_run: _FakeRun) -> None:
        session_setup.orchestrate(
            _make_spec(commands=["mcp-coder implement"]), Path("/proj"), {}
        )
        assert len(fake_run.calls) == 1
        argv = fake_run.argvs()[0]
        assert _is_claude(argv)
        assert argv[-1] == "mcp-coder implement 123"
        assert "--resume" not in argv

    def test_multi_command_order_and_id_threading(self, fake_run: _FakeRun) -> None:
        spec = _make_spec(
            commands=["mcp-coder implement", "mcp-coder verify", "mcp-coder commit"]
        )
        session_setup.orchestrate(spec, Path("/proj"), {})

        argvs = fake_run.argvs()
        assert len(argvs) == 3
        first, middle, last = argvs

        # First step: automated prompt that captures the session id.
        assert _is_prompt(first)
        assert "--output-format" in first
        assert "mcp-coder implement 123" in first

        # Middle step: resumes captured id, non-interactive prompt.
        assert _is_prompt(middle)
        assert middle[middle.index("--session-id") + 1] == "sid-abc"

        # Last step: interactive claude resuming the captured id.
        assert _is_claude(last)
        assert last[last.index("--resume") + 1] == "sid-abc"
        assert last[-1] == "mcp-coder commit"


class TestSessionIdCapture:
    """``run_first_step`` parses stdout as the session id."""

    def test_captures_trimmed_stdout(self, monkeypatch: pytest.MonkeyPatch) -> None:
        fake = _FakeRun(stdout="abc123\n")
        _patch_run(monkeypatch, fake)
        session_id = session_setup.run_first_step(
            _make_spec(), "mcp-coder implement", {}, Path("/proj")
        )
        assert session_id == "abc123"
        # First step must capture output.
        assert fake.calls[0][1]["capture_output"] is True
        assert fake.calls[0][1]["text"] is True

    def test_empty_stdout_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        fake = _FakeRun(stdout="   \n")
        _patch_run(monkeypatch, fake)
        with pytest.raises(RuntimeError):
            session_setup.run_first_step(
                _make_spec(), "mcp-coder implement", {}, Path("/proj")
            )

    def test_empty_session_id_surfaces_stderr(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Empty session id surfaces the captured stderr and returncode."""
        fake = _FakeRun(
            stdout="",
            stderr="boom: mcp-coder blew up\n",
            returncodes={0: 2},
        )
        _patch_run(monkeypatch, fake)
        with pytest.raises(RuntimeError) as excinfo:
            session_setup.run_first_step(
                _make_spec(), "mcp-coder implement", {}, Path("/proj")
            )
        # Real cause is visible in the exception message ...
        assert "boom: mcp-coder blew up" in str(excinfo.value)
        assert "returncode=2" in str(excinfo.value)
        # ... and echoed to stderr for the operator.
        assert "boom: mcp-coder blew up" in capsys.readouterr().err


class TestMiddleStepNonFatal:
    """A non-zero middle step warns but the flow still reaches the last claude."""

    def test_warns_and_continues(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        # Calls: [0] first-step capture, [1] middle (fails), [2] last claude.
        fake = _FakeRun(returncodes={1: 1})
        _patch_run(monkeypatch, fake)
        spec = _make_spec(
            commands=["mcp-coder implement", "mcp-coder verify", "mcp-coder commit"]
        )
        session_setup.orchestrate(spec, Path("/proj"), {})

        out = capsys.readouterr().out
        assert "Step 2 encountered an error. Continuing..." in out
        # Flow still reached the final interactive claude.
        assert _is_claude(fake.argvs()[-1])


class TestEnvPropagation:
    """Every subprocess call carries the shared env and the string cwd."""

    def test_env_and_cwd_on_every_call(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        fake = _FakeRun()
        _patch_run(monkeypatch, fake)
        write_session_spec(
            tmp_path,
            _make_spec(
                commands=[
                    "mcp-coder implement",
                    "mcp-coder verify",
                    "mcp-coder commit",
                ]
            ),
        )
        session_setup.run_session(tmp_path)

        assert fake.calls  # sanity
        for _argv, kwargs in fake.calls:
            env = kwargs["env"]
            for var in _MCP_VARS:
                assert var in env
            assert kwargs["cwd"] == str(tmp_path)

    def test_install_env_virtual_env_is_project_venv(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        fake = _FakeRun()
        _patch_run(monkeypatch, fake)
        write_session_spec(tmp_path, _make_spec(commands=[]))
        session_setup.run_session(tmp_path)

        install_calls = [
            (argv, kwargs) for argv, kwargs in fake.calls if _is_install(argv)
        ]
        assert len(install_calls) == 1
        _argv, kwargs = install_calls[0]
        assert kwargs["env"]["VIRTUAL_ENV"] == str(tmp_path / ".venv")
        assert kwargs["check"] is True


class TestRunSessionProvisioning:
    """``run_session`` provisions the venv before orchestrating."""

    def test_install_runs_first(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        fake = _FakeRun()
        _patch_run(monkeypatch, fake)
        write_session_spec(tmp_path, _make_spec(commands=["mcp-coder implement"]))
        session_setup.run_session(tmp_path)

        assert _is_install(fake.argvs()[0])
        assert _is_claude(fake.argvs()[1])


class TestMainGracefulExit:
    """``main`` prompts once and exits 0 on any expected failure."""

    def test_read_spec_failure_exits_zero_and_prompts(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        prompts: list[str] = []
        monkeypatch.setattr("builtins.input", lambda msg="": prompts.append(msg))

        def _boom(_cwd: Path) -> SessionSpec:
            raise FileNotFoundError("no spec")

        monkeypatch.setattr(session_setup, "read_session_spec", _boom)

        with pytest.raises(SystemExit) as excinfo:
            session_setup.main([str(tmp_path)])

        assert excinfo.value.code == 0
        assert len(prompts) == 1

    def test_success_path_returns_without_prompt(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path, fake_run: _FakeRun
    ) -> None:
        prompts: list[str] = []
        monkeypatch.setattr("builtins.input", lambda msg="": prompts.append(msg))
        write_session_spec(tmp_path, _make_spec(commands=[]))

        session_setup.main([str(tmp_path)])

        assert prompts == []


class TestUtf8BeforeBanner:
    """UTF-8 stdout is forced before the banner prints."""

    def test_force_utf8_precedes_banner(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path, fake_run: _FakeRun
    ) -> None:
        order: list[str] = []
        monkeypatch.setattr(
            session_setup, "_force_utf8_stdout", lambda: order.append("utf8")
        )
        real_render = session_setup.render_banner

        def _spy_render(spec: SessionSpec) -> str:
            order.append("banner")
            return real_render(spec)

        monkeypatch.setattr(session_setup, "render_banner", _spy_render)
        write_session_spec(tmp_path, _make_spec(commands=[]))

        session_setup.main([str(tmp_path)])

        assert order == ["utf8", "banner"]

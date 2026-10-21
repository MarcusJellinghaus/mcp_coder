"""Unit tests for the post-install checks phase and its executable resolver.

The runner is stubbed by patching ``_phases.execute_subprocess``, so no
process is ever spawned. Every test pins ``PATH`` to a ``tmp_path``
directory it controls, so tool binaries already installed on the host
(``mcp-coder``, ``mcp-workspace``, ...) cannot change the outcome.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from mcp_coder.install import InstallConfig, _phases, install
from mcp_coder.install._env import exe
from mcp_coder.utils.subprocess_runner import CommandOptions, CommandResult

from .conftest import namespace as _namespace


def _ok(
    return_code: int = 0,
    *,
    timed_out: bool = False,
    execution_error: str | None = None,
) -> CommandResult:
    """Build a CommandResult the way the real runner does."""
    return CommandResult(
        return_code=return_code,
        stdout="",
        stderr="",
        timed_out=timed_out,
        execution_error=execution_error,
    )


def _config(
    tmp_path: Path, checks: list[list[str]], *, check: bool = False
) -> InstallConfig:
    """Write a pyproject.toml declaring ``checks`` and resolve a config for it."""
    if checks:
        body = ", ".join(json.dumps(c) for c in checks)
        text = f"[tool.mcp-coder.install]\npost_install_checks = [{body}]\n"
    else:
        text = '[project]\nname = "test-project"\n'
    (tmp_path / "pyproject.toml").write_text(text, encoding="utf-8")
    return InstallConfig.from_args(_namespace(target=tmp_path, check=check))


def _touch(directory: Path, name: str) -> Path:
    """Create an empty fake executable ``directory/name``."""
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / name
    path.write_text("", encoding="utf-8")
    return path


class _Runner:
    """Stand-in for execute_subprocess that records every call."""

    def __init__(self, results: list[CommandResult] | None = None) -> None:
        self.calls: list[tuple[list[str], CommandOptions]] = []
        self._results = list(results or [])

    def __call__(self, cmd: list[str], options: CommandOptions) -> CommandResult:
        self.calls.append((cmd, options))
        return self._results.pop(0) if self._results else _ok()


@pytest.fixture
def bin_dir(tmp_path: Path) -> Path:
    """The venv executable directory under ``tmp_path``."""
    directory = tmp_path / "venv-bin"
    directory.mkdir()
    return directory


@pytest.fixture
def path_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """An empty directory that is the only ``PATH`` entry."""
    directory = tmp_path / "path-dir"
    directory.mkdir()
    monkeypatch.setenv("PATH", str(directory))
    return directory


@pytest.fixture
def runner(monkeypatch: pytest.MonkeyPatch) -> _Runner:
    """Patch the phase's subprocess runner with a recording stub."""
    stub = _Runner()
    monkeypatch.setattr(_phases, "execute_subprocess", stub)
    return stub


class TestPhasePostInstallChecks:
    """Running the declared checks and summarising failures."""

    def test_no_checks_declared_is_silent(
        self,
        tmp_path: Path,
        bin_dir: Path,
        path_dir: Path,
        runner: _Runner,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _phases.phase_post_install_checks(_config(tmp_path, []), bin_dir)
        assert capsys.readouterr().out == ""
        assert runner.calls == []

    def test_all_pass(
        self,
        tmp_path: Path,
        bin_dir: Path,
        path_dir: Path,
        runner: _Runner,
    ) -> None:
        a = _touch(bin_dir, exe("tool-a"))
        b = _touch(bin_dir, exe("tool-b"))
        config = _config(tmp_path, [["tool-a", "--version"], ["tool-b"]])
        _phases.phase_post_install_checks(config, bin_dir)  # must not exit

        assert [cmd for cmd, _ in runner.calls] == [[str(a), "--version"], [str(b)]]
        for _, options in runner.calls:
            assert options.cwd == str(config.local_path)
            assert options.timeout_seconds == 300
            assert options.capture_output is False
            assert options.env is not None
            assert options.env["PATH"].startswith(str(bin_dir))

    def test_one_failure_exits_with_summary(
        self,
        tmp_path: Path,
        bin_dir: Path,
        path_dir: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _touch(bin_dir, exe("tool-a"))
        _touch(bin_dir, exe("tool-b"))
        monkeypatch.setattr(_phases, "execute_subprocess", _Runner([_ok(), _ok(2)]))
        config = _config(tmp_path, [["tool-a"], ["tool-b", "--version"]])
        with pytest.raises(SystemExit) as exc_info:
            _phases.phase_post_install_checks(config, bin_dir)
        assert exc_info.value.code == 1
        out = capsys.readouterr().out
        assert "1 of 2 post-install checks failed" in out
        assert "tool-b --version: exit code 2" in out

    def test_several_failures_all_run_one_summary(
        self,
        tmp_path: Path,
        bin_dir: Path,
        path_dir: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _touch(bin_dir, exe("tool-a"))
        _touch(bin_dir, exe("tool-b"))
        _touch(bin_dir, exe("tool-c"))
        stub = _Runner([_ok(1), _ok(), _ok(3)])
        monkeypatch.setattr(_phases, "execute_subprocess", stub)
        config = _config(tmp_path, [["tool-a"], ["tool-b"], ["tool-c"], ["missing"]])
        with pytest.raises(SystemExit):
            _phases.phase_post_install_checks(config, bin_dir)
        assert len(stub.calls) == 3
        out = capsys.readouterr().out
        assert out.count("post-install checks failed") == 1
        assert "3 of 4 post-install checks failed" in out
        assert "tool-a: exit code 1" in out
        assert "tool-c: exit code 3" in out
        assert "missing: not found" in out
        assert "tool-b:" not in out

    def test_timeout_reason_wins_over_error_and_code(
        self,
        tmp_path: Path,
        bin_dir: Path,
        path_dir: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _touch(bin_dir, exe("slow"))
        timed_out = _ok(
            1,
            timed_out=True,
            execution_error="Process timed out after 300 seconds",
        )
        monkeypatch.setattr(_phases, "execute_subprocess", _Runner([timed_out]))
        with pytest.raises(SystemExit):
            _phases.phase_post_install_checks(_config(tmp_path, [["slow"]]), bin_dir)
        out = capsys.readouterr().out
        assert "slow: timed out after 300 s" in out
        assert "Process timed out" not in out
        assert "exit code" not in out

    def test_execution_error_text_is_reported(
        self,
        tmp_path: Path,
        bin_dir: Path,
        path_dir: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _touch(bin_dir, exe("locked"))
        error = _ok(1, execution_error="PermissionError: access denied")
        monkeypatch.setattr(_phases, "execute_subprocess", _Runner([error]))
        with pytest.raises(SystemExit):
            _phases.phase_post_install_checks(_config(tmp_path, [["locked"]]), bin_dir)
        out = capsys.readouterr().out
        assert "locked: PermissionError: access denied" in out
        assert "exit code" not in out

    def test_not_found_never_spawns(
        self,
        tmp_path: Path,
        bin_dir: Path,
        path_dir: Path,
        runner: _Runner,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        with pytest.raises(SystemExit):
            _phases.phase_post_install_checks(
                _config(tmp_path, [["nowhere", "--version"]]), bin_dir
            )
        assert runner.calls == []
        assert "nowhere --version: not found" in capsys.readouterr().out

    def test_cwd_is_never_searched(
        self,
        tmp_path: Path,
        bin_dir: Path,
        runner: _Runner,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        cwd = tmp_path / "cwd"
        _touch(cwd, exe("in-cwd"))
        monkeypatch.chdir(cwd)
        monkeypatch.setenv("PATH", ".")
        with pytest.raises(SystemExit):
            _phases.phase_post_install_checks(_config(tmp_path, [["in-cwd"]]), bin_dir)
        assert runner.calls == []
        assert "in-cwd: not found" in capsys.readouterr().out

    def test_dry_run_echoes_declared_argv(
        self,
        tmp_path: Path,
        bin_dir: Path,
        path_dir: Path,
        runner: _Runner,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        config = _config(tmp_path, [["tool-a", "--version"], ["tool-b"]], check=True)
        _phases.phase_post_install_checks(config, bin_dir)
        assert runner.calls == []
        lines = [
            line for line in capsys.readouterr().out.splitlines() if line[:2] == "> "
        ]
        assert len(lines) == 2
        assert lines[0].startswith("> tool-a --version")
        assert lines[1].startswith("> tool-b")


class TestResolveCheckExecutable:
    """Where argv[0] of a check is looked up."""

    def test_venv_beats_path(
        self, tmp_path: Path, bin_dir: Path, path_dir: Path
    ) -> None:
        venv_tool = _touch(bin_dir, exe("tool"))
        _touch(path_dir, exe("tool"))
        resolved = _phases._resolve_check_executable("tool", bin_dir, tmp_path)
        assert resolved == venv_tool

    def test_path_fallback(self, tmp_path: Path, bin_dir: Path, path_dir: Path) -> None:
        path_tool = _touch(path_dir, exe("tool"))
        resolved = _phases._resolve_check_executable("tool", bin_dir, tmp_path)
        assert resolved == path_tool

    def test_exe_suffixed_name_gets_no_double_suffix(
        self,
        tmp_path: Path,
        bin_dir: Path,
        path_dir: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(_phases, "exe", lambda name: f"{name}.exe")
        tool = _touch(bin_dir, "tool.exe")
        _touch(bin_dir, "tool.exe.exe")  # would win if the suffix were doubled
        assert _phases._resolve_check_executable("tool.exe", bin_dir, tmp_path) == tool

    def test_relative_path_resolved_against_local_path(
        self, tmp_path: Path, bin_dir: Path, path_dir: Path
    ) -> None:
        local_path = tmp_path / "project"
        tool = _touch(local_path / "tools", "check")
        resolved = _phases._resolve_check_executable("tools/check", bin_dir, local_path)
        assert resolved == tool

    def test_absolute_path_used_as_is(
        self, tmp_path: Path, bin_dir: Path, path_dir: Path
    ) -> None:
        tool = _touch(tmp_path / "elsewhere", "check")
        resolved = _phases._resolve_check_executable(
            str(tool), bin_dir, tmp_path / "project"
        )
        assert resolved == tool

    def test_missing_path_form_is_not_found(
        self, tmp_path: Path, bin_dir: Path, path_dir: Path
    ) -> None:
        assert (
            _phases._resolve_check_executable("tools/absent", bin_dir, tmp_path) is None
        )


class TestInstallDriver:
    """install() wires the phase in before the completion line."""

    def test_failure_suppresses_complete_line(
        self,
        tmp_path: Path,
        path_dir: Path,
        runner: _Runner,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.setattr("mcp_coder.install.ensure_system_uv", lambda: "uv")
        for name in (
            "phase_venv",
            "phase_bootstrap_pip_uv",
            "phase_overrides",
            "phase_report_versions",
        ):
            monkeypatch.setattr(f"mcp_coder.install.{name}", lambda *_a: None)
        monkeypatch.setattr("mcp_coder.install.phase_install_main", lambda *_a: False)

        with pytest.raises(SystemExit):
            install(_config(tmp_path, [["nowhere"]]))
        out = capsys.readouterr().out
        assert "nowhere: not found" in out
        assert "install complete" not in out

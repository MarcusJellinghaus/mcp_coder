"""Tests for the setup step runner (``mcp_coder.install.project_setup``).

Every subprocess, install and git call is mocked: the steps are fakes.
"""

from __future__ import annotations

import logging
import os
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.install.project_setup import SetupError, run_setup
from mcp_coder.utils.mcp_verification import get_bin_dir
from mcp_coder.utils.setup_config import DEFAULT_STEP_TIMEOUT, SetupConfig, SetupStep
from mcp_coder.utils.subprocess_runner import CommandResult

_MOD = "mcp_coder.install.project_setup"

_PYTHON = SetupStep(None, "python", None, DEFAULT_STEP_TIMEOUT)


def _argv(*argv: str, name: str | None = None, timeout: int = 60) -> SetupStep:
    return SetupStep(tuple(argv), None, name, timeout)


def _result(**overrides: Any) -> CommandResult:
    values: dict[str, Any] = {
        "return_code": 0,
        "stdout": "",
        "stderr": "",
        "timed_out": False,
    }
    values.update(overrides)
    return CommandResult(**values)


def _status(
    *,
    success: bool = True,
    staged: list[str] | None = None,
    modified: list[str] | None = None,
    untracked: list[str] | None = None,
    error: str | None = None,
) -> dict[str, Any]:
    return {
        "success": success,
        "error": error,
        "returncode": 0 if success else 128,
        "stderr": "",
        "clean": not (staged or modified or untracked),
        "staged": staged or [],
        "modified": modified or [],
        "untracked": untracked or [],
    }


@dataclass
class Mocks:
    """The patched collaborators of ``run_setup``."""

    load: MagicMock
    install: MagicMock
    install_config: MagicMock
    execute: MagicMock
    resolve: MagicMock
    is_repo: MagicMock
    status: MagicMock

    def set_steps(self, *steps: SetupStep) -> None:
        """Make ``load_setup_config`` return these steps."""
        self.load.return_value = SetupConfig(steps, "pyproject.toml")

    def run_argvs(self) -> list[list[str]]:
        """Command lines passed to ``execute_subprocess``, in order."""
        return [c.args[0] for c in self.execute.call_args_list]


@pytest.fixture(autouse=True)
def _no_uv_git_shallow(monkeypatch: pytest.MonkeyPatch) -> None:
    # setenv first so monkeypatch restores the original state (set or unset).
    monkeypatch.setenv("UV_GIT_SHALLOW", "1")
    monkeypatch.delenv("UV_GIT_SHALLOW")


@pytest.fixture
def mocks() -> Iterator[Mocks]:
    with (
        patch(f"{_MOD}.load_setup_config") as load,
        patch(f"{_MOD}.install") as install,
        patch(f"{_MOD}.InstallConfig") as install_config,
        patch(f"{_MOD}.execute_subprocess") as execute,
        patch(f"{_MOD}.resolve_executable") as resolve,
        patch(f"{_MOD}.is_git_repository") as is_repo,
        patch(f"{_MOD}.get_working_tree_status") as status,
    ):
        resolve.side_effect = lambda argv0, project_dir, path=None: f"/bin/{argv0}"
        execute.return_value = _result()
        is_repo.return_value = True
        status.return_value = _status()
        yield Mocks(load, install, install_config, execute, resolve, is_repo, status)


def _run(project_dir: Path, **kwargs: bool) -> None:
    run_setup(
        project_dir,
        refresh=kwargs.get("refresh", False),
        skip_overrides=kwargs.get("skip_overrides", False),
    )


class TestArgvSteps:
    """Command-line steps."""

    def test_steps_run_in_order(self, mocks: Mocks, tmp_path: Path) -> None:
        mocks.set_steps(_argv("first", "a"), _argv("second", "b", "c"))
        _run(tmp_path)
        assert mocks.run_argvs() == [["/bin/first", "a"], ["/bin/second", "b", "c"]]

    def test_options(self, mocks: Mocks, tmp_path: Path) -> None:
        mocks.set_steps(_argv("tool", timeout=42))
        _run(tmp_path)
        options = mocks.execute.call_args.args[1]
        assert options.cwd == str(tmp_path)
        assert options.timeout_seconds == 42
        assert options.capture_output is False

    def test_first_failure_stops_the_rest(self, mocks: Mocks, tmp_path: Path) -> None:
        mocks.set_steps(_argv("bad", name="Bad step"), _argv("never"))
        mocks.execute.return_value = _result(return_code=3)
        with pytest.raises(SetupError, match="Bad step"):
            _run(tmp_path)
        assert mocks.run_argvs() == [["/bin/bad"]]

    @pytest.mark.parametrize(
        "result",
        [
            _result(return_code=1),
            _result(return_code=1, timed_out=True),
            _result(return_code=1, execution_error="boom"),
        ],
        ids=["non-zero", "timeout", "execution-error"],
    )
    def test_failure_names_step(
        self, mocks: Mocks, tmp_path: Path, result: CommandResult
    ) -> None:
        mocks.set_steps(_argv("npm", "ci"))
        mocks.execute.return_value = result
        with pytest.raises(SetupError, match="npm ci"):
            _run(tmp_path)

    def test_unresolved_argv0(self, mocks: Mocks, tmp_path: Path) -> None:
        mocks.set_steps(_argv("missing", name="Missing tool"), _argv("never"))
        mocks.resolve.side_effect = None
        mocks.resolve.return_value = None
        with pytest.raises(SetupError, match="Missing tool.*'missing' not found"):
            _run(tmp_path)
        mocks.execute.assert_not_called()

    def test_npm_without_python_venv(self, mocks: Mocks, tmp_path: Path) -> None:
        mocks.set_steps(_argv("npm", "ci"))
        _run(tmp_path)
        mocks.install.assert_not_called()
        mocks.install_config.from_args.assert_not_called()
        assert mocks.execute.call_args.args[1].env is None
        assert mocks.resolve.call_args.kwargs["path"] is None
        assert "VIRTUAL_ENV" not in str(mocks.execute.call_args)


class TestPythonBuiltin:
    """The ``python`` built-in."""

    @pytest.mark.parametrize(
        ("refresh", "skip_overrides"), [(False, False), (True, True), (True, False)]
    )
    def test_namespace(
        self, mocks: Mocks, tmp_path: Path, refresh: bool, skip_overrides: bool
    ) -> None:
        mocks.set_steps(_PYTHON)
        _run(tmp_path, refresh=refresh, skip_overrides=skip_overrides)
        ns = mocks.install_config.from_args.call_args.args[0]
        assert ns.target == tmp_path
        assert ns.source == "local"
        assert ns.local_path == tmp_path
        assert ns.use_sync is True
        assert ns.extras is None
        assert ns.clean is False
        assert ns.check is False
        assert ns.refresh is refresh
        assert ns.skip_overrides is skip_overrides
        mocks.install.assert_called_once_with(
            mocks.install_config.from_args.return_value
        )

    def test_system_exit_becomes_setup_error(
        self, mocks: Mocks, tmp_path: Path
    ) -> None:
        mocks.set_steps(_PYTHON, _argv("never"))
        mocks.install.side_effect = SystemExit(1)
        with pytest.raises(SetupError, match=r"python: install failed \(1\)"):
            _run(tmp_path)
        mocks.execute.assert_not_called()

    def test_system_exit_zero_is_success(self, mocks: Mocks, tmp_path: Path) -> None:
        mocks.set_steps(_PYTHON)
        mocks.install.side_effect = SystemExit(0)
        _run(tmp_path)

    def test_value_error_becomes_setup_error(
        self, mocks: Mocks, tmp_path: Path
    ) -> None:
        mocks.set_steps(_PYTHON)
        mocks.install_config.from_args.side_effect = ValueError("bad pyproject")
        with pytest.raises(SetupError, match="bad pyproject"):
            _run(tmp_path)
        mocks.install.assert_not_called()

    def test_later_steps_get_venv(
        self, mocks: Mocks, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("PATH", "original")
        mocks.set_steps(_PYTHON, _argv("pytest"))
        _run(tmp_path)
        bin_dir = str(get_bin_dir(tmp_path / ".venv"))
        env = mocks.execute.call_args.args[1].env
        assert env["PATH"] == bin_dir + os.pathsep + "original"
        assert env["VIRTUAL_ENV"] == str(tmp_path / ".venv")
        assert mocks.resolve.call_args.kwargs["path"] == env["PATH"]

    def test_steps_before_builtin_get_no_venv(
        self, mocks: Mocks, tmp_path: Path
    ) -> None:
        mocks.set_steps(_argv("before"), _PYTHON)
        _run(tmp_path)
        assert mocks.execute.call_args.args[1].env is None


class TestEnvironment:
    """``UV_GIT_SHALLOW`` defaulting."""

    def test_uv_git_shallow_defaults_to_zero(
        self, mocks: Mocks, tmp_path: Path
    ) -> None:
        mocks.set_steps()
        _run(tmp_path)
        assert os.environ["UV_GIT_SHALLOW"] == "0"

    def test_uv_git_shallow_preserved(
        self, mocks: Mocks, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("UV_GIT_SHALLOW", "1")
        mocks.set_steps()
        _run(tmp_path)
        assert os.environ["UV_GIT_SHALLOW"] == "1"


class TestConfig:
    """Config loading."""

    def test_empty_steps_nothing_to_do(
        self, mocks: Mocks, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        mocks.set_steps()
        with caplog.at_level(logging.INFO, logger=_MOD):
            _run(tmp_path)
        assert "nothing to do" in caplog.text
        mocks.execute.assert_not_called()
        mocks.install.assert_not_called()
        mocks.status.assert_not_called()

    def test_config_value_error_propagates(self, mocks: Mocks, tmp_path: Path) -> None:
        mocks.load.side_effect = ValueError("Invalid [tool.mcp-coder.setup]")
        with pytest.raises(ValueError, match="Invalid"):
            _run(tmp_path)
        mocks.execute.assert_not_called()


class TestChangedFiles:
    """Setup must not change tracked files or create untracked ones."""

    def test_new_untracked_file_fails(self, mocks: Mocks, tmp_path: Path) -> None:
        mocks.set_steps(_argv("tool"))
        mocks.status.side_effect = [
            _status(),
            _status(untracked=["b.txt", "a.lock"], modified=["src/x.py"]),
        ]
        with pytest.raises(
            SetupError, match="Setup changed or created files: a.lock, b.txt, src/x.py"
        ):
            _run(tmp_path)

    def test_already_dirty_file_passes(self, mocks: Mocks, tmp_path: Path) -> None:
        mocks.set_steps(_argv("tool"))
        dirty = _status(staged=["s.py"], modified=["m.py"], untracked=["u.txt"])
        mocks.status.side_effect = [dirty, dirty]
        _run(tmp_path)

    def test_not_a_git_repo_skipped(
        self, mocks: Mocks, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        mocks.set_steps(_argv("tool"))
        mocks.is_repo.return_value = False
        with caplog.at_level(logging.INFO, logger=_MOD):
            _run(tmp_path)
        assert "changed-files check skipped" in caplog.text
        mocks.status.assert_not_called()
        mocks.execute.assert_called_once()

    def test_git_status_failure_fails(self, mocks: Mocks, tmp_path: Path) -> None:
        mocks.set_steps(_argv("tool"))
        mocks.status.return_value = _status(
            success=False, error="git status failed (exit 128)"
        )
        with pytest.raises(SetupError, match=r"git status failed \(exit 128\)"):
            _run(tmp_path)
        mocks.execute.assert_not_called()

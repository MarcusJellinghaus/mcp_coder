"""Run a project's ``[tool.mcp-coder.setup]`` steps (backs ``mcp-coder setup``).

Steps run in order and the first failure stops the run. The ``python``
built-in runs ``install()`` in-process (today's ``mcp-coder install --source
local --use-sync``); every later command step gets the project venv's bin dir
first on ``PATH`` and ``VIRTUAL_ENV``. In a git repository, setup fails when it
changed tracked files or created untracked, non-ignored files.
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from collections.abc import Callable
from pathlib import Path

from ..mcp_workspace_git import get_working_tree_status, is_git_repository
from ..utils.executable import resolve_executable, venv_search_path
from ..utils.setup_config import SetupStep, load_setup_config
from ..utils.subprocess_runner import CommandOptions, execute_subprocess
from . import InstallConfig, install

logger = logging.getLogger(__name__)


class SetupError(Exception):
    """A setup step failed or setup changed files; message is user-facing."""


def _run_python_builtin(project_dir: Path, refresh: bool, skip_overrides: bool) -> None:
    """Run the ``python`` built-in: a local, uv.lock-honoring install.

    Args:
        project_dir: Project root; the venv is ``<project_dir>/.venv``.
        refresh: Passed to install as ``--refresh``.
        skip_overrides: Passed to install as ``--skip-overrides``.

    Raises:
        SetupError: If the install configuration is invalid or install exits
            with a non-zero code.
    """
    args = argparse.Namespace(
        target=project_dir,
        source="local",
        ref="main",
        local_path=project_dir,
        extras=None,
        extra_packages="",
        use_sync=True,
        skip_overrides=skip_overrides,
        refresh=refresh,
        clean=False,
        python=sys.executable,
        check=False,
    )
    try:
        install(InstallConfig.from_args(args))
    except ValueError as exc:
        raise SetupError(f"python: {exc}") from exc
    except SystemExit as exc:
        if exc.code not in (None, 0):
            raise SetupError(f"python: install failed ({exc.code})") from exc


_BUILTINS: dict[str, Callable[[Path, bool, bool], None]] = {
    "python": _run_python_builtin,
}


def _run_argv_step(step: SetupStep, project_dir: Path, overlay: dict[str, str]) -> None:
    """Run one command-line step in the project directory.

    Args:
        step: The step; ``step.argv`` is set.
        project_dir: Working directory, and base for relative ``argv[0]``.
        overlay: Environment entries merged over ``os.environ``; also the
            ``PATH`` used to resolve a bare ``argv[0]``.

    Raises:
        SetupError: If ``argv[0]`` is not found, or the command times out,
            cannot start or exits non-zero.
    """
    label = step.label
    if not step.argv:
        raise SetupError(f"{label}: no command line")
    exe = resolve_executable(step.argv[0], project_dir, path=overlay.get("PATH"))
    if exe is None:
        raise SetupError(f"{label}: {step.argv[0]!r} not found")

    result = execute_subprocess(
        [exe, *step.argv[1:]],
        CommandOptions(
            cwd=str(project_dir),
            timeout_seconds=step.timeout,
            capture_output=False,
            env=overlay or None,
        ),
    )
    if result.timed_out:
        raise SetupError(f"{label}: timed out after {step.timeout}s")
    if result.execution_error:
        raise SetupError(f"{label}: {result.execution_error}")
    if result.return_code != 0:
        raise SetupError(f"{label}: exited with code {result.return_code}")


def _dirty_paths(project_dir: Path) -> set[str] | None:
    """Return the staged, modified and untracked paths of the working tree.

    Args:
        project_dir: Project root.

    Returns:
        Repo-relative paths, or None when ``project_dir`` is not a git
        repository.

    Raises:
        SetupError: If ``git status`` fails in a git repository.
    """
    if not is_git_repository(project_dir):
        logger.info(
            "%s is not a git repository; changed-files check skipped", project_dir
        )
        return None
    status = get_working_tree_status(project_dir)
    if not status["success"]:
        raise SetupError(f"Cannot check for changed files: {status['error']}")
    return set(status["staged"]) | set(status["modified"]) | set(status["untracked"])


def run_setup(project_dir: Path, *, refresh: bool, skip_overrides: bool) -> None:
    """Run [tool.mcp-coder.setup] steps in order.

    Args:
        project_dir: Project root.
        refresh: Forwarded to the ``python`` built-in.
        skip_overrides: Forwarded to the ``python`` built-in.

    Raises:
        ValueError: If the setup configuration is invalid.
        SetupError: If a step fails, git status fails, or setup changed
            tracked files or created untracked ones.
    """  # noqa: DOC502 - ValueError raised by load_setup_config, part of this contract
    os.environ.setdefault("UV_GIT_SHALLOW", "0")
    config = load_setup_config(project_dir)
    if not config.steps:
        logger.info("No setup steps for %s; nothing to do", project_dir)
        return

    before = _dirty_paths(project_dir)
    overlay: dict[str, str] = {}
    total = len(config.steps)
    for index, step in enumerate(config.steps, start=1):
        logger.info("Setup step %d/%d: %s", index, total, step.label)
        if step.builtin is not None:
            _BUILTINS[step.builtin](project_dir, refresh, skip_overrides)
            overlay = {
                "PATH": venv_search_path(project_dir),
                "VIRTUAL_ENV": str(project_dir / ".venv"),
            }
        else:
            _run_argv_step(step, project_dir, overlay)

    if before is not None:
        changed = (_dirty_paths(project_dir) or set()) - before
        if changed:
            raise SetupError(
                "Setup changed or created files: " + ", ".join(sorted(changed))
            )

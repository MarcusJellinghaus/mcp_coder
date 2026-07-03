"""Pure, run-time helpers for the vscodeclaude session launcher.

This module is executed via ``python -m
mcp_coder.workflows.vscodeclaude.session_setup <CWD>`` by the thin launcher.
Step 2 provides only the *pure* building blocks — no ``subprocess`` and no
``main`` — so every helper is directly unit-testable without mocking.
"""

import os
import sys
from pathlib import Path

from .types import SessionSpec

# MCP tool timeout (ms) forwarded to subprocesses. See
# src/mcp_coder/llm/claude_settings.py for the canonical value.
MCP_TIMEOUT_MS = "30000"


def _venv_bin_dir(venv_root: Path) -> Path:
    """Return the venv's executables directory (``Scripts`` win / ``bin`` posix).

    Runtime platform detection lives here alone, so both-platform tests only
    need to monkeypatch ``sys.platform`` at this single point.

    Args:
        venv_root: Root directory of a virtual environment (holds ``pyvenv.cfg``).

    Returns:
        The platform-specific executables subdirectory.
    """
    return venv_root / ("Scripts" if sys.platform == "win32" else "bin")


def _mcp_coder_exe(spec: SessionSpec) -> Path:
    """Return the absolute path to the coordinator's ``mcp-coder`` executable.

    Absolute (not PATH-resolved) to sidestep the Windows ``CreateProcess``
    PATH-lookup gotcha.

    Args:
        spec: The session spec carrying ``mcp_coder_install_path``.

    Returns:
        Absolute path to ``mcp-coder(.exe)`` inside the coordinator venv.
    """
    exe = "mcp-coder.exe" if sys.platform == "win32" else "mcp-coder"
    return _venv_bin_dir(Path(spec.mcp_coder_install_path) / ".venv") / exe


def _coordinator_python(spec: SessionSpec) -> Path:
    """Return the absolute path to the coordinator venv's Python interpreter.

    Args:
        spec: The session spec carrying ``mcp_coder_install_path``.

    Returns:
        Absolute path to ``python(.exe)`` inside the coordinator venv.
    """
    exe = "python.exe" if sys.platform == "win32" else "python"
    return _venv_bin_dir(Path(spec.mcp_coder_install_path) / ".venv") / exe


def build_subprocess_env(spec: SessionSpec, cwd: Path) -> dict[str, str]:
    """Build the environment shared by every subprocess of the session.

    Starts from a full copy of the current environment (preserving
    ``USERPROFILE``/``SystemRoot``/``TEMP`` etc. required for ``.mcp.json``
    interpolation), then overlays the four MCP vars, a PATH prepend
    (coordinator venv bin, then project venv bin), and the pinned
    ``MCP_TIMEOUT`` / ``UV_GIT_SHALLOW`` values.

    Invariant preserved: ``VIRTUAL_ENV == <cwd>/.venv == target``.

    Args:
        spec: The session spec carrying ``mcp_coder_install_path``.
        cwd: The session/project directory (launcher's ``%CD%`` / ``$PWD``).

    Returns:
        A full environment dict with the session overlay applied.
    """
    env = os.environ.copy()
    coder_bin = _venv_bin_dir(Path(spec.mcp_coder_install_path) / ".venv")
    project_venv = cwd / ".venv"
    project_bin = _venv_bin_dir(project_venv)

    env["MCP_CODER_VENV_PATH"] = str(coder_bin)
    env["MCP_CODER_PROJECT_DIR"] = str(cwd)
    env["MCP_CODER_VENV_DIR"] = str(project_venv)
    env["VIRTUAL_ENV"] = str(project_venv)
    env["MCP_TIMEOUT"] = MCP_TIMEOUT_MS
    env["UV_GIT_SHALLOW"] = "0"
    env["PATH"] = (
        str(coder_bin)
        + os.pathsep
        + str(project_bin)
        + os.pathsep
        + env.get("PATH", "")
    )
    return env


def build_install_argv(spec: SessionSpec, cwd: Path) -> list[str]:
    """Build the argv that provisions the project venv via ``install.py``.

    Mirrors the exact flags used by the retired shell templates; appends
    ``--skip-overrides`` iff ``spec.skip_github_install`` is set.

    Args:
        spec: The session spec carrying the resolved ``install_script_path``.
        cwd: The session/project directory.

    Returns:
        The argv list to invoke ``install.py`` with the coordinator Python.
    """
    argv = [
        str(_coordinator_python(spec)),
        spec.install_script_path,
        str(cwd),
        "--source",
        "local",
        "--local-path",
        str(cwd),
        "--extras",
        "dev",
        "--use-sync",
        "--refresh",
    ]
    if spec.skip_github_install:
        argv.append("--skip-overrides")
    return argv


def build_step_argv(
    spec: SessionSpec,
    command: str,
    *,
    session_id: str | None,
    issue_number: int | None,
) -> list[str]:
    """Build the ``mcp-coder prompt`` argv for one automated step.

    A ``session_id`` of ``None`` means the first step: it captures the session
    ID (``--output-format session-id``) and prompts with ``"<cmd> <issue>"``.
    A non-``None`` ``session_id`` resumes an existing session and prompts with
    the bare ``<cmd>``.

    Args:
        spec: The session spec (absolute exe, ``mcp_config``, ``timeout``).
        command: The command text for this step.
        session_id: Existing session ID to resume, or ``None`` for the first step.
        issue_number: The issue number appended to the first-step prompt.

    Returns:
        The argv list for ``mcp-coder prompt``.
    """
    prompt = f"{command} {issue_number}" if session_id is None else command
    argv = [str(_mcp_coder_exe(spec)), "prompt", prompt, "--llm-method", "claude"]
    if session_id is None:
        argv += ["--output-format", "session-id"]
    else:
        argv += ["--session-id", session_id]
    argv += ["--mcp-config", spec.mcp_config, "--timeout", str(spec.timeout)]
    return argv


def build_claude_argv(
    spec: SessionSpec,
    *,
    prompt: str | None = None,
    session_id: str | None = None,
) -> list[str]:
    """Build the interactive ``claude`` argv.

    ``claude`` stays PATH-resolved (global npm CLI). ``--strict-mcp-config`` is
    always present. With no ``prompt`` the call is bare (intervention). With a
    ``session_id`` the prior conversation is resumed via ``--resume``.

    Args:
        spec: The session spec carrying ``mcp_config``.
        prompt: Prompt text, or ``None`` for a bare interactive launch.
        session_id: Session ID to resume, or ``None``.

    Returns:
        The argv list for ``claude``.
    """
    argv = ["claude", "--mcp-config", spec.mcp_config, "--strict-mcp-config"]
    if prompt is None:
        return argv
    if session_id:
        argv += ["--resume", session_id]
    return argv + [prompt]


def render_banner(spec: SessionSpec) -> str:
    """Render the session banner (plus intervention warning where applicable).

    Reuses ``BANNER_TEMPLATE`` and, for intervention specs, appends the
    ``INTERVENTION_WARNING`` block — restoring parity with the old
    ``INTERVENTION_SCRIPT_*`` templates. Both templates are imported inside the
    function to keep the top-level import light.

    Args:
        spec: The session spec supplying the banner fields.

    Returns:
        The banner text ready to print to the UTF-8-forced terminal.
    """
    from .templates import BANNER_TEMPLATE, INTERVENTION_WARNING

    banner = BANNER_TEMPLATE.format(
        emoji=spec.emoji,
        issue_number=spec.issue_number,
        title=spec.title,
        repo=spec.repo,
        status=spec.status,
        issue_url=spec.issue_url,
    )
    if spec.is_intervention:
        banner += INTERVENTION_WARNING
    return banner

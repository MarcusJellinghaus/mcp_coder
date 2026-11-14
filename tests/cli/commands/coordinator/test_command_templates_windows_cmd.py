"""Run the rendered Windows templates through cmd.exe with a stub ``mcp-coder``."""

import os
import sys
from pathlib import Path

import pytest

from mcp_coder.cli.commands.coordinator import (
    CREATE_PLAN_COMMAND_WINDOWS,
    CREATE_PR_COMMAND_WINDOWS,
    DEFAULT_TEST_COMMAND_WINDOWS,
    FIX_CI_COMMAND_WINDOWS,
    FIX_CONFLICT_COMMAND_WINDOWS,
    IMPLEMENT_COMMAND_WINDOWS,
    REVIEW_IMPLEMENTATION_COMMAND_WINDOWS,
    REVIEW_PLAN_COMMAND_WINDOWS,
)
from mcp_coder.utils.subprocess_runner import CommandOptions, execute_subprocess

pytestmark = pytest.mark.skipif(
    sys.platform != "win32", reason="runs the templates through cmd.exe"
)

WORKFLOWS = [  # (template, command) — the args after "--log-level INFO"
    pytest.param(CREATE_PLAN_COMMAND_WINDOWS, "create-plan 42", id="create-plan"),
    pytest.param(IMPLEMENT_COMMAND_WINDOWS, "implement", id="implement"),
    pytest.param(CREATE_PR_COMMAND_WINDOWS, "create-pr", id="create-pr"),
    pytest.param(REVIEW_PLAN_COMMAND_WINDOWS, "review-plan", id="review-plan"),
    pytest.param(
        REVIEW_IMPLEMENTATION_COMMAND_WINDOWS,
        "review-implementation",
        id="review-implementation",
    ),
    pytest.param(FIX_CI_COMMAND_WINDOWS, "fix-ci", id="fix-ci"),
    pytest.param(FIX_CONFLICT_COMMAND_WINDOWS, "fix-conflict", id="fix-conflict"),
]

STUB = """@echo off
>>"{log}" echo ARGS=%*
>>"{log}" echo VENV=%VIRTUAL_ENV%
if "%1"=="setup" exit /b {setup_rc}
exit /b 0
"""


def _run(
    tmp_path: Path, template: str, *, setup_rc: int, has_venv: bool
) -> tuple[int, list[tuple[str, str]]]:
    """Run the rendered template through cmd.exe; return (exit code, stub calls as (args, venv))."""
    workspace = tmp_path / "ws"
    (workspace / "repo").mkdir(parents=True)
    # VENV_BASE_DIR is also the cwd: cmd searches the cwd first, so it holds no mcp-coder
    venv_base = tmp_path / "venv_base"
    venv_base.mkdir()
    if has_venv:
        scripts = workspace / "repo" / ".venv" / "Scripts"
        scripts.mkdir(parents=True)
        (scripts / "python.exe").touch()
    stub_dir = tmp_path / "stub"
    stub_dir.mkdir()
    log = tmp_path / "stub.log"
    (stub_dir / "mcp-coder.cmd").write_text(
        STUB.format(log=log, setup_rc=setup_rc), newline="\r\n"
    )

    # A .cmd invoked without `call` never returns; production runs mcp-coder.exe.
    script = template.format(log_level="INFO", issue_number=42, branch_name="b")
    bat = tmp_path / "run.bat"
    bat.write_text(script.replace("mcp-coder ", "call mcp-coder "), newline="\r\n")

    result = execute_subprocess(
        [os.environ["COMSPEC"], "/c", str(bat)],
        CommandOptions(
            cwd=str(venv_base),
            env={
                "WORKSPACE": str(workspace),
                "VENV_BASE_DIR": str(venv_base),
                "PATH": str(stub_dir) + os.pathsep + os.environ["PATH"],
            },
            # pytest usually runs in a venv; the wrapper clears it in production
            env_remove=["VIRTUAL_ENV"],
            timeout_seconds=60,
        ),
    )

    lines = log.read_text().splitlines() if log.exists() else []
    calls = [
        (args.removeprefix("ARGS="), venv.removeprefix("VENV="))
        for args, venv in zip(lines[::2], lines[1::2], strict=True)
    ]
    return result.return_code, calls


@pytest.mark.parametrize("has_venv", [True, False], ids=["venv", "no-venv"])
@pytest.mark.parametrize("template, command", WORKFLOWS)
def test_setup_succeeds(
    tmp_path: Path, template: str, command: str, has_venv: bool
) -> None:
    """Setup passes: the command runs, with VIRTUAL_ENV only when the venv exists."""
    return_code, calls = _run(tmp_path, template, setup_rc=0, has_venv=has_venv)

    workspace = tmp_path / "ws"
    assert calls[0][0] == f"setup --project-dir {workspace}\\repo --refresh"
    command_calls = [
        call for call in calls if call[0].startswith(f"--log-level INFO {command} ")
    ]
    assert len(command_calls) == 1
    expected_venv = f"{workspace}\\repo\\.venv" if has_venv else ""
    assert command_calls[0][1] == expected_venv
    assert return_code == 0


@pytest.mark.parametrize(
    "template, expected_calls",
    [
        pytest.param(param.values[0], ["setup", "gh-tool"], id=param.id)
        for param in WORKFLOWS
    ]
    + [pytest.param(DEFAULT_TEST_COMMAND_WINDOWS, ["setup"], id="test-command")],
)
def test_setup_fails(tmp_path: Path, template: str, expected_calls: list[str]) -> None:
    """Setup fails: workflows run the watchdog, nothing reaches the command, exit 1."""
    return_code, calls = _run(tmp_path, template, setup_rc=1, has_venv=True)

    assert return_code == 1
    assert [args.split()[0] for args, _ in calls] == expected_calls

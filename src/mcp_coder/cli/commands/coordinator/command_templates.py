"""Command template strings for coordinator CLI operations.

This module centralizes all command templates used by the coordinator package:
- Test command templates (for coordinator test command)
- Workflow command templates (for coordinator run workflows)

All templates support format string placeholders:
- {log_level}: Logging level to use (debug, info, warning, error)
- {issue_number}: GitHub issue number (for create-plan workflows)
- {branch_name}: Git branch name (for implement and create-pr workflows)
"""

# Default test command for coordinator integration tests
# This comprehensive script verifies the complete environment setup
DEFAULT_TEST_COMMAND: str = """# Tool verification
which mcp-coder && mcp-coder --version
which mcp-tools-py && mcp-tools-py --help
which mcp-workspace && mcp-workspace --help
mcp-coder verify
export DISABLE_AUTOUPDATER=1
export MCP_TIMEOUT=30000
# Environment setup
export MCP_CODER_PROJECT_DIR='/workspace/repo'
export MCP_CODER_VENV_DIR='/workspace/.venv'
# Claude CLI verification
which claude
claude --mcp-config .mcp.json --strict-mcp-config mcp list
claude --mcp-config .mcp.json --strict-mcp-config -p "What is 1 + 1?"
# MCP Coder functionality test
mcp-coder --log-level {log_level} prompt "Which MCP server can you use?"
mcp-coder --log-level {log_level} prompt --timeout 300 "For testing, please create a file, edit it, read it to verify, delete it, and tell me whether these actions worked well with the MCP server." --project-dir /workspace/repo --mcp-config .mcp.json
# Project environment verification
if [ -f .venv/bin/activate ]; then source .venv/bin/activate; fi
which mcp-coder && mcp-coder --version
echo "archive after execution ======================================="
ls -la .mcp-coder/create_plan_sessions
ls -la logs
"""

# Windows equivalent of DEFAULT_TEST_COMMAND
# Note: Using raw string (r""") for cleaner Windows path handling
DEFAULT_TEST_COMMAND_WINDOWS: str = r"""@echo ON

echo current WORKSPACE directory===================================
cd %WORKSPACE%

echo switch to python execution environment =====================
cd %VENV_BASE_DIR%
cd
dir

echo python environment ================================
if "%VENV_BASE_DIR%"=="" (
    echo ERROR: VENV_BASE_DIR environment variable not set
    exit /b 1
)

mcp-coder setup --project-dir %WORKSPACE%\repo --refresh
if %ERRORLEVEL% NEQ 0 (
exit /b 1
)
if exist "%WORKSPACE%\repo\.venv\Scripts\python.exe" set "VIRTUAL_ENV=%WORKSPACE%\repo\.venv"

echo %VIRTUAL_ENV%
where python
python --version
pip list

echo Tools in current environment ===================
claude --version
where mcp-coder
mcp-coder --version
where mcp-tools-py
mcp-tools-py --version
where mcp-workspace
mcp-workspace --version

set DISABLE_AUTOUPDATER=1
set MCP_TIMEOUT=30000

echo llm verification =====================================
mcp-coder verify
claude --mcp-config .mcp.json --strict-mcp-config mcp list 
claude --mcp-config .mcp.json --strict-mcp-config -p "What is 1 + 1?"

mcp-coder --log-level debug prompt "What is 1 + 1?"
mcp-coder --log-level {log_level} prompt "Which MCP server can you use?"
mcp-coder --log-level {log_level} prompt --timeout 300 "For testing, please create a file, edit it, read it to verify, delete it, and tell me whether these actions worked well with the MCP server." --project-dir %WORKSPACE%\repo --mcp-config .mcp.json

echo archive after execution =======================================
dir .mcp-coder\create_plan_sessions
dir logs
"""

# Template selection mapping for execute_coordinator_test
TEST_COMMAND_TEMPLATES: dict[str, str] = {
    "windows": DEFAULT_TEST_COMMAND_WINDOWS,
    "linux": DEFAULT_TEST_COMMAND,
}

# Command templates for Jenkins workflows - Linux
# IMPORTANT: These templates assume Jenkins workspace clones repository to /workspace/repo
# The --project-dir parameter must match the Jenkins workspace structure
# All templates follow the pattern:
#   1. Checkout appropriate branch (main for planning, feature branch for implementation/PR)
#   2. Pull latest code (implement, fix-ci, fix-conflict, review-implementation
#      then run `mcp-coder setup`; see _linux_setup_template)
#   3. Verify tool versions
#   4. Execute mcp-coder command
#   5. Capture exit code and run watchdog set-status
#   6. Archive logs
#   7. Exit with captured RC
#
# Silent-death recovery watchdog (see issue #713)
#
# After the main mcp-coder command, each template captures $RC / %ERRORLEVEL%
# and runs a conditional set-status that only fires if the issue is still at
# the in-progress label (--from-status). This rescues issues stuck by a
# silent process death where Python cleanup never ran.
#
# Recovery matrix:
#   Clean success        → label already past in-progress → watchdog no-ops
#   Graceful failure     → Python set a specific failure label → watchdog no-ops
#   Silent death (#710)  → issue still at in-progress label → watchdog rescues
#   Hard kill of shell   → watchdog never runs → not recoverable (out of scope)
#
# The watchdog always runs (not gated on exit code). The original exit code
# is re-emitted via exit $RC / exit /b %RC% so Jenkins sees the real outcome.
CREATE_PLAN_COMMAND_TEMPLATE: str = """git checkout main
git pull
export DISABLE_AUTOUPDATER=1
export MCP_TIMEOUT=30000
which mcp-coder && mcp-coder --version
which claude && claude --version
mcp-coder --log-level {log_level} create-plan {issue_number} --project-dir /workspace/repo --mcp-config .mcp.json
RC=$?
echo RC=$RC

mcp-coder gh-tool set-status status-03f:planning-failed --from-status status-03:planning --issue {issue_number} --project-dir /workspace/repo --force || true

echo "archive after execution ======================================="
ls -la .mcp-coder/create_plan_sessions
ls -la logs

exit $RC
"""


def _watchdog(failed: str, current: str) -> str:
    """Return the watchdog set-status line for a workflow without --issue."""
    return (
        f"mcp-coder gh-tool set-status {failed} --from-status {current} "
        "--project-dir /workspace/repo --force || true"
    )


def _linux_setup_template(
    command: str, failed: str, current: str, *, archive_plan_sessions: bool = True
) -> str:
    """Return the Linux template for a workflow that needs the project set up.

    `mcp-coder setup` runs after `git pull`; on failure the watchdog moves the
    issue to its failed label and the script exits 1. The VIRTUAL_ENV line then
    points mcp-tools-py checks at the project venv. The setup and venv lines
    contain no $, braces or backticks (str.format and AutoRunner's outer
    bash -c), and use if blocks because the executor runs under set -e.
    """
    watchdog = _watchdog(failed, current)
    plan_sessions = (
        "ls -la .mcp-coder/create_plan_sessions\n" if archive_plan_sessions else ""
    )
    return (
        "git checkout {branch_name}\n"
        "git pull\n"
        "if ! mcp-coder setup --project-dir /workspace/repo; then\n"
        f"{watchdog}\n"
        "exit 1\n"
        "fi\n"
        "if [ -x .venv/bin/python ]; then export VIRTUAL_ENV=/workspace/repo/.venv; fi\n"
        "export DISABLE_AUTOUPDATER=1\n"
        "export MCP_TIMEOUT=30000\n"
        "which mcp-coder && mcp-coder --version\n"
        "which claude && claude --version\n"
        f"mcp-coder --log-level {{log_level}} {command} "
        "--project-dir /workspace/repo --mcp-config .mcp.json\n"
        "RC=$?\n"
        "echo RC=$RC\n"
        "\n"
        f"{watchdog}\n"
        "\n"
        'echo "archive after execution ======================================="\n'
        f"{plan_sessions}"
        "ls -la logs\n"
        "\n"
        "exit $RC\n"
    )


IMPLEMENT_COMMAND_TEMPLATE: str = _linux_setup_template(
    "implement", "status-06f:implementing-failed", "status-06:implementing"
)

CREATE_PR_COMMAND_TEMPLATE: str = """git checkout {branch_name}
git pull
export DISABLE_AUTOUPDATER=1
export MCP_TIMEOUT=30000
which mcp-coder && mcp-coder --version
which claude && claude --version
mcp-coder --log-level {log_level} create-pr --project-dir /workspace/repo --mcp-config .mcp.json
RC=$?
echo RC=$RC

mcp-coder gh-tool set-status status-09f:pr-creating-failed --from-status status-09:pr-creating --project-dir /workspace/repo --force || true

echo "archive after execution ======================================="
ls -la .mcp-coder/create_plan_sessions
ls -la logs

exit $RC
"""

REVIEW_PLAN_COMMAND_TEMPLATE: str = """git checkout {branch_name}
git pull
export DISABLE_AUTOUPDATER=1
export MCP_TIMEOUT=30000
which mcp-coder && mcp-coder --version
which claude && claude --version
mcp-coder --log-level {log_level} review-plan --project-dir /workspace/repo --mcp-config .mcp.json
RC=$?
echo RC=$RC

mcp-coder gh-tool set-status status-14f:plan-review-failed --from-status status-14i:plan-reviewing --project-dir /workspace/repo --force || true

echo "archive after execution ======================================="
ls -la .mcp-coder/create_plan_sessions
ls -la logs

exit $RC
"""

REVIEW_IMPLEMENTATION_COMMAND_TEMPLATE: str = _linux_setup_template(
    "review-implementation",
    "status-17f:code-review-failed",
    "status-17i:code-reviewing",
)

FIX_CI_COMMAND_TEMPLATE: str = _linux_setup_template(
    "fix-ci", "status-83:ci-fix-failed", "status-82:fixing-ci"
)

FIX_CONFLICT_COMMAND_TEMPLATE: str = _linux_setup_template(
    "fix-conflict",
    "status-73:merge-conflict-failed",
    "status-72:fixing-merge-conflict",
    archive_plan_sessions=False,
)

# Windows workflow command templates
# Built by _windows_template: each runs `mcp-coder setup` before the command,
# with the same watchdog on setup failure and after the command.


def _windows_template(
    command: str,
    failed: str,
    current: str,
    *,
    issue_flag: bool = False,
    archive_plan_sessions: bool = True,
) -> str:
    """Return the Windows template for a workflow.

    `mcp-coder setup` runs before the command; on failure the watchdog moves the
    issue to its failed label and the script exits 1. VIRTUAL_ENV is set only
    when the project venv has an interpreter. Block bodies are not indented and
    use a literal `exit /b 1` (%ERRORLEVEL% would expand when the block is parsed).
    """
    issue = " --issue {issue_number}" if issue_flag else ""
    watchdog = (
        f"mcp-coder gh-tool set-status {failed} --from-status {current}{issue} "
        r"--project-dir %WORKSPACE%\repo --force"
    )
    plan_sessions = (
        r"dir .mcp-coder\create_plan_sessions" + "\n" if archive_plan_sessions else ""
    )
    return rf"""@echo ON

echo current WORKSPACE directory===================================
cd %WORKSPACE%

echo switch to python execution environment =====================
cd %VENV_BASE_DIR%

echo python environment ================================
if "%VENV_BASE_DIR%"=="" (
    echo ERROR: VENV_BASE_DIR environment variable not set
    exit /b 1
)

mcp-coder setup --project-dir %WORKSPACE%\repo --refresh
if %ERRORLEVEL% NEQ 0 (
{watchdog}
exit /b 1
)
if exist "%WORKSPACE%\repo\.venv\Scripts\python.exe" set "VIRTUAL_ENV=%WORKSPACE%\repo\.venv"

set DISABLE_AUTOUPDATER=1
set MCP_TIMEOUT=30000

echo command execution  =====================================
mcp-coder --log-level {{log_level}} {command} --project-dir %WORKSPACE%\repo --mcp-config .mcp.json
set RC=%ERRORLEVEL%
echo RC=%RC%

{watchdog}

echo archive after execution =======================================
{plan_sessions}dir logs

exit /b %RC%
"""


CREATE_PLAN_COMMAND_WINDOWS: str = _windows_template(
    "create-plan {issue_number}",
    "status-03f:planning-failed",
    "status-03:planning",
    issue_flag=True,
)

IMPLEMENT_COMMAND_WINDOWS: str = _windows_template(
    "implement", "status-06f:implementing-failed", "status-06:implementing"
)

CREATE_PR_COMMAND_WINDOWS: str = _windows_template(
    "create-pr", "status-09f:pr-creating-failed", "status-09:pr-creating"
)

REVIEW_PLAN_COMMAND_WINDOWS: str = _windows_template(
    "review-plan", "status-14f:plan-review-failed", "status-14i:plan-reviewing"
)

REVIEW_IMPLEMENTATION_COMMAND_WINDOWS: str = _windows_template(
    "review-implementation",
    "status-17f:code-review-failed",
    "status-17i:code-reviewing",
)

FIX_CI_COMMAND_WINDOWS: str = _windows_template(
    "fix-ci", "status-83:ci-fix-failed", "status-82:fixing-ci"
)

FIX_CONFLICT_COMMAND_WINDOWS: str = _windows_template(
    "fix-conflict",
    "status-73:merge-conflict-failed",
    "status-72:fixing-merge-conflict",
    archive_plan_sessions=False,
)

# Data-driven workflow dispatch table.
# Maps a workflow name to its (linux_template, windows_template) pair so the
# coordinator can select templates by lookup instead of mirrored if/elif ladders.
# An unknown workflow raises KeyError at dispatch instead of silently misrouting.
WORKFLOW_TEMPLATES: dict[str, tuple[str, str]] = {
    # workflow name -> (linux_template, windows_template)
    "create-plan": (CREATE_PLAN_COMMAND_TEMPLATE, CREATE_PLAN_COMMAND_WINDOWS),
    "implement": (IMPLEMENT_COMMAND_TEMPLATE, IMPLEMENT_COMMAND_WINDOWS),
    "create-pr": (CREATE_PR_COMMAND_TEMPLATE, CREATE_PR_COMMAND_WINDOWS),
    "review-plan": (REVIEW_PLAN_COMMAND_TEMPLATE, REVIEW_PLAN_COMMAND_WINDOWS),
    "review-implementation": (
        REVIEW_IMPLEMENTATION_COMMAND_TEMPLATE,
        REVIEW_IMPLEMENTATION_COMMAND_WINDOWS,
    ),
    "fix-conflict": (FIX_CONFLICT_COMMAND_TEMPLATE, FIX_CONFLICT_COMMAND_WINDOWS),
    "fix-ci": (FIX_CI_COMMAND_TEMPLATE, FIX_CI_COMMAND_WINDOWS),
}

# Priority order for processing issues (highest to lowest).
# Each review step sits just below the stage it unblocks: 08 -> 17 -> 05 -> 14 -> 02.
PRIORITY_ORDER: list[str] = [
    "status-08:ready-pr",  # create-pr (closest to done)
    "status-17:code-review-bot",  # review-implementation
    "status-05:plan-ready",  # implement
    "status-14:plan-review-bot",  # review-plan
    "status-02:awaiting-planning",  # create-plan (furthest from done)
]

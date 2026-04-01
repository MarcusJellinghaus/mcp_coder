"""Workspace setup for vscodeclaude feature.

Handles git operations, folder creation, and file generation.
"""

import logging
import platform
import shutil
import stat
import sys
import tomllib
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Any

from ...utils.git_operations import checkout_branch, fetch_remote
from ...utils.subprocess_runner import (
    CalledProcessError,
    CommandOptions,
    execute_subprocess,
)
from .config import get_vscodeclaude_config, sanitize_folder_name
from .helpers import load_to_be_deleted
from .types import DEFAULT_PROMPT_TIMEOUT

logger = logging.getLogger(__name__)


def get_mcp_coder_install_path() -> Path | None:
    """Get the mcp-coder installation directory path.

    This determines where mcp-coder is installed so the startup script
    can find the executable, separate from MCP config variables.

    Returns:
        Path to mcp-coder installation directory, or None if not found
    """
    try:
        # Get the path where this module is located
        current_file = Path(__file__).resolve()
        logger.debug(f"Starting mcp-coder install path search from: {current_file}")

        # This file is at: /path/to/project/src/mcp_coder/workflows/vscodeclaude/workspace.py
        # Go up to find the project root (where .venv would be)
        # Start from src/mcp_coder level
        current_path = current_file.parent.parent.parent.parent
        logger.debug(f"Initial search path: {current_path}")

        # Look for indicators of the project root
        for i in range(5):  # Limit search depth
            logger.debug(f"Checking path {i+1}/5: {current_path}")
            if (current_path / ".venv").exists() or (
                current_path / "pyproject.toml"
            ).exists():
                logger.info(f"Found mcp-coder installation directory: {current_path}")
                return current_path
            current_path = current_path.parent

        # Fallback: try to find venv in sys.executable path
        logger.debug(
            f"Primary search failed, trying sys.executable fallback: {sys.executable}"
        )
        if sys.executable:
            venv_path = Path(
                sys.executable
            ).parent.parent  # executable is in venv/Scripts or venv/bin
            logger.debug(f"Checking venv path: {venv_path}")
            if venv_path.name == ".venv":
                install_path = venv_path.parent
                logger.info(
                    f"Found mcp-coder installation directory via sys.executable: {install_path}"
                )
                return install_path

        logger.warning("Could not determine mcp-coder installation directory")
        return None
    except (
        Exception
    ) as e:  # pylint: disable=broad-exception-caught  # TODO: narrow exception type
        logger.error(f"Error determining mcp-coder installation path: {e}")
        return None


def _remove_readonly(
    func: Callable[[str], None],
    path: str,
    excinfo: tuple[type[BaseException], BaseException, Any],
) -> None:
    """Error handler for shutil.rmtree on Windows.

    Handles read-only files by clearing the read-only flag and retrying.
    This is needed because git pack files are often marked read-only on Windows.

    Args:
        func: The function that raised the error (e.g., os.unlink)
        path: The path being processed
        excinfo: Exception info tuple (type, value, traceback)

    Raises:
        PermissionError: If file cannot be deleted even after clearing read-only flag,
            with a helpful message about closing applications that may have the file open.
    """
    import os

    exc_type, exc_value, _ = excinfo
    logger.debug(
        "rmtree error on '%s': %s(%s)",
        path,
        exc_type.__name__,
        exc_value,
    )

    # Check if it's a permission/access error (use issubclass for robustness)
    # OSError covers PermissionError and other OS-level errors on Windows
    if issubclass(exc_type, OSError):
        try:
            # Clear the read-only flag and retry
            logger.debug("Clearing read-only flag on '%s'", path)
            os.chmod(path, stat.S_IWRITE)
            func(path)
            logger.debug(
                "Successfully deleted '%s' after clearing read-only flag", path
            )
        except OSError as e:
            # File is likely locked by another process
            logger.debug(
                "Still cannot delete '%s' after clearing read-only: %s", path, e
            )
            raise PermissionError(
                f"Cannot delete '{path}': file may be locked by another process. "
                "Please close VS Code, any git GUIs, or other applications that may "
                "have this repository open, then try again."
            ) from e
    else:
        raise exc_value


def get_working_folder_path(
    workspace_base: str,
    repo_name: str,
    issue_number: int,
) -> Path:
    """Get full path for working folder.

    If the base name exists on disk or is in .to_be_deleted, tries
    suffixes -folder2 through -folder9. Raises ValueError if all
    slots are exhausted.

    Args:
        workspace_base: Base directory from config
        repo_name: Repository short name (sanitized)
        issue_number: GitHub issue number

    Returns:
        Path like: workspace_base/mcp-coder_123

    Raises:
        ValueError: If all folder slots (base + folder2-9) are exhausted.
    """
    sanitized_repo = sanitize_folder_name(repo_name)
    base_name = f"{sanitized_repo}_{issue_number}"
    to_be_deleted = load_to_be_deleted(workspace_base)
    base_path = Path(workspace_base)

    # Try base name first
    if not (base_path / base_name).exists() and base_name not in to_be_deleted:
        return base_path / base_name

    # Try suffixes -folder2 through -folder9
    for i in range(2, 10):
        candidate = f"{base_name}-folder{i}"
        if not (base_path / candidate).exists() and candidate not in to_be_deleted:
            return base_path / candidate

    raise ValueError(f"All folder slots exhausted for {base_name} (max: -folder9)")


def create_working_folder(folder_path: Path) -> bool:
    """Create working folder if it doesn't exist.

    Args:
        folder_path: Full path to create

    Returns:
        True if folder was newly created, False if it already existed.
    """
    if folder_path.exists():
        return False
    folder_path.mkdir(parents=True, exist_ok=True)
    return True


def setup_git_repo(
    folder_path: Path,
    repo_url: str,
    branch_name: str | None,
) -> None:
    """Clone repo or checkout branch and pull.

    Args:
        folder_path: Working folder path
        repo_url: Git clone URL
        branch_name: Branch to checkout (None = use main)

    Steps:
    1. If folder empty: git clone
    2. If folder has .git: checkout branch, pull
    3. Uses system git credentials
    4. Logs progress using logger.info()

    Raises:
        CalledProcessError: If git command fails
        ValueError: If folder exists with content but is not a git repository.
    """
    # Check if folder is empty or doesn't have .git
    is_empty = not any(folder_path.iterdir()) if folder_path.exists() else True
    has_git = (folder_path / ".git").exists()

    # Validate existing git repo is functional
    git_is_valid = False
    if has_git:
        try:
            options = CommandOptions(cwd=str(folder_path))
            result = execute_subprocess(
                ["git", "rev-parse", "--is-inside-work-tree"],
                options,
            )
            git_is_valid = result.return_code == 0
        except Exception:
            git_is_valid = False

        if not git_is_valid:
            # Corrupted git repo - delete and re-clone
            logger.warning(
                "Corrupted git repository at %s, deleting and re-cloning",
                folder_path,
            )
            shutil.rmtree(
                folder_path, onerror=_remove_readonly
            )  # pylint: disable=deprecated-argument  # onexc requires Python 3.12+
            folder_path.mkdir(parents=True, exist_ok=True)
            is_empty = True
            has_git = False

    if is_empty:
        # Clone into folder
        logger.info("Cloning %s into %s", repo_url, folder_path)
        clone_options = CommandOptions(check=True)
        execute_subprocess(
            ["git", "clone", repo_url, str(folder_path)],
            clone_options,
        )
    elif not has_git:
        # Folder has content but no .git - error
        raise ValueError(
            f"Folder {folder_path} exists with content but is not a git repository"
        )

    # Checkout and pull
    branch = branch_name or "main"
    logger.info("Checking out branch %s", branch)

    # Use git operations utility to checkout branch (handles remote tracking)
    if not checkout_branch(branch, folder_path):
        raise CalledProcessError(
            returncode=1,
            cmd=["git", "checkout", branch],
            output=f"Failed to checkout branch '{branch}'",
        )

    # Fetch and pull latest changes
    logger.info("Pulling latest changes")
    if not fetch_remote(folder_path):
        raise CalledProcessError(
            returncode=1,
            cmd=["git", "fetch"],
            output="Failed to fetch from origin",
        )

    pull_options = CommandOptions(cwd=str(folder_path), check=True)
    execute_subprocess(
        ["git", "pull"],
        pull_options,
    )


def validate_mcp_json(folder_path: Path) -> None:
    """Validate .mcp.json exists in repo.

    Args:
        folder_path: Working folder path

    Raises:
        FileNotFoundError: If .mcp.json missing
    """
    mcp_json_path = folder_path / ".mcp.json"
    if not mcp_json_path.exists():
        raise FileNotFoundError(
            f".mcp.json not found in {folder_path}. "
            "This file is required for Claude Code integration."
        )


def validate_setup_commands(commands: list[str]) -> None:
    """Validate that setup commands exist in PATH.

    Args:
        commands: List of shell commands to validate

    Raises:
        FileNotFoundError: If any command not found in PATH
    """
    for command in commands:
        # Extract the executable (first word) from the command
        executable = command.split()[0] if command.strip() else ""
        if not executable:
            continue

        # Check if executable exists in PATH
        if shutil.which(executable) is None:
            raise FileNotFoundError(
                f"Command '{executable}' not found in PATH. "
                f"Full command: '{command}'"
            )


def run_setup_commands(
    folder_path: Path,
    commands: list[str],
) -> None:
    """Run platform-specific setup commands.

    Args:
        folder_path: Working directory for commands
        commands: List of shell commands to run

    Logs progress for each command using logger.info().
    """
    for command in commands:
        logger.info("Running: %s", command)
        options = CommandOptions(cwd=str(folder_path), check=True, shell=True)
        execute_subprocess(
            [command],  # Shell commands passed as single-element list with shell=True
            options,
        )


def update_gitignore(folder_path: Path) -> None:
    """Append vscodeclaude entries to .gitignore.

    Args:
        folder_path: Working folder path

    Idempotent: won't duplicate entries.
    """
    from .templates import GITIGNORE_ENTRY

    gitignore_path = folder_path / ".gitignore"

    # Read existing content
    existing_content = ""
    if gitignore_path.exists():
        existing_content = gitignore_path.read_text(encoding="utf-8")

    # Check if already present
    if ".vscodeclaude_status.txt" in existing_content:
        return

    # Append entry
    with gitignore_path.open("a", encoding="utf-8") as f:
        f.write(GITIGNORE_ENTRY)


def create_workspace_file(
    workspace_base: str,
    folder_name: str,
    issue_number: int,
    issue_title: str,
    status: str,
    repo_name: str,
) -> Path:
    """Create .code-workspace file in workspace_base.

    Args:
        workspace_base: Base directory for workspace files
        folder_name: Working folder name (e.g., "mcp-coder_123")
        issue_number: GitHub issue number
        issue_title: Issue title for window title
        status: Status label for window title
        repo_name: Repo short name for window title

    Returns:
        Path to created workspace file
    """
    from .templates import WORKSPACE_FILE_TEMPLATE

    # Truncate title if too long
    title_short = issue_title[:30] + "..." if len(issue_title) > 30 else issue_title
    config = get_vscodeclaude_config(status)
    stage_short = config["stage_short"] if config else status[:6]

    # Format the workspace file
    content = WORKSPACE_FILE_TEMPLATE.format(
        folder_path=f"./{folder_name}",
        issue_number=issue_number,
        stage_short=stage_short,
        title_short=title_short,
        repo_name=repo_name,
    )

    # Write to workspace_base
    workspace_file = Path(workspace_base) / f"{folder_name}.code-workspace"
    workspace_file.write_text(content, encoding="utf-8")

    return workspace_file


def _escape_batch_title(text: str) -> str:
    """Escape special characters in text for Windows batch echo commands.

    Prevents shell injection when issue titles contain characters like >
    that cmd.exe would otherwise interpret as redirection operators.
    Order matters: ^ must be escaped first to avoid double-escaping.

    Returns:
        Text with special batch characters escaped.
    """
    for char in ("^", "&", "|", "<", ">"):
        text = text.replace(char, f"^{char}")
    return text


def _build_github_install_section(folder_path: Path) -> str:
    """Read [tool.mcp-coder.from-github] from pyproject.toml and build install commands.

    Args:
        folder_path: Path to the cloned repo containing pyproject.toml.

    Returns:
        Batch script lines to inject, or empty string if no packages configured.
    """
    pyproject_path = folder_path / "pyproject.toml"
    if not pyproject_path.exists():
        logger.warning(
            "pyproject.toml not found at %s, skipping GitHub installs", folder_path
        )
        return ""

    with pyproject_path.open("rb") as f:
        config = tomllib.load(f)

    gh_config = config.get("tool", {}).get("mcp-coder", {}).get("from-github", {})
    packages = gh_config.get("packages", [])
    packages_no_deps = gh_config.get("packages-no-deps", [])

    if not packages and not packages_no_deps:
        logger.info("No GitHub override packages configured in pyproject.toml")
        return ""

    lines = ["", "REM === GitHub override installs ==="]
    if packages:
        quoted = " ".join(f'"{p}"' for p in packages)
        lines.append(f"uv pip install {quoted}")
    if packages_no_deps:
        quoted = " ".join(f'"{p}"' for p in packages_no_deps)
        lines.append(f"uv pip install --no-deps {quoted}")
    lines.append("uv pip install -e . --no-deps")

    return "\n".join(lines)


def create_startup_script(
    folder_path: Path,
    issue_number: int,
    issue_title: str,
    status: str,
    repo_name: str,
    issue_url: str,
    is_intervention: bool,
    timeout: int = DEFAULT_PROMPT_TIMEOUT,
    mcp_coder_install_path: Path | None = None,
    session_folder_path: Path | None = None,
    from_github: bool = False,
) -> Path:
    """Create platform-specific startup script.

    Args:
        folder_path: Working folder path
        issue_number: GitHub issue number
        issue_title: Issue title for banner
        status: Status label
        repo_name: Repo short name
        issue_url: GitHub issue URL
        is_intervention: If True, use intervention mode (no automation)
        timeout: Timeout for mcp-coder prompt calls (default: 300 seconds)
        mcp_coder_install_path: Path to mcp-coder installation directory
            (for finding the executable, separate from session folder)
        session_folder_path: Path to session folder for MCP environment variables
            (overrides folder_path if provided, used for MCP_CODER_PROJECT_DIR)
        from_github: If True, read [tool.mcp-coder.from-github] from the repo's
            pyproject.toml and inject uv pip install commands for GitHub packages.

    Returns:
        Path to created script (.bat or .sh)

    Raises:
        NotImplementedError: If platform is not Windows.
        ValueError: If commands config is not a list of strings.

    Execution strategy depends on the number of commands in the config:
    - Single command: interactive-only via ``claude "{cmd} {issue_number}"``.
      No timeout, no session ID capture, no step labels.
    - Multiple commands: first command automated via ``mcp-coder prompt``,
      middle commands via ``mcp-coder prompt --session-id``,
      last command interactive via ``claude --resume``.
      Step labels are shown for each command.
    - No commands: bare script with venv setup only.

    The ``timeout`` parameter is only used for multi-command flows.
    """
    from .templates import (
        AUTOMATED_RESUME_SECTION_WINDOWS,
        AUTOMATED_SECTION_WINDOWS,
        INTERACTIVE_ONLY_SECTION_WINDOWS,
        INTERACTIVE_RESUME_WITH_COMMAND_WINDOWS,
        INTERVENTION_SCRIPT_WINDOWS,
        STARTUP_SCRIPT_WINDOWS,
        VENV_SECTION_WINDOWS,
    )

    is_windows = platform.system() == "Windows"

    # Get config for this status
    config = get_vscodeclaude_config(status)
    commands = config.get("commands", []) if config else []
    emoji = config["emoji"] if config else "📋"

    # Default: use raw title (for non-Windows platforms when implemented)
    title_display = issue_title[:58] if len(issue_title) > 58 else issue_title

    if is_windows:
        # Escape first so expansion from escaping is counted in the truncation
        title_display = _escape_batch_title(issue_title)
        title_display = title_display[:58].rstrip("^")

        # Get mcp_coder_install_path if not provided
        if mcp_coder_install_path is None:
            mcp_coder_install_path = get_mcp_coder_install_path()

        # Use session_folder_path if provided, otherwise use folder_path
        session_path = session_folder_path or folder_path

        # Format VENV section with both paths
        venv_section = VENV_SECTION_WINDOWS.format(
            mcp_coder_install_path=mcp_coder_install_path or "",
            session_folder_path=str(session_path),
        )

        # Inject GitHub override install commands when from_github is True
        if from_github:
            github_install_section = _build_github_install_section(folder_path)
            venv_section = venv_section + github_install_section

        if is_intervention:
            # Intervention mode - plain claude, no automation
            script_content = INTERVENTION_SCRIPT_WINDOWS.format(
                emoji=emoji,
                issue_number=issue_number,
                title=title_display,
                repo=repo_name,
                status=status,
                issue_url=issue_url,
                venv_section=venv_section,
            )
        else:
            # Validate commands config
            if commands and (
                not isinstance(commands, list)
                or not all(isinstance(c, str) for c in commands)
            ):
                raise ValueError(
                    f"Invalid commands config for status '{status}': "
                    f"expected list of strings, got {commands!r}"
                )

            # Build command sections based on commands list
            if len(commands) == 1:
                # Single command: interactive only, no step labels
                command_sections = INTERACTIVE_ONLY_SECTION_WINDOWS.format(
                    command=commands[0],
                    issue_number=issue_number,
                )
            elif len(commands) > 1:
                sections = []
                for i, cmd in enumerate(commands):
                    step_number = i + 1
                    is_last = i == len(commands) - 1
                    if i == 0:
                        sections.append(
                            AUTOMATED_SECTION_WINDOWS.format(
                                command=cmd,
                                issue_number=issue_number,
                                timeout=timeout,
                                step_number=step_number,
                            )
                        )
                    elif not is_last:
                        sections.append(
                            AUTOMATED_RESUME_SECTION_WINDOWS.format(
                                command=cmd,
                                timeout=timeout,
                                step_number=step_number,
                            )
                        )
                    if is_last:
                        sections.append(
                            INTERACTIVE_RESUME_WITH_COMMAND_WINDOWS.format(
                                command=cmd,
                                step_number=step_number,
                            )
                        )
                command_sections = "\n".join(sections)
            else:
                command_sections = ""

            script_content = STARTUP_SCRIPT_WINDOWS.format(
                emoji=emoji,
                issue_number=issue_number,
                title=title_display,
                repo=repo_name,
                status=status,
                issue_url=issue_url,
                venv_section=venv_section,
                command_sections=command_sections,
            )

        script_path = folder_path / ".vscodeclaude_start.bat"

        # Write script
        script_path.write_text(script_content, encoding="utf-8")

        return script_path
    else:
        # Linux - TODO: Implement in Step 17
        # For now, raise NotImplementedError
        raise NotImplementedError("Linux startup scripts are not yet supported.")


def create_vscode_task(folder_path: Path, script_path: Path) -> None:
    """Create .vscode/tasks.json with runOn: folderOpen.

    Args:
        folder_path: Working folder path
        script_path: Path to startup script
    """
    from .templates import TASKS_JSON_TEMPLATE

    # Create .vscode directory
    vscode_dir = folder_path / ".vscode"
    vscode_dir.mkdir(parents=True, exist_ok=True)

    # Format tasks.json
    content = TASKS_JSON_TEMPLATE.format(script_path=script_path.name)

    # Write tasks.json
    tasks_file = vscode_dir / "tasks.json"
    tasks_file.write_text(content, encoding="utf-8")


def create_status_file(
    folder_path: Path,
    issue_number: int,
    issue_title: str,
    status: str,
    repo_full_name: str,
    branch_name: str,
    issue_url: str,
    is_intervention: bool,
) -> None:
    """Create .vscodeclaude_status.txt in project root.

    Args:
        folder_path: Working folder path
        issue_number: GitHub issue number
        issue_title: Issue title
        status: Status label
        repo_full_name: Full repo name (owner/repo)
        branch_name: Git branch name
        issue_url: GitHub issue URL
        is_intervention: If True, add intervention warning
    """
    from .templates import INTERVENTION_LINE, STATUS_FILE_TEMPLATE

    # Get emoji for status from config
    config = get_vscodeclaude_config(status)
    status_emoji = config["emoji"] if config else "📋"

    # Build intervention line if needed
    intervention_line = INTERVENTION_LINE if is_intervention else ""

    # Format status file
    content = STATUS_FILE_TEMPLATE.format(
        issue_number=issue_number,
        title=issue_title,
        status_emoji=status_emoji,
        status_name=status,
        repo=repo_full_name,
        branch=branch_name,
        started_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        intervention_line=intervention_line,
        issue_url=issue_url,
    )

    # Write status file
    status_file = folder_path / ".vscodeclaude_status.txt"
    status_file.write_text(content, encoding="utf-8")

"""Workspace setup for vscodeclaude feature.

Handles git operations, folder creation, and file generation.
"""

import logging
import platform
import shutil
import stat
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ...utils.git_operations import checkout_branch, fetch_remote
from ...utils.subprocess_runner import (
    CalledProcessError,
    CommandOptions,
    execute_subprocess,
)
from .config import get_vscodeclaude_config, sanitize_folder_name
from .types import DEFAULT_PROMPT_TIMEOUT

logger = logging.getLogger(__name__)


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

    Args:
        workspace_base: Base directory from config
        repo_name: Repository short name (sanitized)
        issue_number: GitHub issue number

    Returns:
        Path like: workspace_base/mcp-coder_123
    """
    sanitized_repo = sanitize_folder_name(repo_name)
    folder_name = f"{sanitized_repo}_{issue_number}"
    return Path(workspace_base) / folder_name


def create_working_folder(folder_path: Path) -> bool:
    """Create working folder if it doesn't exist.

    Args:
        folder_path: Full path to create

    Returns:
        True if created, False if already existed
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
            shutil.rmtree(folder_path, onerror=_remove_readonly)
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

    Raises:
        CalledProcessError: If any command fails

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
    """
    for char in ("^", "&", "|", "<", ">"):
        text = text.replace(char, f"^{char}")
    return text


def create_startup_script(
    folder_path: Path,
    issue_number: int,
    issue_title: str,
    status: str,
    repo_name: str,
    issue_url: str,
    is_intervention: bool,
    timeout: int = DEFAULT_PROMPT_TIMEOUT,
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

    Returns:
        Path to created script (.bat or .sh)

    The templates include:
    - Venv creation/activation
    - mcp-coder prompt for automated analysis
    - mcp-coder prompt for /discuss
    - claude --resume for interactive session
    """
    from .templates import (
        AUTOMATED_SECTION_WINDOWS,
        DISCUSSION_SECTION_WINDOWS,
        INTERACTIVE_SECTION_WINDOWS,
        INTERVENTION_SCRIPT_WINDOWS,
        STARTUP_SCRIPT_WINDOWS,
        VENV_SECTION_WINDOWS,
    )

    is_windows = platform.system() == "Windows"

    # Get config for this status
    config = get_vscodeclaude_config(status)
    initial_cmd = config["initial_command"] if config else None
    emoji = config["emoji"] if config else "📋"

    if is_windows:
        # Escape first so expansion from escaping is counted in the truncation
        title_display = _escape_batch_title(issue_title)
        title_display = title_display[:58] if len(title_display) > 58 else title_display
        if is_intervention:
            # Intervention mode - plain claude, no automation
            script_content = INTERVENTION_SCRIPT_WINDOWS.format(
                emoji=emoji,
                issue_number=issue_number,
                title=title_display,
                repo=repo_name,
                status=status,
                issue_url=issue_url,
                venv_section=VENV_SECTION_WINDOWS,
            )
        else:
            # Normal mode - full automation flow
            automated_section = AUTOMATED_SECTION_WINDOWS.format(
                initial_command=initial_cmd or "/issue_analyse",
                issue_number=issue_number,
                timeout=timeout,
            )

            discussion_section = DISCUSSION_SECTION_WINDOWS.format(
                timeout=timeout,
            )

            script_content = STARTUP_SCRIPT_WINDOWS.format(
                emoji=emoji,
                issue_number=issue_number,
                title=title_display,
                repo=repo_name,
                status=status,
                issue_url=issue_url,
                venv_section=VENV_SECTION_WINDOWS,
                automated_section=automated_section,
                discussion_section=discussion_section,
                interactive_section=INTERACTIVE_SECTION_WINDOWS,
            )

        script_path = folder_path / ".vscodeclaude_start.bat"

        # Write script
        script_path.write_text(script_content, encoding="utf-8")

        return script_path
    else:
        # Linux - TODO: Implement in Step 17
        # For now, raise NotImplementedError
        raise NotImplementedError(
            "Linux templates not yet implemented. " "See Step 17 for Linux support."
        )


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
        started_at=datetime.now(timezone.utc).isoformat(),
        intervention_line=intervention_line,
        issue_url=issue_url,
    )

    # Write status file
    status_file = folder_path / ".vscodeclaude_status.txt"
    status_file.write_text(content, encoding="utf-8")

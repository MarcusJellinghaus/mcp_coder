"""Workspace setup for vscodeclaude feature.

Handles git operations, folder creation, and file generation.
"""

import logging
import platform
import shutil
import stat
import sys
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Any

from mcp_coder.mcp_workspace_git import checkout_branch, fetch_remote

from ...utils.subprocess_runner import (
    CalledProcessError,
    CommandOptions,
    execute_subprocess,
)
from .config import get_vscodeclaude_config, sanitize_folder_name
from .helpers import load_to_be_deleted
from .types import DEFAULT_PROMPT_TIMEOUT, SessionSpec, write_session_spec

logger = logging.getLogger(__name__)

_MCP_CONFIG_FILES: dict[str, str] = {
    "Windows": ".mcp.json",
    "Darwin": ".mcp.macos.json",
    "Linux": ".mcp.linux.json",
}


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


def get_workspace_file_path(workspace_base: str, folder_name: str) -> Path:
    """Return the `.code-workspace` file path for a session folder.

    Single source of truth for the `{workspace_base}/{folder_name}.code-workspace`
    pattern. Callers should use this helper instead of constructing the path
    inline so the convention lives in one place.
    """
    return Path(workspace_base) / f"{folder_name}.code-workspace"


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
    """Validate the platform-appropriate MCP config file exists in repo.

    Args:
        folder_path: Working folder path

    Raises:
        FileNotFoundError: If the required config file is missing.
    """
    system = platform.system()
    required_filename = _MCP_CONFIG_FILES.get(system, ".mcp.json")
    mcp_path = folder_path / required_filename
    if not mcp_path.exists():
        raise FileNotFoundError(
            f"{required_filename} not found in {folder_path}. "
            f"This file is required for Claude Code integration on {system}."
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
    workspace_file = get_workspace_file_path(workspace_base, folder_name)
    workspace_file.write_text(content, encoding="utf-8")

    return workspace_file


def _resolve_install_script(install_path: Path) -> Path:
    """Locate ``tools/install.py`` given the mcp-coder install dir.

    Two layouts are supported:

    * **Wheel install** (production): mcp-coder was ``pip install``ed
      from a wheel; ``pyproject.toml`` data-files put a copy at
      ``<install_path>/.venv/share/mcp-coder/install.py``.
    * **Editable install** (developer): mcp-coder is installed
      ``-e <repo>`` and the canonical ``<repo>/tools/install.py`` is
      reachable from ``install_path``.

    Returns:
        Path to the script. The vscodeclaude template substitutes this
        into the generated startup script so the session runs it
        directly with the mcp-coder venv's interpreter.

    Raises:
        FileNotFoundError: When neither candidate exists — usually
        means mcp-coder was installed from an older wheel without the
        data-files entry, or the install layout is unusual.
    """
    candidates = (
        install_path / ".venv" / "share" / "mcp-coder" / "install.py",
        install_path / "tools" / "install.py",
    )
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(
        f"install.py not found under {install_path}. Looked at: "
        + ", ".join(str(c) for c in candidates)
    )


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
    session_folder_path: Path | None = None,  # pylint: disable=unused-argument
    skip_github_install: bool = False,
) -> Path:
    """Serialize a session spec and write the thin launcher.

    The startup script no longer bakes shell orchestration. It resolves the
    session config, writes a typed ``SessionSpec`` to
    ``<folder>/.vscodeclaude_session.json``, and emits a one-line launcher
    (``.bat``/``.sh``) that bootstraps into ``session_setup`` at run time.
    All flow branching (intervention, 0/1/multi command) now lives in the
    spec and is consumed by ``session_setup``, so the launcher is
    byte-identical for every session apart from the coordinator's Python path.

    Args:
        folder_path: Working folder path (spec + launcher are written here)
        issue_number: GitHub issue number
        issue_title: Issue title for banner
        status: Status label
        repo_name: Repo short name
        issue_url: GitHub issue URL
        is_intervention: If True, mark the spec for intervention mode
        timeout: Timeout for mcp-coder prompt calls (default: 300 seconds)
        mcp_coder_install_path: Path to mcp-coder installation directory
            (for locating install.py and the coordinator venv Python)
        session_folder_path: Unused. Retained for signature stability; the
            CWD is the runtime source of truth for the session directory.
        skip_github_install: If True, thread ``--skip-overrides`` into the
            install.py argv at run time. Default False (auto-detect).

    Returns:
        Path to created launcher script (.bat or .sh)

    Raises:
        FileNotFoundError: If the platform-specific MCP config file is absent
            (POSIX only), or if ``tools/install.py`` cannot be located under
            ``mcp_coder_install_path``.
        RuntimeError: If ``mcp_coder_install_path`` is not provided and cannot
            be auto-discovered from the running mcp-coder install.
        ValueError: If commands config is not a list of strings.
    """
    from .templates import LAUNCHER_POSIX, LAUNCHER_WINDOWS

    is_windows = platform.system() == "Windows"
    mcp_config_filename = _MCP_CONFIG_FILES.get(platform.system(), ".mcp.json")

    # Get config for this status
    config = get_vscodeclaude_config(status)
    commands = config.get("commands", []) if config else []
    emoji = config["emoji"] if config else "📋"

    # Validate commands config (fail-fast; runs for every mode now).
    if commands and (
        not isinstance(commands, list) or not all(isinstance(c, str) for c in commands)
    ):
        raise ValueError(
            f"Invalid commands config for status '{status}': "
            f"expected list of strings, got {commands!r}"
        )

    # POSIX requires the platform-specific MCP config file to exist in the repo.
    if not is_windows and not (folder_path / mcp_config_filename).exists():
        raise FileNotFoundError(
            f"{mcp_config_filename} not found in {folder_path}. "
            f"This file is required for Claude Code integration on "
            f"{platform.system()}."
        )

    if mcp_coder_install_path is None:
        mcp_coder_install_path = get_mcp_coder_install_path()
    if mcp_coder_install_path is None:
        raise RuntimeError(
            "mcp-coder install path could not be determined. "
            "Pass mcp_coder_install_path explicitly."
        )

    install_script_path = _resolve_install_script(mcp_coder_install_path)

    # Serialize the typed spec that session_setup consumes at run time.
    spec = SessionSpec(
        issue_number=issue_number,
        title=issue_title,
        repo=repo_name,
        status=status,
        issue_url=issue_url,
        emoji=emoji,
        commands=list(commands),
        timeout=timeout,
        mcp_config=mcp_config_filename,
        install_script_path=str(install_script_path),
        mcp_coder_install_path=str(mcp_coder_install_path),
        skip_github_install=skip_github_install,
        is_intervention=is_intervention,
    )
    write_session_spec(folder_path, spec)

    # Write the thin launcher (byte-identical apart from the venv Python path).
    if is_windows:
        script_name, template = ".vscodeclaude_start.bat", LAUNCHER_WINDOWS
    else:
        script_name, template = ".vscodeclaude_start.sh", LAUNCHER_POSIX

    script_path = folder_path / script_name
    script_path.write_text(
        template.format(mcp_coder_install_path=str(mcp_coder_install_path)),
        encoding="utf-8",
    )
    if not is_windows:
        script_path.chmod(0o755)

    return script_path


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

    # POSIX shell tasks need ./ prefix to execute a script in the workspace folder.
    if platform.system() == "Windows":
        command_str = script_path.name
    else:
        command_str = f"./{script_path.name}"

    # Format tasks.json
    content = TASKS_JSON_TEMPLATE.format(script_path=command_str)

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

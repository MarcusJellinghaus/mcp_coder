"""Global test configuration and shared fixtures for all tests."""

import logging
import os
import shutil
import tempfile
from importlib.resources.abc import Traversable
from pathlib import Path
from typing import Generator, Type, TypeVar, Union

import git
import pytest


@pytest.fixture
def labels_config_path() -> Union[Path, Traversable]:
    """Get the path to the labels configuration file."""
    from mcp_coder.utils.github_operations.label_config import get_labels_config_path

    return get_labels_config_path()


try:
    from typing import TypedDict
except ImportError:
    from typing_extensions import TypedDict


@pytest.fixture(autouse=True)
def reset_logging() -> Generator[None, None, None]:
    """Reset logging configuration before and after each test.

    This fixture automatically runs for every test to prevent test pollution
    from logging configuration changes. It ensures each test starts with
    a clean logging state.
    """
    # Store initial logging state
    root_logger = logging.getLogger()
    initial_level = root_logger.level
    initial_handlers = root_logger.handlers[:]

    yield  # Run the test

    # Restore logging state after test
    # Close and remove all handlers to prevent resource leaks
    for handler in root_logger.handlers[:]:
        handler.close()
        root_logger.removeHandler(handler)

    # Restore original handlers and level
    for handler in initial_handlers:
        root_logger.addHandler(handler)
    root_logger.setLevel(initial_level)


@pytest.fixture(autouse=True)
def cleanup_test_artifacts() -> Generator[None, None, None]:
    """Clean up any test artifacts created during test execution.

    This fixture automatically runs after every test to ensure no test
    artifacts are left behind that could affect other tests.
    """
    yield  # Run the test first

    # After test execution, clean up any artifacts
    test_dir = Path("tests")

    # Only run cleanup if test_dir exists
    if not test_dir.exists():
        return

    # List of patterns that should be cleaned up
    cleanup_patterns = [
        "*.tmp",
        "tmp*",
        "test_*.log",
        "*.temp",
        "temp_*",
    ]

    # Files/directories that should be preserved
    preserve_files = {
        "__init__.py",
        "conftest.py",
        "README.md",
        "__pycache__",
        ".pytest_cache",
    }

    preserve_dirs = {
        "cli",
        "llm_providers",
        "utils",
        "__pycache__",
        ".pytest_cache",
    }

    # Clean up matching patterns in the tests directory
    for pattern in cleanup_patterns:
        for artifact in test_dir.glob(pattern):
            if (
                artifact.name not in preserve_files
                and artifact.name not in preserve_dirs
            ):
                try:
                    if artifact.is_file():
                        artifact.unlink()
                    elif artifact.is_dir():
                        shutil.rmtree(artifact, ignore_errors=True)
                except (OSError, PermissionError):
                    # If we can't delete it, don't fail the test
                    pass

    # Clean up any directories that might have been created during tests
    for item in test_dir.iterdir():
        if item.is_dir() and item.name not in preserve_dirs:
            # Check if it looks like a test artifact directory
            if any(marker in item.name.lower() for marker in ["temp", "tmp", "test_"]):
                try:
                    shutil.rmtree(item, ignore_errors=True)
                except (OSError, PermissionError):
                    pass


@pytest.fixture
def temp_log_file(tmp_path: Path) -> Generator[Path, None, None]:
    """Provide a temporary log file path for tests that need to test logging to files.

    This fixture uses pytest's tmp_path for automatic cleanup and provides
    a standardized way for tests to create log files.

    Args:
        tmp_path: pytest's temporary directory fixture

    Yields:
        Path: Path to a temporary log file
    """
    log_file = tmp_path / "test.log"
    yield log_file
    # tmp_path cleanup is automatic


@pytest.fixture
def isolated_temp_dir(tmp_path: Path) -> Generator[Path, None, None]:
    """Provide an isolated temporary directory for tests that need to create files.

    This fixture ensures tests have a clean temporary directory that's
    automatically cleaned up after the test completes.

    Args:
        tmp_path: pytest's temporary directory fixture

    Yields:
        Path: Path to a temporary directory
    """
    yield tmp_path
    # tmp_path cleanup is automatic


@pytest.fixture(scope="session")
def session_temp_dir() -> Generator[Path, None, None]:
    """Provide a session-scoped temporary directory for expensive setup operations.

    This fixture creates a temporary directory that persists for the entire
    test session, useful for expensive setup operations that can be shared
    across multiple tests.

    Yields:
        Path: Path to a session-scoped temporary directory
    """
    with tempfile.TemporaryDirectory(prefix="pytest_session_") as temp_dir:
        yield Path(temp_dir)


class GitHubTestSetup(TypedDict):
    """Configuration data for GitHub integration tests.

    Attributes:
        github_token: GitHub Personal Access Token with repo scope
        test_repo_url: URL of test repository (e.g., https://github.com/user/test-repo)
        project_dir: Path to cloned test repository
    """

    github_token: str
    test_repo_url: str
    project_dir: Path


@pytest.fixture
def github_test_setup(tmp_path: Path) -> Generator[GitHubTestSetup, None, None]:
    """Provide shared GitHub test configuration and repository setup.

    Validates GitHub configuration and gracefully skips when missing.

    Configuration sources (in order of preference):
    1. Environment variables: GITHUB_TOKEN, GITHUB_TEST_REPO_URL
    2. MCP Coder config: github.token, github.test_repo_url

    Environment variables:
        GITHUB_TOKEN: GitHub Personal Access Token with repo scope
        GITHUB_TEST_REPO_URL: URL of test repository (e.g., https://github.com/user/test-repo)

    Yields:
        GitHubTestSetup: Configuration dict with token, URL, and cloned repo path

    Raises:
        pytest.skip: When GitHub token or test repository not configured
    """
    from mcp_coder.utils.user_config import get_config_file_path, get_config_values

    # Check for required GitHub configuration
    # Priority 1: Environment variables
    github_token = os.getenv("GITHUB_TOKEN")
    test_repo_url = os.getenv("GITHUB_TEST_REPO_URL")

    # Priority 2: Config system fallback
    config_file_path = get_config_file_path()

    if not github_token or not test_repo_url:
        config: dict[tuple[str, str], str | None] = get_config_values(
            [
                ("github", "token", None),
                ("github", "test_repo_url", None),
            ]
        )
        if not github_token:
            github_token = config[("github", "token")]
        if not test_repo_url:
            test_repo_url = config[("github", "test_repo_url")]

    # Summary of what was found
    token_source = (
        "env" if os.getenv("GITHUB_TOKEN") else "config" if github_token else "none"
    )
    repo_source = (
        "env"
        if os.getenv("GITHUB_TEST_REPO_URL")
        else "config" if test_repo_url else "none"
    )
    print(f"\nGitHub Integration: token={token_source}, repo={repo_source}")

    if not github_token:
        skip_msg = (
            "GitHub token not configured.\n"
            f"  Environment variable GITHUB_TOKEN: Not found\n"
            f"  Config file location: {config_file_path}\n"
            f"  Config file exists: {config_file_path.exists() if config_file_path else False}\n"
            f"  Config file github.token: Not found\n\n"
            "To fix, either:\n"
            "  1. Set environment variable: set GITHUB_TOKEN=ghp_your_token_here\n"
            f"  2. Add to config file {config_file_path}:\n"
            "     [github]\n"
            '     token = "ghp_your_token_here"'
        )
        pytest.skip(skip_msg)

    if not test_repo_url:
        skip_msg = (
            "Test repository URL not configured.\n"
            f"  Environment variable GITHUB_TEST_REPO_URL: Not found\n"
            f"  Config file location: {config_file_path}\n"
            f"  Config file exists: {config_file_path.exists() if config_file_path else False}\n"
            f"  Config file github.test_repo_url: Not found\n\n"
            "To fix, either:\n"
            "  1. Set environment variable: set GITHUB_TEST_REPO_URL=https://github.com/user/test-repo\n"
            f"  2. Add to config file {config_file_path}:\n"
            "     [github]\n"
            '     test_repo_url = "https://github.com/user/test-repo"'
        )
        pytest.skip(skip_msg)

    # Clone the actual test repository
    git_dir = tmp_path / "test_repo"

    try:
        repo = git.Repo.clone_from(test_repo_url, git_dir)
        # Fetch all branches to make sure we have the latest
        repo.git.fetch("origin")
        # Ensure we're on main branch
        try:
            repo.git.checkout("main")
        except:
            # Try master if main doesn't exist
            try:
                repo.git.checkout("master")
            except:
                pass  # Use current branch
    except Exception as e:
        pytest.skip(f"Could not clone test repository {test_repo_url}: {e}")

    setup: GitHubTestSetup = {
        "github_token": github_token,
        "test_repo_url": test_repo_url,
        "project_dir": git_dir,
    }
    yield setup


T = TypeVar("T")


def create_github_manager(manager_class: Type[T], github_setup: GitHubTestSetup) -> T:
    """Create a GitHub manager instance using real configuration.

    This helper function provides a consistent way to instantiate GitHub managers
    for integration tests. The managers will use the real configuration system
    to read the GitHub token from the cloned repository's config or environment.

    Args:
        manager_class: The manager class to instantiate (e.g., LabelsManager, PullRequestManager)
        github_setup: GitHub test configuration from github_test_setup fixture

    Returns:
        Instance of the specified manager class

    Raises:
        Exception: If manager instantiation fails

    Example:
        >>> def labels_manager(github_test_setup: GitHubTestSetup) -> LabelsManager:
        ...     return create_github_manager(LabelsManager, github_test_setup)
    """
    # No mocking - let the manager use real config system
    # The BaseGitHubManager will read from environment variables or config file
    return manager_class(github_setup["project_dir"])  # type: ignore[call-arg]


@pytest.fixture
def require_claude_cli() -> None:
    """Skip test if Claude CLI is not installed.

    This fixture checks if Claude Code CLI is available on the system.
    Tests that require actual Claude CLI executable should use this fixture.

    Usage:
        @pytest.mark.claude_cli_integration
        def test_something(require_claude_cli):
            # Test code that needs Claude CLI
            pass

    Raises:
        pytest.skip: When Claude CLI is not found on the system
    """
    from mcp_coder.llm.providers.claude.claude_executable_finder import (
        find_claude_executable,
    )

    try:
        find_claude_executable()
    except FileNotFoundError as e:
        pytest.skip(
            f"Claude CLI not installed: {e}\n"
            "Install with: npm install -g @anthropic-ai/claude-code"
        )

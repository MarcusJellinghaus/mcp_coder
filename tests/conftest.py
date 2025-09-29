"""Global test configuration and shared fixtures for all tests."""

import logging
import os
import shutil
import tempfile
from pathlib import Path
from typing import Generator, Type, TypeVar
from unittest.mock import patch

import git
import pytest

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
    from mcp_coder.utils.user_config import get_config_value

    # Check for required GitHub configuration
    # Priority 1: Environment variables
    github_token = os.getenv("GITHUB_TOKEN")
    test_repo_url = os.getenv("GITHUB_TEST_REPO_URL")

    # Priority 2: Config system fallback
    if not github_token:
        github_token = get_config_value("github", "token")
    if not test_repo_url:
        test_repo_url = get_config_value("github", "test_repo_url")

    if not github_token:
        pytest.skip(
            "GitHub token not configured. Set GITHUB_TOKEN environment variable "
            "or add github.token to ~/.mcp_coder/config.toml"
        )

    if not test_repo_url:
        pytest.skip(
            "Test repository URL not configured. Set GITHUB_TEST_REPO_URL environment variable "
            "or add github.test_repo_url to ~/.mcp_coder/config.toml"
        )

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
    """Create a GitHub manager instance with mocked token configuration.

    This helper function eliminates duplicated fixture logic by providing
    a consistent way to instantiate GitHub managers with proper token mocking.

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
    patcher = patch("mcp_coder.utils.user_config.get_config_value")
    mock_config = patcher.start()
    mock_config.return_value = github_setup["github_token"]
    try:
        return manager_class(github_setup["project_dir"])  # type: ignore[call-arg]
    finally:
        patcher.stop()

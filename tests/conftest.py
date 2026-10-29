"""Global test configuration and shared fixtures for all tests."""

import contextlib
import logging
import os
import shutil
import tempfile
from collections.abc import Generator
from importlib.resources.abc import Traversable
from pathlib import Path
from unittest.mock import patch

import git
import pytest


@pytest.fixture
def labels_config_path() -> Path | Traversable:
    """Get the path to the labels configuration file."""
    from mcp_coder.config.label_config import get_labels_config_path

    return get_labels_config_path()


@pytest.fixture
def git_repo(tmp_path: Path) -> tuple[git.Repo, Path]:
    """Create clean, empty git repository for testing.

    Args:
        tmp_path: Pytest temporary directory fixture

    Returns:
        tuple[Repo, Path]: Git repository object and path to project directory
    """
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()

    # Initialize git repository
    repo = git.Repo.init(project_dir)

    # Configure git user (required for commits)
    setup_git_config(repo)

    return repo, project_dir


@pytest.fixture
def github_remote_repo(
    git_repo: tuple[git.Repo, Path], monkeypatch: pytest.MonkeyPatch
) -> Path:
    """Git repository with a GitHub ``origin`` remote and a dummy token.

    Lets real GitHub manager constructors run without network access.

    Returns:
        Path to the project directory.
    """
    repo, project_dir = git_repo
    repo.create_remote("origin", "https://github.com/owner/repo.git")
    monkeypatch.setenv("GITHUB_TOKEN", "x")
    return project_dir


def setup_git_config(repo: git.Repo) -> None:
    """Configure git user for repository.

    Args:
        repo: Git repository object to configure
    """
    with repo.config_writer() as config:
        config.set_value("user", "name", "Test User")
        config.set_value("user", "email", "test@example.com")


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
def _resolvable_formatter() -> Generator[None, None, None]:
    """Let formatter pre-flights pass in project dirs without pyproject.toml.

    Patches the single lookup site behind check_formatter_config. Real formatting
    is unaffected (the wrapper uses mcp-tools-py's own resolve_steps). Tests of the
    helper re-patch it.

    Uses patch() rather than monkeypatch: requesting monkeypatch here would
    delay its teardown past cleanup_test_artifacts, which then runs with the
    test's own monkeypatches (e.g. of Path.iterdir) still applied.
    """
    with patch(
        "mcp_coder.workflow_steps.commit.resolve_steps",
        lambda _p: ["isort", "black"],
    ):
        yield


@pytest.fixture(autouse=True)
def isolate_mlflow_artifacts(
    tmp_path: Path,
) -> Generator[None, None, None]:  # noqa: F841 (autouse fixture)
    """Isolate MLflow artifacts to prevent pollution of project root.

    This fixture automatically sets MLflow's tracking URI to a temporary
    directory for all tests, ensuring that no MLflow databases or artifacts
    are created in the project root directory.
    """
    # Set MLflow tracking URI to temp directory for all tests
    original_uri = os.environ.get("MLFLOW_TRACKING_URI")
    mlflow_temp = tmp_path / ".mlflow_test"
    mlflow_temp.mkdir(exist_ok=True)
    os.environ["MLFLOW_TRACKING_URI"] = f"file:///{mlflow_temp}"

    yield  # Run the test

    # Restore original tracking URI
    if original_uri:
        os.environ["MLFLOW_TRACKING_URI"] = original_uri
    else:
        os.environ.pop("MLFLOW_TRACKING_URI", None)


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
        if (
            item.is_dir()
            and item.name not in preserve_dirs
            and any(marker in item.name.lower() for marker in ["temp", "tmp", "test_"])
        ):
            # Check if it looks like a test artifact directory
            with contextlib.suppress(OSError, PermissionError):
                shutil.rmtree(item, ignore_errors=True)


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


@pytest.fixture
def require_copilot_cli() -> None:
    """Skip test if Copilot CLI is not installed."""
    from mcp_coder.utils.executable_finder import find_executable

    try:
        find_executable("copilot", install_hint="")
    except FileNotFoundError:
        pytest.skip("Copilot CLI not installed")

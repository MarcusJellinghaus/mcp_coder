"""Shared test fixtures for git operations testing."""

import pytest
from pathlib import Path
from typing import Any
from git import Repo


@pytest.fixture
def git_repo(tmp_path: Path) -> tuple[Repo, Path]:
    """Create clean, empty git repository for testing.

    Args:
        tmp_path: Pytest temporary directory fixture

    Returns:
        tuple[Repo, Path]: Git repository object and path to project directory
    """
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()

    # Initialize git repository
    repo = Repo.init(project_dir)

    # Configure git user (required for commits)
    setup_git_config(repo)

    return repo, project_dir


@pytest.fixture
def git_repo_with_files(tmp_path: Path) -> tuple[Repo, Path]:
    """Create git repository with sample committed files for modification tests.

    Args:
        tmp_path: Pytest temporary directory fixture

    Returns:
        tuple[Repo, Path]: Git repository object and path to project directory with committed files
    """
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()

    # Initialize git repository
    repo = Repo.init(project_dir)

    # Configure git user (required for commits)
    setup_git_config(repo)

    # Create simple test files
    sample_files = {
        "README.md": "# Test Project\n\nSample project for testing.",
        "main.py": "def main():\n    print('Hello, World!')",
        "config.yml": "debug: false\nport: 8080",
    }

    create_sample_files(project_dir, sample_files)

    # Stage and commit files
    repo.index.add(list(sample_files.keys()))
    repo.index.commit("Initial commit with sample files")

    return repo, project_dir


def setup_git_config(repo: Repo) -> None:
    """Configure git user for repository.

    Args:
        repo: Git repository object to configure
    """
    with repo.config_writer() as config:
        config.set_value("user", "name", "Test User")
        config.set_value("user", "email", "test@example.com")


def create_sample_files(project_dir: Path, file_specs: dict[str, str]) -> None:
    """Create test files from specifications.

    Args:
        project_dir: Directory to create files in
        file_specs: Dictionary mapping file paths to content
    """
    for file_path, content in file_specs.items():
        full_path = project_dir / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content)


def verify_git_state(repo: Repo, expected_commits: int | None = None) -> dict[str, Any]:
    """Check repository state for assertions.

    Args:
        repo: Git repository object to verify
        expected_commits: Expected number of commits (optional)

    Returns:
        dict: Repository state information
    """
    try:
        commits = list(repo.iter_commits())
        commit_count = len(commits)

        # Get current branch
        try:
            current_branch = repo.active_branch.name
        except TypeError:
            current_branch = None  # Detached HEAD or no commits

        # Check if working tree is clean
        is_dirty = repo.is_dirty()

        # Get untracked files
        untracked_files = repo.untracked_files

        state = {
            "commit_count": commit_count,
            "current_branch": current_branch,
            "is_dirty": is_dirty,
            "untracked_files": untracked_files,
            "has_commits": commit_count > 0,
        }

        # Verify expected commits if specified
        if expected_commits is not None and commit_count != expected_commits:
            raise AssertionError(
                f"Expected {expected_commits} commits, found {commit_count}"
            )

        return state

    except Exception as e:
        return {
            "error": str(e),
            "commit_count": 0,
            "current_branch": None,
            "is_dirty": False,
            "untracked_files": [],
            "has_commits": False,
        }

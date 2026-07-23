"""Shared git fixtures/helpers for the rebase workflow tests.

Kept local to ``tests.workflows.rebase`` so the tests satisfy the Test Module
Independence contract (no imports from ``tests.utils``). ``git_repo_with_files``
is injected via pytest conftest discovery; ``setup_git_config`` is a plain
helper imported directly by test-local fixtures.
"""

from pathlib import Path

import pytest
from git import Repo


def setup_git_config(repo: Repo) -> None:
    """Configure git user for a repository (required for commits)."""
    with repo.config_writer() as config:
        config.set_value("user", "name", "Test User")
        config.set_value("user", "email", "test@example.com")


@pytest.fixture
def git_repo_with_files(tmp_path: Path) -> tuple[Repo, Path]:
    """Create a git repository with sample committed files.

    Returns:
        The ``Repo`` object and the project directory path.
    """
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()

    repo = Repo.init(project_dir)
    setup_git_config(repo)

    sample_files = {
        "README.md": "# Test Project\n\nSample project for testing.",
        "main.py": "def main():\n    print('Hello, World!')",
        "config.yml": "debug: false\nport: 8080",
    }
    for name, content in sample_files.items():
        (project_dir / name).write_text(content)

    repo.index.add(list(sample_files.keys()))
    repo.index.commit("Initial commit with sample files")

    return repo, project_dir

"""Shared test fixtures for git operations testing."""

import pytest
from pathlib import Path
from git import Repo


@pytest.fixture
def git_repo(tmp_path: Path) -> Path:
    """Create clean, empty git repository for testing.
    
    Args:
        tmp_path: Pytest temporary directory fixture
        
    Returns:
        Path: Path to the git repository directory
    """
    # Initialize git repository
    repo = Repo.init(tmp_path)
    
    # Configure git user for commits (required for testing)
    repo.config_writer().set_value("user", "name", "Test User").release()
    repo.config_writer().set_value("user", "email", "test@example.com").release()
    
    return tmp_path


@pytest.fixture  
def git_repo_with_files(tmp_path: Path) -> Path:
    """Create git repository with 2-3 committed files for modification tests.
    
    Args:
        tmp_path: Pytest temporary directory fixture
        
    Returns:
        Path: Path to the git repository directory with committed files
    """
    # Initialize git repository
    repo = Repo.init(tmp_path)
    
    # Configure git user for commits (required for testing)
    repo.config_writer().set_value("user", "name", "Test User").release()
    repo.config_writer().set_value("user", "email", "test@example.com").release()
    
    # Create initial files
    file1 = tmp_path / "file1.txt"
    file1.write_text("Initial content for file 1")
    
    file2 = tmp_path / "subdir" / "file2.py"
    file2.parent.mkdir(exist_ok=True)
    file2.write_text("# Initial Python file\nprint('Hello, World!')")
    
    file3 = tmp_path / "config.json"
    file3.write_text('{"setting": "initial_value", "enabled": true}')
    
    # Stage and commit initial files
    repo.index.add([str(file1), str(file2), str(file3)])
    repo.index.commit("Initial commit with test files")
    
    return tmp_path

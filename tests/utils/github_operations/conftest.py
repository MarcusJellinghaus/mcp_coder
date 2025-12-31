"""Shared fixtures for GitHub operations tests."""

import io
import zipfile
from typing import Generator
from unittest.mock import Mock, patch

import pytest

from mcp_coder.utils.github_operations import CIResultsManager


@pytest.fixture
def mock_repo() -> Mock:
    """Mock GitHub repository for testing."""
    return Mock()


@pytest.fixture
def ci_manager(mock_repo: Mock) -> CIResultsManager:
    """CIResultsManager instance for testing with mocked dependencies."""
    repo_url = "https://github.com/test/repo.git"

    with patch("mcp_coder.utils.user_config.get_config_value") as mock_config:
        mock_config.return_value = "test_token"

        with patch("github.Github") as mock_github:
            mock_github.return_value.get_repo.return_value = mock_repo
            manager = CIResultsManager(repo_url=repo_url)
            manager._repository = mock_repo
            return manager


@pytest.fixture
def mock_artifact() -> Mock:
    """Mock artifact for testing."""
    artifact = Mock()
    artifact.name = "test-results"
    artifact.archive_download_url = (
        "https://api.github.com/repos/test/repo/artifacts/123/zip"
    )
    return artifact


@pytest.fixture
def mock_zip_content() -> bytes:
    """Create mock ZIP content with test files."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as zf:
        zf.writestr("results.xml", "<?xml version='1.0'?><testsuites></testsuites>")
        zf.writestr("coverage.json", '{"total": 85.5}')
    return buffer.getvalue()

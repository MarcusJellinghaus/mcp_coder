"""Shared fixtures for issue branch resolution tests."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from mcp_coder.utils.github_operations.issues import IssueBranchManager


@pytest.fixture
def mock_manager() -> IssueBranchManager:
    """Create a mock IssueBranchManager for testing."""
    mock_path = Mock(spec=Path)
    mock_path.exists.return_value = True
    mock_path.is_dir.return_value = True

    with (
        patch("mcp_coder.utils.git_operations.is_git_repository", return_value=True),
        patch(
            "mcp_coder.utils.github_operations.base_manager.user_config.get_config_values",
            return_value={(("github", "token")): "fake_token"},
        ),
        patch("mcp_coder.utils.github_operations.base_manager.Github"),
    ):
        manager = IssueBranchManager(mock_path)
        return manager

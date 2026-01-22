"""Shared fixtures for workflows tests."""

from pathlib import Path

import pytest


@pytest.fixture
def labels_config_path() -> Path:
    """Get the path to the labels configuration file."""
    from mcp_coder.utils.github_operations.label_config import get_labels_config_path

    return get_labels_config_path()

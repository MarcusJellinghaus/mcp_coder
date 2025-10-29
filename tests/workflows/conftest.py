"""Shared fixtures for workflows tests."""

from pathlib import Path

import pytest


@pytest.fixture
def labels_config_path() -> Path:
    """Get the path to the labels configuration file.

    This fixture ensures tests can find the labels.json file regardless of
    where pytest is run from or whether package is installed.

    Returns:
        Path to labels.json (tries local first, then package bundled)
    """
    # Use the helper function from label_config module
    from mcp_coder.utils.github_operations.label_config import get_labels_config_path
    
    # Try multiple strategies to find the config file
    conftest_path = Path(__file__).resolve()
    project_root = conftest_path.parent.parent.parent
    
    # Check if running in development mode (workflows/config exists)
    local_config = project_root / "workflows" / "config" / "labels.json"
    if local_config.exists():
        return local_config
    
    # Fall back to package bundled config using helper function
    return get_labels_config_path()

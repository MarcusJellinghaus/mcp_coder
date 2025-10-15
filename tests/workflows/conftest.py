"""Shared fixtures for workflows tests."""

from pathlib import Path

import pytest


@pytest.fixture
def labels_config_path() -> Path:
    """Get the path to the labels configuration file.

    This fixture ensures tests can find the labels.json file regardless of
    where pytest is run from.

    Returns:
        Path to workflows/config/labels.json
    """
    # Try multiple strategies to find the config file

    # Strategy 1: Relative to this conftest.py file
    # conftest.py is in tests/workflows/, so go up 2 levels to project root
    conftest_path = Path(__file__).resolve()
    project_root_from_conftest = conftest_path.parent.parent.parent
    labels_file_1 = project_root_from_conftest / "workflows" / "config" / "labels.json"

    if labels_file_1.exists():
        return labels_file_1

    # Strategy 2: From current working directory
    labels_file_2 = Path.cwd() / "workflows" / "config" / "labels.json"

    if labels_file_2.exists():
        return labels_file_2

    # If neither works, raise an error with debug info
    raise FileNotFoundError(
        f"Cannot find labels.json. Tried:\n"
        f"  1. {labels_file_1} (from conftest)\n"
        f"  2. {labels_file_2} (from cwd)\n"
        f"  conftest.py: {conftest_path}\n"
        f"  CWD: {Path.cwd()}"
    )

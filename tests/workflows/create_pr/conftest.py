"""Shared fixtures for create_pr workflow tests."""

from collections.abc import Iterator
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture(autouse=True)
def _no_branch_issue_link() -> Iterator[MagicMock]:
    """Default: branch not linked. Tests override with their own @patch."""
    with patch(
        "mcp_coder.workflows.create_pr.core.validate_branch_issue_linkage",
        return_value=None,
    ) as mock:
        yield mock

"""Shared fixtures for coordinator command tests."""

from collections.abc import Iterator
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.mcp_workspace_github import BodyTrust, BodyTrustResult


@pytest.fixture(autouse=True)
def _trusted_issue_bodies() -> Iterator[MagicMock]:
    """Treat every issue body as trusted unless a test patches otherwise.

    Yields:
        The patched ``evaluate_body_trust`` in the coordinator commands module.
    """
    with patch(
        "mcp_coder.cli.commands.coordinator.commands.evaluate_body_trust",
        return_value=BodyTrustResult(status=BodyTrust.TRUSTED, reason=""),
    ) as mock_trust:
        yield mock_trust

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


@pytest.fixture(autouse=True)
def _no_untrusted_launch_keys() -> Iterator[MagicMock]:
    """Keep the status command's trust lookups off GitHub.

    Yields:
        The patched ``find_untrusted_launch_keys``, returning an empty set.
    """
    with patch(
        "mcp_coder.workflows.vscodeclaude.issues.find_untrusted_launch_keys",
        return_value=set(),
    ) as mock_finder:
        yield mock_finder


@pytest.fixture(autouse=True)
def _no_dispatch_sleep() -> Iterator[MagicMock]:
    """Keep the delay between dispatches from sleeping.

    Yields:
        The patched ``sleep`` in the coordinator commands module.
    """
    with patch("mcp_coder.cli.commands.coordinator.commands.sleep") as mock_sleep:
        yield mock_sleep


@pytest.fixture(autouse=True)
def _dispatch_delay() -> Iterator[MagicMock]:
    """Keep the run off the real user config for the dispatch delay.

    Yields:
        The patched ``get_dispatch_delay_seconds``, returning 15.
    """
    with patch(
        "mcp_coder.cli.commands.coordinator.commands.get_dispatch_delay_seconds",
        return_value=15,
    ) as mock_delay:
        yield mock_delay

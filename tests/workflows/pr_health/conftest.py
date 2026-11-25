"""Shared fixtures for PR-health tests."""

from collections.abc import Iterator
from unittest.mock import MagicMock

import pytest


@pytest.fixture(autouse=True)
def _no_cache_write(monkeypatch: pytest.MonkeyPatch) -> Iterator[MagicMock]:
    """Stub the issue-cache write-back so escalations never touch the real cache dir."""
    mock = MagicMock()
    monkeypatch.setattr(
        "mcp_coder.workflows.pr_health.checks.update_issue_labels_in_cache", mock
    )
    yield mock

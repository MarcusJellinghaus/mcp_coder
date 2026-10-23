"""Shared fixtures for implement workflow tests."""

from collections.abc import Iterator
from unittest.mock import patch

import pytest


@pytest.fixture(autouse=True)
def _stub_branch_head() -> Iterator[None]:
    """Keep the shared failure comment builder away from real git."""
    with patch(
        "mcp_coder.workflow_utils.failure_handling._branch_head",
        return_value=("feat", "abc1234"),
    ):
        yield

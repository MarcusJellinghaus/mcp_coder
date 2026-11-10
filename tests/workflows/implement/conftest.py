"""Shared fixtures for implement workflow tests."""

from collections.abc import Iterator
from unittest.mock import patch

import pytest

from mcp_coder.workflows.implement.check_loop import CheckOutcome


@pytest.fixture(autouse=True)
def _stub_branch_head() -> Iterator[None]:
    """Keep the shared failure comment builder away from real git."""
    with patch(
        "mcp_coder.workflow_utils.failure_handling._branch_head",
        return_value=("feat", "abc1234"),
    ):
        yield


@pytest.fixture(autouse=True)
def _stub_task_checks(request: pytest.FixtureRequest) -> Iterator[None]:
    """Keep process_single_task away from the real check loop and toolkit.

    A test that needs another result patches the same target itself (the
    innermost patch wins); ``@pytest.mark.real_check_loop`` opts out entirely.
    """
    if request.node.get_closest_marker("real_check_loop"):
        yield
        return
    with patch(
        "mcp_coder.workflows.implement.task_processing.check_and_fix_mypy",
        return_value=CheckOutcome("clean"),
    ):
        yield

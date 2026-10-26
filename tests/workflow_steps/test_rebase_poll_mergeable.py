"""Tests for _poll_mergeable_state in the rebase workflow step."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.workflow_steps.rebase import _poll_mergeable_state

_MODULE = "mcp_coder.workflow_steps.rebase"


class TestPollMergeableState:
    """Tests for _poll_mergeable_state."""

    @pytest.mark.parametrize(
        ("responses", "expected_state", "expected_sleeps"),
        [
            pytest.param([[{"mergeable_state": "clean"}]], "clean", 0, id="settled"),
            pytest.param(
                [[{"mergeable_state": "unknown"}]] * 6, "unknown", 5, id="unknown_cap"
            ),
            pytest.param([[]] * 6, None, 5, id="no_pr"),
            pytest.param(
                [[{"mergeable_state": "unknown"}], [{"mergeable_state": "clean"}]],
                "clean",
                1,
                id="unknown_then_clean",
            ),
        ],
    )
    def test_poll_result(
        self,
        responses: list[list[dict[str, str]]],
        expected_state: str | None,
        expected_sleeps: int,
    ) -> None:
        pr_manager = MagicMock()
        pr_manager.find_pull_request_by_head.side_effect = responses
        with (
            patch(f"{_MODULE}.PullRequestManager", return_value=pr_manager),
            patch(f"{_MODULE}.time.sleep") as mock_sleep,
        ):
            state = _poll_mergeable_state(Path("/fake/project"), "123-branch")

        assert state == expected_state
        assert mock_sleep.call_count == expected_sleeps
        assert pr_manager.find_pull_request_by_head.call_count == len(responses)
        pr_manager.find_pull_request_by_head.assert_called_with("123-branch")

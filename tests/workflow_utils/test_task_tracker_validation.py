from mcp_coder.workflow_utils.task_tracker import TASK_TRACKER_TEMPLATE
from mcp_coder.workflow_utils.task_tracker_classify import (
    TrackerState,
    classify_tracker_content,
)


class TestTaskTrackerTemplate:
    """Tests for TASK_TRACKER_TEMPLATE constant."""

    def test_template_contains_tasks_header(self) -> None:
        """Test template contains ## Tasks header."""
        assert "## Tasks" in TASK_TRACKER_TEMPLATE

    def test_template_contains_pull_request_header(self) -> None:
        """Test template contains ## Pull Request header."""
        assert "## Pull Request" in TASK_TRACKER_TEMPLATE

    def test_template_is_valid(self) -> None:
        """Test the template classifies as an empty tracker."""
        assert classify_tracker_content(TASK_TRACKER_TEMPLATE) == (
            TrackerState.EMPTY,
            [],
        )

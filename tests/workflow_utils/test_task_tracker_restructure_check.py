"""Tests for the restructure check and completed-task detection."""

from mcp_coder.workflow_utils.task_tracker import TASK_TRACKER_TEMPLATE
from mcp_coder.workflow_utils.task_tracker_classify import (
    check_restructure,
    has_completed_tasks,
)

# Title plus "## Instructions for LLM" block of the template; contains an [x] line.
INSTRUCTIONS = TASK_TRACKER_TEMPLATE.split("## Tasks")[0]

STEP_TRACKER = (
    INSTRUCTIONS + "## Step 1: Setup\n"
    "- [x] Implementation\n"
    "- [ ] Commit message prepared\n\n"
    "## Step 2: More\n"
    "- [ ] Implementation\n"
    "- [ ] Commit message prepared\n"
)

RESTRUCTURED = (
    INSTRUCTIONS + "## Tasks\n\n"
    "### Step 1: Setup\n"
    "- [x] Implementation\n"
    "- [ ] Commit message prepared\n\n"
    "### Step 2: More\n"
    "- [ ] Implementation\n"
    "- [ ] Commit message prepared\n\n"
    "## Pull Request\n"
    "- [ ] PR review\n"
)


class TestHasCompletedTasks:
    """Detection of [x] lines outside the instructions section."""

    def test_template_has_none(self) -> None:
        assert "- [x]" in TASK_TRACKER_TEMPLATE
        assert has_completed_tasks(TASK_TRACKER_TEMPLATE) is False

    def test_step_tracker_with_checked_line(self) -> None:
        assert has_completed_tasks(STEP_TRACKER) is True

    def test_flat_list_without_checked_line(self) -> None:
        content = TASK_TRACKER_TEMPLATE.replace(
            "<!-- Tasks populated from pr_info/steps/ by prepare_task_tracker -->",
            "- [ ] One\n- [ ] Two",
        )
        assert has_completed_tasks(content) is False


class TestCheckRestructureAccepted:
    """Restructures that keep every checkbox verbatim."""

    def test_step_tracker_moved_into_tasks(self) -> None:
        assert check_restructure(STEP_TRACKER, RESTRUCTURED) == []

    def test_pull_request_tasks_unrestricted_with_checked_pr_box(self) -> None:
        original = RESTRUCTURED.replace(
            "## Pull Request\n- [ ] PR review\n",
            "## Pull Request\n- [x] PR review\n",
        )
        restructured = original + "- [ ] PR summary prepared\n- [ ] Extra PR task\n"
        assert check_restructure(original, restructured) == []

    def test_new_unchecked_under_step_without_checked(self) -> None:
        restructured = RESTRUCTURED.replace(
            "### Step 2: More\n", "### Step 2: More\n- [ ] Brand new task\n"
        )
        assert check_restructure(STEP_TRACKER, restructured) == []


class TestCheckRestructureRejected:
    """Restructures that lose, change or add protected checkboxes."""

    def test_deleted_checkbox(self) -> None:
        restructured = RESTRUCTURED.replace("- [ ] Implementation\n", "")
        errors = check_restructure(STEP_TRACKER, restructured)
        assert errors
        assert any("'implementation'" in e for e in errors)

    def test_reworded_checkbox(self) -> None:
        restructured = RESTRUCTURED.replace(
            "- [ ] Implementation\n", "- [ ] Implement it\n"
        )
        errors = check_restructure(STEP_TRACKER, restructured)
        assert any("'implementation'" in e for e in errors)

    def test_unchecked_to_checked(self) -> None:
        restructured = RESTRUCTURED.replace(
            "- [ ] Implementation\n", "- [x] Implementation\n"
        )
        errors = check_restructure(STEP_TRACKER, restructured)
        assert any("[x] lines" in e for e in errors)

    def test_checked_to_unchecked(self) -> None:
        restructured = RESTRUCTURED.replace(
            "- [x] Implementation\n", "- [ ] Implementation\n"
        )
        errors = check_restructure(STEP_TRACKER, restructured)
        assert any("[x] lines" in e for e in errors)

    def test_added_checked(self) -> None:
        restructured = RESTRUCTURED.replace(
            "- [x] Implementation\n", "- [x] Implementation\n- [x] Bonus\n"
        )
        errors = check_restructure(STEP_TRACKER, restructured)
        assert any("[x] lines" in e for e in errors)

    def test_added_unchecked_under_checked_step(self) -> None:
        restructured = RESTRUCTURED.replace(
            "- [x] Implementation\n", "- [x] Implementation\n- [ ] Bonus\n"
        )
        errors = check_restructure(STEP_TRACKER, restructured)
        assert any("'bonus'" in e for e in errors)

    def test_commit_message_count_under_checked_steps(self) -> None:
        restructured = RESTRUCTURED.replace(
            "- [x] Implementation\n",
            "- [x] Implementation\n- [ ] Commit message prepared\n"
            "- [ ] Commit message prepared\n",
        )
        errors = check_restructure(STEP_TRACKER, restructured)
        assert (
            "'commit message prepared': 3 unchecked under steps with [x],"
            " original has 2" in errors
        )

    def test_result_not_populated(self) -> None:
        errors = check_restructure(STEP_TRACKER, STEP_TRACKER)
        assert errors
        assert all(e.startswith("pr_info/TASK_TRACKER.md") for e in errors)

    def test_empty_result_not_populated(self) -> None:
        errors = check_restructure(STEP_TRACKER, TASK_TRACKER_TEMPLATE)
        assert errors

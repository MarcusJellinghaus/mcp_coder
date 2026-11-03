"""Tests for the strict task tracker classifier."""

from pathlib import Path

import pytest

from mcp_coder.workflow_utils.task_tracker import (
    TASK_TRACKER_TEMPLATE,
    get_task_counts,
)
from mcp_coder.workflow_utils.task_tracker_classify import (
    EXPECTED_FORMAT,
    TrackerState,
    _scan_tracker,
    classify_task_tracker,
    classify_tracker_content,
    describe_violations,
)

TEST_DATA = Path(__file__).parent / "test_data"

HEAD = "# Task Status Tracker\n\n"

VALID = (
    HEAD + "## Tasks\n\n"
    "### Step 1: Setup\n"
    "- [x] Implementation\n"
    "- [ ] Quality checks\n\n"
    "### Step 2: More\n"
    "- [ ] Implementation\n\n"
    "## Pull Request\n"
    "- [ ] PR review\n"
)


def _template_with_tasks(tasks_body: str) -> str:
    """Replace the placeholder comment of the template with ``tasks_body``."""
    placeholder = "<!-- Tasks populated from pr_info/steps/ by prepare_task_tracker -->"
    assert placeholder in TASK_TRACKER_TEMPLATE
    return TASK_TRACKER_TEMPLATE.replace(placeholder, tasks_body)


class TestClassifyValidStates:
    """EMPTY and POPULATED trackers."""

    def test_template_is_empty(self) -> None:
        assert classify_tracker_content(TASK_TRACKER_TEMPLATE) == (
            TrackerState.EMPTY,
            [],
        )

    def test_real_tracker_is_populated(self) -> None:
        content = (TEST_DATA / "populated_tracker.md").read_text(encoding="utf-8")
        assert classify_tracker_content(content) == (TrackerState.POPULATED, [])

    def test_simple_valid_tracker_is_populated(self) -> None:
        assert classify_tracker_content(VALID) == (TrackerState.POPULATED, [])

    def test_multiline_html_comment_is_skipped(self) -> None:
        content = VALID.replace(
            "## Tasks\n", "## Tasks\n<!--\n- [ ] commented out\n### Notes\n-->\n"
        )
        assert classify_tracker_content(content) == (TrackerState.POPULATED, [])


class TestClassifyInvalid:
    """INVALID shapes seen in real runs and synthetic variants."""

    def _assert_invalid(self, content: str) -> list[str]:
        state, violations = classify_tracker_content(content)
        assert state is TrackerState.INVALID
        assert violations
        assert all(v.startswith("pr_info/TASK_TRACKER.md") for v in violations)
        return violations

    def test_issue_1146_flat_checkboxes(self) -> None:
        content = _template_with_tasks("- [ ] Do the thing\n- [ ] Do another thing")
        violations = self._assert_invalid(content)
        joined = "\n".join(violations)
        assert "outside any '### Step N:' section (2 checkboxes affected)" in joined
        assert "'## Pull Request' section has no checkboxes" in joined

    def test_issue_1085_flat_step_list(self) -> None:
        content = _template_with_tasks(
            "- [x] [Step 1 — Setup](./steps/step_1.md)\n"
            "- [x] [Step 2 — Core](./steps/step_2.md)\n"
            "- [ ] [Step 3 — Docs](./steps/step_3.md)"
        )
        content += "- [ ] PR review\n"
        violations = self._assert_invalid(content)
        assert any("3 checkboxes affected" in v for v in violations)

    def test_flat_list_under_implementation_steps(self) -> None:
        content = _template_with_tasks("### Implementation Steps\n- [ ] One\n- [ ] Two")
        content += "- [ ] PR review\n"
        violations = self._assert_invalid(content)
        assert any("'### Implementation Steps'" in v for v in violations)

    def test_step_headers_without_tasks_section(self) -> None:
        content = HEAD + "## Step 1: Setup\n- [x] Done\n\n## Step 2: More\n- [ ] Todo\n"
        violations = self._assert_invalid(content)
        assert any("no '## Tasks' section" in v for v in violations)

    def test_checkbox_before_first_step(self) -> None:
        content = VALID.replace(
            "### Step 1: Setup\n", "- [ ] Early\n### Step 1: Setup\n"
        )
        violations = self._assert_invalid(content)
        assert any("1 checkboxes affected" in v for v in violations)

    def test_step_without_checkboxes(self) -> None:
        content = VALID.replace(
            "## Pull Request", "### Step 3: Empty step\n\n## Pull Request"
        )
        violations = self._assert_invalid(content)
        assert any("has no checkboxes" in v and "Step 3" in v for v in violations)

    @pytest.mark.parametrize("header", ["### Notes", "## Code Review", "#### Notes"])
    def test_foreign_header_inside_tasks(self, header: str) -> None:
        content = VALID.replace(
            "### Step 2: More", f"{header}\nsome text\n\n### Step 2: More"
        )
        violations = self._assert_invalid(content)
        assert any(f"header '{header}'" in v for v in violations)

    def test_step_after_pull_request(self) -> None:
        content = VALID + "\n### Step 3: Late\n- [ ] Late task\n"
        violations = self._assert_invalid(content)
        assert any("is outside '## Tasks'" in v for v in violations)

    def test_missing_pull_request(self) -> None:
        content = VALID.split("## Pull Request")[0]
        violations = self._assert_invalid(content)
        assert any("no '## Pull Request' section" in v for v in violations)

    def test_pull_request_without_checkbox(self) -> None:
        content = VALID.replace("- [ ] PR review\n", "")
        violations = self._assert_invalid(content)
        assert any("has no checkboxes" in v for v in violations)

    def test_template_with_step_after_pull_request_is_invalid(self) -> None:
        content = TASK_TRACKER_TEMPLATE + "### Step 1: x\n- [ ] task\n"
        state, _ = classify_tracker_content(content)
        assert state is TrackerState.INVALID

    def test_violation_carries_file_line_number(self) -> None:
        lines = [f"line {i}" for i in range(1, 22)]
        lines[0] = "# Task Status Tracker"
        content = "\n".join(lines) + "\n## Tasks\n\n\n\n- [ ] orphan\n## Pull Request\n"
        # "## Tasks" is line 22, the orphan checkbox line 26.
        _, violations = classify_tracker_content(content)
        assert any(v.startswith("pr_info/TASK_TRACKER.md line 26:") for v in violations)


class TestParserAgreement:
    """Classifier and lenient parser agree on where ``## Tasks`` ends."""

    @pytest.mark.parametrize(
        "pr_header", ["## Pull Request", "### Pull Request", "#### Pull Request"]
    )
    def test_tasks_end_matches_parser(self, tmp_path: Path, pr_header: str) -> None:
        content = VALID.replace("## Pull Request", pr_header)
        (tmp_path / "TASK_TRACKER.md").write_text(content, encoding="utf-8")

        assert classify_tracker_content(content) == (TrackerState.POPULATED, [])

        records = _scan_tracker(content)
        task_boxes = [
            r for r in records if r.section == "tasks" and r.checked is not None
        ]
        total, completed = get_task_counts(str(tmp_path))
        assert len(task_boxes) == total
        assert sum(1 for r in task_boxes if r.checked) == completed

        pr_box = next(r for r in records if r.name == "pr review")
        assert pr_box.section == "pull_request"


class TestClassifyTaskTracker:
    """File-level wrapper."""

    def test_missing_file(self, tmp_path: Path) -> None:
        assert classify_task_tracker(str(tmp_path)) == (TrackerState.MISSING, [])

    def test_reads_file(self, tmp_path: Path) -> None:
        (tmp_path / "TASK_TRACKER.md").write_text(VALID, encoding="utf-8")
        assert classify_task_tracker(str(tmp_path)) == (TrackerState.POPULATED, [])


def test_describe_violations_includes_lines_and_format() -> None:
    text = describe_violations(["pr_info/TASK_TRACKER.md line 3: bad"])
    assert "pr_info/TASK_TRACKER.md line 3: bad" in text
    assert "Tasks must be grouped" in text
    assert EXPECTED_FORMAT in text

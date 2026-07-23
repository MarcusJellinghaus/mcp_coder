"""Tests for the review log writer (Step 6)."""

from datetime import date
from pathlib import Path

from mcp_coder.workflows.review.config import REVIEW_IMPLEMENTATION, REVIEW_PLAN
from mcp_coder.workflows.review.review_log import next_run_number, write_round_log


class TestNextRunNumber:
    """Allocation of the run number from existing log files."""

    def test_starts_at_one_when_no_pr_info(self, tmp_path: Path) -> None:
        assert next_run_number(tmp_path, REVIEW_IMPLEMENTATION) == 1

    def test_starts_at_one_when_empty(self, tmp_path: Path) -> None:
        (tmp_path / "pr_info").mkdir()
        assert next_run_number(tmp_path, REVIEW_IMPLEMENTATION) == 1

    def test_increments_past_existing(self, tmp_path: Path) -> None:
        pr_info = tmp_path / "pr_info"
        pr_info.mkdir()
        (pr_info / "implementation_review_log_1.md").write_text("x")
        (pr_info / "implementation_review_log_2.md").write_text("x")
        assert next_run_number(tmp_path, REVIEW_IMPLEMENTATION) == 3

    def test_uses_highest_not_count(self, tmp_path: Path) -> None:
        pr_info = tmp_path / "pr_info"
        pr_info.mkdir()
        (pr_info / "implementation_review_log_5.md").write_text("x")
        assert next_run_number(tmp_path, REVIEW_IMPLEMENTATION) == 6

    def test_ignores_other_stems(self, tmp_path: Path) -> None:
        pr_info = tmp_path / "pr_info"
        pr_info.mkdir()
        (pr_info / "plan_review_log_4.md").write_text("x")
        assert next_run_number(tmp_path, REVIEW_IMPLEMENTATION) == 1

    def test_distinct_stems_independent(self, tmp_path: Path) -> None:
        pr_info = tmp_path / "pr_info"
        pr_info.mkdir()
        (pr_info / "implementation_review_log_3.md").write_text("x")
        assert next_run_number(tmp_path, REVIEW_PLAN) == 1


class TestWriteRoundLog:
    """Creation and appending of round blocks."""

    def test_creates_file_with_header_on_round_one(self, tmp_path: Path) -> None:
        path = write_round_log(
            tmp_path,
            REVIEW_IMPLEMENTATION,
            run_number=1,
            round_number=1,
            findings="a finding",
            decisions="a decision",
            changes="a change",
        )
        assert path == tmp_path / "pr_info" / "implementation_review_log_1.md"
        assert path.exists()
        content = path.read_text(encoding="utf-8")
        assert "# review-implementation review log 1" in content
        assert "## Round 1" in content
        assert date.today().isoformat() in content
        assert "a finding" in content
        assert "a decision" in content
        assert "a change" in content

    def test_creates_pr_info_dir_if_missing(self, tmp_path: Path) -> None:
        assert not (tmp_path / "pr_info").exists()
        write_round_log(
            tmp_path,
            REVIEW_PLAN,
            run_number=1,
            round_number=1,
            findings="f",
            decisions="d",
            changes="c",
        )
        assert (tmp_path / "pr_info" / "plan_review_log_1.md").exists()

    def test_appends_second_round_without_new_header(self, tmp_path: Path) -> None:
        write_round_log(
            tmp_path,
            REVIEW_IMPLEMENTATION,
            run_number=1,
            round_number=1,
            findings="f1",
            decisions="d1",
            changes="c1",
        )
        path = write_round_log(
            tmp_path,
            REVIEW_IMPLEMENTATION,
            run_number=1,
            round_number=2,
            findings="f2",
            decisions="d2",
            changes="c2",
        )
        content = path.read_text(encoding="utf-8")
        assert content.count("# review-implementation review log 1") == 1
        assert "## Round 1" in content
        assert "## Round 2" in content
        assert "f1" in content and "f2" in content

    def test_escalate_reason_rendered_when_given(self, tmp_path: Path) -> None:
        path = write_round_log(
            tmp_path,
            REVIEW_IMPLEMENTATION,
            run_number=2,
            round_number=1,
            findings="f",
            decisions="d",
            changes="c",
            escalate_reason="needs human eyes",
        )
        content = path.read_text(encoding="utf-8")
        assert "**Escalate reason**: needs human eyes" in content

    def test_escalate_reason_absent_by_default(self, tmp_path: Path) -> None:
        path = write_round_log(
            tmp_path,
            REVIEW_IMPLEMENTATION,
            run_number=1,
            round_number=1,
            findings="f",
            decisions="d",
            changes="c",
        )
        assert "Escalate reason" not in path.read_text(encoding="utf-8")

    def test_run_number_reflected_in_filename_and_header(self, tmp_path: Path) -> None:
        path = write_round_log(
            tmp_path,
            REVIEW_PLAN,
            run_number=7,
            round_number=1,
            findings="f",
            decisions="d",
            changes="c",
        )
        assert path.name == "plan_review_log_7.md"
        assert "review log 7" in path.read_text(encoding="utf-8")

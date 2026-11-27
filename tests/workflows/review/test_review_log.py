"""Tests for the review log writer (Step 6)."""

from datetime import date
from pathlib import Path

import pytest

from mcp_coder.workflows.review import review_log
from mcp_coder.workflows.review.config import REVIEW_IMPLEMENTATION, REVIEW_PLAN
from mcp_coder.workflows.review.review_log import next_run_number, write_round_log

_BLOCK_LABELS = {"**Findings**:", "**Decisions**:", "**Changes**:"}


class _FixedDate:
    """Stand-in for ``datetime.date`` whose ``today()`` is fixed."""

    @staticmethod
    def today() -> date:
        return date(2026, 1, 2)


@pytest.fixture
def fixed_date(monkeypatch: pytest.MonkeyPatch) -> str:
    """Pin the date the round log writes into each round heading."""
    monkeypatch.setattr(review_log, "date", _FixedDate)
    return _FixedDate.today().isoformat()


def _read(path: Path) -> str:
    return path.read_bytes().decode("utf-8")


def _assert_formatter_stable(text: str) -> None:
    """Assert the markdown layout a formatter would leave unchanged."""
    assert not text.startswith("\n")
    assert text.endswith("\n") and not text.endswith("\n\n")
    assert "\n\n\n" not in text
    lines = text.split("\n")[:-1]
    for index, line in enumerate(lines):
        if line.startswith("# ") or line.startswith("## "):
            assert lines[index + 1] == "", f"no blank line after {line!r}"
            if index > 0:
                assert lines[index - 1] == "", f"no blank line before {line!r}"
        if line in _BLOCK_LABELS:
            assert lines[index + 1] == "", f"no blank line after {line!r}"
        if line.startswith("**Escalate reason**:"):
            assert line == "**Escalate reason**: x"


class TestWriteRoundLogGolden:
    """Exact text of the round log."""

    def test_one_round(self, tmp_path: Path, fixed_date: str) -> None:
        path = write_round_log(
            tmp_path,
            REVIEW_IMPLEMENTATION,
            run_number=1,
            round_number=1,
            findings=" f \n",
            decisions="d",
            changes="c",
        )
        assert _read(path) == (
            "# review-implementation review log 1\n"
            "\n"
            f"## Round 1 — {fixed_date}\n"
            "\n"
            "**Findings**:\n"
            "\n"
            "f\n"
            "\n"
            "**Decisions**:\n"
            "\n"
            "d\n"
            "\n"
            "**Changes**:\n"
            "\n"
            "c\n"
        )

    def test_two_rounds_with_escalate_reason(
        self, tmp_path: Path, fixed_date: str
    ) -> None:
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
            escalate_reason=" why \n",
        )
        assert _read(path) == (
            "# review-implementation review log 1\n"
            "\n"
            f"## Round 1 — {fixed_date}\n"
            "\n"
            "**Findings**:\n"
            "\n"
            "f1\n"
            "\n"
            "**Decisions**:\n"
            "\n"
            "d1\n"
            "\n"
            "**Changes**:\n"
            "\n"
            "c1\n"
            "\n"
            f"## Round 2 — {fixed_date}\n"
            "\n"
            "**Findings**:\n"
            "\n"
            "f2\n"
            "\n"
            "**Decisions**:\n"
            "\n"
            "d2\n"
            "\n"
            "**Changes**:\n"
            "\n"
            "c2\n"
            "\n"
            "**Escalate reason**: why\n"
        )

    def test_later_round_on_missing_file_starts_with_heading(
        self, tmp_path: Path, fixed_date: str
    ) -> None:
        path = write_round_log(
            tmp_path,
            REVIEW_IMPLEMENTATION,
            run_number=1,
            round_number=3,
            findings="f",
            decisions="d",
            changes="c",
        )
        assert _read(path).startswith(f"## Round 3 — {fixed_date}\n\n**Findings**:\n")


class TestWriteRoundLogInvariants:
    """Formatter-stable layout across input shapes."""

    @pytest.mark.parametrize(
        ("findings", "escalate_reason"),
        [
            pytest.param("plain text", None, id="plain"),
            pytest.param("- a\n- b", None, id="starts-with-list"),
            pytest.param("intro\n- a\n- b", None, id="ends-with-list"),
            pytest.param("\n\n  padded  \n\n", None, id="surrounding-blank-lines"),
            pytest.param("plain text", "x", id="escalate"),
            pytest.param("- a\n- b\n", " x \n", id="list-and-escalate"),
        ],
    )
    def test_layout_after_each_round(
        self, tmp_path: Path, findings: str, escalate_reason: str | None
    ) -> None:
        for round_number in (1, 2):
            path = write_round_log(
                tmp_path,
                REVIEW_IMPLEMENTATION,
                run_number=1,
                round_number=round_number,
                findings=findings,
                decisions="\nd\n",
                changes="c",
                escalate_reason=escalate_reason,
            )
            text = _read(path)
            _assert_formatter_stable(text)
            if escalate_reason:
                assert text.count("**Escalate reason**: x\n") == round_number


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

    def test_round_log_bytes_have_no_crlf(self, tmp_path: Path) -> None:
        path = write_round_log(
            tmp_path,
            REVIEW_IMPLEMENTATION,
            run_number=1,
            round_number=1,
            findings="f",
            decisions="d",
            changes="c",
        )
        assert b"\r" not in path.read_bytes()

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

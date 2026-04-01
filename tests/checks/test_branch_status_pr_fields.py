"""Tests for PR fields in BranchStatusReport.

Tests the optional PR fields (pr_number, pr_url, pr_found) added to
BranchStatusReport, and their display in format_for_human() and format_for_llm().
"""

from mcp_coder.checks.branch_status import (
    CI_PASSED,
    BranchStatusReport,
    create_empty_report,
)


def _make_report(
    pr_found: bool | None = None,
    pr_number: int | None = None,
    pr_url: str | None = None,
) -> BranchStatusReport:
    """Create a BranchStatusReport with given PR fields and sensible defaults."""
    return BranchStatusReport(
        branch_name="feature/42-thing",
        base_branch="main",
        ci_status=CI_PASSED,
        ci_details=None,
        rebase_needed=False,
        rebase_reason="Up to date",
        tasks_complete=True,
        current_github_label="status-03:implementing",
        recommendations=["Ready to merge"],
        pr_found=pr_found,
        pr_number=pr_number,
        pr_url=pr_url,
    )


def test_report_without_pr_fields() -> None:
    """Default None fields — human/LLM output unchanged (no PR section)."""
    report = _make_report()

    assert report.pr_found is None
    assert report.pr_number is None
    assert report.pr_url is None

    human = report.format_for_human()
    assert "PR" not in human

    llm = report.format_for_llm()
    assert "PR=" not in llm


def test_report_with_pr_found() -> None:
    """pr_found=True — human shows PR line, LLM shows PR=#123."""
    report = _make_report(
        pr_found=True,
        pr_number=123,
        pr_url="https://github.com/org/repo/pull/123",
    )

    human = report.format_for_human()
    assert "PR:" in human
    assert "#123" in human
    assert "https://github.com/org/repo/pull/123" in human
    assert "✅" in human.split("PR:")[1].split("\n")[0]

    llm = report.format_for_llm()
    assert "PR=#123" in llm


def test_report_with_pr_not_found() -> None:
    """pr_found=False — human shows 'No PR found', LLM shows PR=NOT_FOUND."""
    report = _make_report(pr_found=False)

    human = report.format_for_human()
    assert "PR:" in human
    assert "No PR found" in human
    assert "❌" in human.split("PR:")[1].split("\n")[0]

    llm = report.format_for_llm()
    assert "PR=NOT_FOUND" in llm


def test_empty_report_has_pr_defaults() -> None:
    """create_empty_report() returns None for all PR fields."""
    report = create_empty_report()

    assert report.pr_found is None
    assert report.pr_number is None
    assert report.pr_url is None

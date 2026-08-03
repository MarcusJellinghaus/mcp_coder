"""Table-driven tests for the pure severity parser (Step 1).

The backstop must detect the SEVERITY token only in its anchored
``<sep> SEVERITY <sep>`` position in a ``file:line — SEVERITY — desc`` finding
line, and must tolerate the formatting a fresh reviewer LLM actually emits
(em-dash *or* ASCII hyphen separators; optionally backticked severity token).
"""

import pytest

from mcp_coder.workflows.review.severity import max_severity


class TestSingleFinding:
    """A single finding line of each level returns that level."""

    def test_critical(self) -> None:
        assert max_severity("`src/x.py:10` — critical — boom") == "critical"

    def test_high(self) -> None:
        assert max_severity("`src/x.py:10` — high — leak") == "high"

    def test_medium(self) -> None:
        assert max_severity("`src/x.py:10` — medium — smell") == "medium"

    def test_low(self) -> None:
        assert max_severity("`src/x.py:10` — low — nit") == "low"


class TestMixedReport:
    """The highest severity present wins regardless of order."""

    def test_low_and_high(self) -> None:
        report = "`src/a.py:1` — low — nit\n`src/b.py:2` — high — leak\n"
        assert max_severity(report) == "high"

    def test_all_levels(self) -> None:
        report = (
            "`a:1` — low — x\n"
            "`b:2` — medium — y\n"
            "`c:3` — critical — z\n"
            "`d:4` — high — w\n"
        )
        assert max_severity(report) == "critical"


class TestNoFindings:
    """Reports without an anchored finding line return None (fail-open)."""

    def test_no_findings_marker(self) -> None:
        assert max_severity("NO FINDINGS") is None

    def test_empty(self) -> None:
        assert max_severity("") is None

    def test_prose_without_finding_line(self) -> None:
        assert max_severity("The reviewer looked and saw nothing of note.") is None


class TestCaseInsensitivity:
    """The severity token matches case-insensitively."""

    def test_upper(self) -> None:
        assert max_severity("`src/x.py:10` — HIGH — leak") == "high"

    def test_mixed_case(self) -> None:
        assert max_severity("`src/x.py:10` — Critical — boom") == "critical"


class TestFormattingTolerance:
    """Tolerate hyphen separators and backticked tokens the LLM may emit.

    A bare-em-dash-only regex passes the other tests while silently no-op'ing in
    production; these cases defend the fail-open path that would break AC1.
    """

    def test_hyphen_separators(self) -> None:
        assert max_severity("`src/x.py:10` - high - desc") == "high"

    def test_backticked_token(self) -> None:
        assert max_severity("`src/x.py:10` — `high` — desc") == "high"

    def test_hyphen_and_backticked(self) -> None:
        assert max_severity("`src/x.py:10` - `high` - desc") == "high"

    def test_multiple_hyphens(self) -> None:
        assert max_severity("`src/x.py:10` -- high -- desc") == "high"

    def test_hyphen_all_low_downgrades(self) -> None:
        # A hyphen-separated all-low/medium report must return the finding max,
        # never None — proving the Step 5 backstop still downgrades to dismiss.
        report = "`a:1` - low - nit\n`b:2` - medium - smell\n"
        assert max_severity(report) == "medium"


class TestAnchoring:
    """A severity word outside the anchored position must not raise the ceiling."""

    def test_severity_word_in_description(self) -> None:
        # A `low` finding described as "high coupling" must stay "low".
        report = "src/x.py:10 — low — high coupling between modules"
        assert max_severity(report) == "low"

    def test_summary_line_does_not_count(self) -> None:
        # All-low/medium finding lines plus a "No critical/high findings" summary
        # must return the finding max, not "high".
        report = (
            "`a:1` — low — nit\n"
            "`b:2` — medium — smell\n"
            "Summary: No critical/high findings.\n"
        )
        assert max_severity(report) == "medium"

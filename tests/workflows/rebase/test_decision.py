"""Tests for the pure decision logic in ``workflows/rebase.py``.

Covers outcome-marker parsing (``_parse_outcome_marker``) and the
worst-case-wins pre-push decision (``_evaluate_pre_push``). Both functions are
pure (no git, stdlib only), so these are plain unit tests.
"""

import pytest

from mcp_coder.workflows.rebase import _evaluate_pre_push, _parse_outcome_marker


class TestParseOutcomeMarker:
    """Unit tests for ``_parse_outcome_marker``."""

    def test_success_marker_with_na_reason(self) -> None:
        """A success marker with ``n/a`` reason yields ``("success", None)``."""
        response = "REBASE_OUTCOME: success\nREBASE_REASON: n/a"
        assert _parse_outcome_marker(response) == ("success", None)

    def test_aborted_marker_with_reason(self) -> None:
        """An aborted marker keeps its human-readable reason text."""
        response = "REBASE_OUTCOME: aborted\nREBASE_REASON: conflict in X"
        assert _parse_outcome_marker(response) == ("aborted", "conflict in X")

    def test_missing_marker(self) -> None:
        """No outcome marker yields ``(None, None)``."""
        response = "The rebase finished but I forgot to emit a marker."
        assert _parse_outcome_marker(response) == (None, None)

    def test_outcome_is_case_insensitive(self) -> None:
        """Outcome value is normalized to lowercase."""
        response = "REBASE_OUTCOME: SUCCESS\nREBASE_REASON: n/a"
        assert _parse_outcome_marker(response) == ("success", None)

    def test_ignores_unrelated_text(self) -> None:
        """Surrounding prose does not confuse the parser."""
        response = (
            "Here is a summary of what I did.\n"
            "REBASE_OUTCOME: aborted\n"
            "REBASE_REASON: unknown conflict in build.rs\n"
            "Please review manually.\n"
        )
        assert _parse_outcome_marker(response) == (
            "aborted",
            "unknown conflict in build.rs",
        )

    def test_unrecognized_outcome_value_is_none(self) -> None:
        """An outcome value outside {success, aborted} is treated as unparseable."""
        response = "REBASE_OUTCOME: maybe\nREBASE_REASON: n/a"
        assert _parse_outcome_marker(response) == (None, None)

    def test_last_match_wins_for_outcome(self) -> None:
        """When multiple markers appear, the last one wins."""
        response = (
            "REBASE_OUTCOME: aborted\n"
            "REBASE_REASON: first attempt failed\n"
            "REBASE_OUTCOME: success\n"
            "REBASE_REASON: n/a\n"
        )
        assert _parse_outcome_marker(response) == ("success", None)

    def test_reason_na_is_case_insensitive(self) -> None:
        """A reason of ``N/A`` (any case) is normalized to ``None``."""
        response = "REBASE_OUTCOME: success\nREBASE_REASON: N/A"
        assert _parse_outcome_marker(response) == ("success", None)

    def test_empty_response(self) -> None:
        """An empty response yields ``(None, None)``."""
        assert _parse_outcome_marker("") == (None, None)


class TestEvaluatePrePush:
    """Truth table for ``_evaluate_pre_push`` (worst-case-wins)."""

    @pytest.mark.parametrize("marker_outcome", ["success", "aborted", None])
    @pytest.mark.parametrize("rebase_success_shape", [True, False])
    def test_mid_rebase_always_aborts(
        self, marker_outcome: str | None, rebase_success_shape: bool
    ) -> None:
        """Still mid-rebase → abort regardless of the other signals."""
        assert (
            _evaluate_pre_push(
                mid_rebase=True,
                marker_outcome=marker_outcome,
                rebase_success_shape=rebase_success_shape,
            )
            == "abort"
        )

    def test_marker_aborted_aborts_even_with_success_shape(self) -> None:
        """Self-reported abort is trusted even when git looks successful."""
        assert (
            _evaluate_pre_push(
                mid_rebase=False,
                marker_outcome="aborted",
                rebase_success_shape=True,
            )
            == "abort"
        )

    def test_success_marker_without_success_shape_aborts(self) -> None:
        """Git cannot corroborate a claimed success → abort."""
        assert (
            _evaluate_pre_push(
                mid_rebase=False,
                marker_outcome="success",
                rebase_success_shape=False,
            )
            == "abort"
        )

    def test_unparseable_marker_with_success_shape_pushes(self) -> None:
        """Unparseable marker but git confirms success → push."""
        assert (
            _evaluate_pre_push(
                mid_rebase=False,
                marker_outcome=None,
                rebase_success_shape=True,
            )
            == "push"
        )

    def test_success_marker_with_success_shape_pushes(self) -> None:
        """Success marker corroborated by git → push."""
        assert (
            _evaluate_pre_push(
                mid_rebase=False,
                marker_outcome="success",
                rebase_success_shape=True,
            )
            == "push"
        )

"""Tests for the pure liveness layer (``assess_liveness``).

Full rule matrix, no Windows — the #38 de-risker. The rule order is the
contract: title -> pid -> cmdline -> folder-existence. PID is a tie-breaker,
not a gate.
"""

from mcp_coder.workflows.vscodeclaude.assessment import assess_liveness
from mcp_coder.workflows.vscodeclaude.types import (
    DetectionSignals,
    LivenessRule,
    LivenessVerdict,
)


def _signals(
    *,
    folder_exists: bool = True,
    title_match: bool = False,
    cmdline_match: bool = False,
    pid_alive: bool = False,
    found_pid: int | None = None,
    age_seconds: float = 0.0,
    within_grace: bool = False,
    directory_empty: bool = False,
) -> DetectionSignals:
    """Build DetectionSignals with everything off by default."""
    return DetectionSignals(
        folder_exists=folder_exists,
        title_match=title_match,
        cmdline_match=cmdline_match,
        pid_alive=pid_alive,
        found_pid=found_pid,
        age_seconds=age_seconds,
        within_grace=within_grace,
        directory_empty=directory_empty,
    )


class TestAssessLiveness:
    """Full rule matrix for the pure liveness verdict."""

    def test_title_hit_cmdline_miss_restores_38(self) -> None:
        """Title positive wins even when cmdline misses (the #38 restore case)."""
        verdict = assess_liveness(
            _signals(title_match=True, cmdline_match=False, pid_alive=False)
        )
        assert verdict == LivenessVerdict(active=True, rule=LivenessRule.TITLE)

    def test_bare_folder_cmdline_fallthrough(self) -> None:
        """Title miss + cmdline hit falls through to CMDLINE."""
        verdict = assess_liveness(
            _signals(title_match=False, pid_alive=False, cmdline_match=True)
        )
        assert verdict == LivenessVerdict(active=True, rule=LivenessRule.CMDLINE)

    def test_pid_alive_only(self) -> None:
        """PID alive (title + cmdline miss) yields ACTIVE via PID tie-breaker."""
        verdict = assess_liveness(
            _signals(title_match=False, pid_alive=True, cmdline_match=False)
        )
        assert verdict == LivenessVerdict(active=True, rule=LivenessRule.PID)

    def test_all_miss_folder_exists(self) -> None:
        """Everything misses but folder exists -> INACTIVE(NO_MATCH)."""
        verdict = assess_liveness(_signals(folder_exists=True))
        assert verdict == LivenessVerdict(active=False, rule=LivenessRule.NO_MATCH)

    def test_all_miss_folder_gone(self) -> None:
        """Everything misses and folder gone -> INACTIVE(NO_ARTIFACTS)."""
        verdict = assess_liveness(_signals(folder_exists=False))
        assert verdict == LivenessVerdict(active=False, rule=LivenessRule.NO_ARTIFACTS)

    def test_zombie_precursor_folder_gone_pid_alive(self) -> None:
        """Folder gone but PID alive -> ACTIVE(PID): no folder-gone short-circuit."""
        verdict = assess_liveness(_signals(folder_exists=False, pid_alive=True))
        assert verdict == LivenessVerdict(active=True, rule=LivenessRule.PID)

    def test_title_wins_over_pid_and_cmdline(self) -> None:
        """Title is authoritative even when pid and cmdline also match."""
        verdict = assess_liveness(
            _signals(title_match=True, pid_alive=True, cmdline_match=True)
        )
        assert verdict == LivenessVerdict(active=True, rule=LivenessRule.TITLE)

    def test_pid_wins_over_cmdline(self) -> None:
        """PID precedes cmdline in the rule order."""
        verdict = assess_liveness(
            _signals(title_match=False, pid_alive=True, cmdline_match=True)
        )
        assert verdict == LivenessVerdict(active=True, rule=LivenessRule.PID)

    def test_returns_frozen_verdict(self) -> None:
        """The verdict is a LivenessVerdict instance."""
        verdict = assess_liveness(_signals(title_match=True))
        assert isinstance(verdict, LivenessVerdict)

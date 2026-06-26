"""Pure assessment layers for vscodeclaude session state.

This module is the ``assess`` stage of the detect -> assess -> decide ->
render/apply pipeline. Every function here is PURE: it imports only ``types``
(no ``sessions``/``psutil``/``win32``), so the rule matrix is unit-testable
without Windows.
"""

from .types import DetectionSignals, LivenessRule, LivenessVerdict


def assess_liveness(signals: DetectionSignals) -> LivenessVerdict:
    """Pure liveness verdict. Returns a frozen ``LivenessVerdict(active, rule)``.

    Ordering is the contract: a live process is detectable regardless of folder
    state, so the order is title -> pid -> cmdline -> folder-existence. PID is a
    tie-breaker, NOT a gate, and there is no folder-gone short-circuit (a live
    process for a deleted folder stays reachable as the zombie precursor).
    """
    if signals.title_match:
        return LivenessVerdict(active=True, rule=LivenessRule.TITLE)
    if signals.pid_alive:
        return LivenessVerdict(active=True, rule=LivenessRule.PID)
    if signals.cmdline_match:
        return LivenessVerdict(active=True, rule=LivenessRule.CMDLINE)
    if not signals.folder_exists:
        return LivenessVerdict(active=False, rule=LivenessRule.NO_ARTIFACTS)
    return LivenessVerdict(active=False, rule=LivenessRule.NO_MATCH)

"""Single source of truth for the CI-status -> verdict policy.

`assess_ci` maps a :class:`CIStatus` to one of three verdicts. It is the sole
implementation of this policy, called by the CLI ``_exit_code`` and pre-``--fix``
bail-out (``require_proven=False``) and by the review Gate 2 exit guard
(``require_proven=True``).

The ``require_proven`` flag distinguishes "not obviously red" (CLI) from "proven
green" (Gate 2): the transient/soft states (``PENDING``, ``NOT_CONFIGURED``, and
any future member) are ``"ok"`` when a proof is not required, but
``"undeterminable"`` when it is. Only ``PASSED``/``FAILED`` are decisive in both
modes; ``UNKNOWN``/``UNAVAILABLE`` are always undeterminable. Using an allowlist
(only ``PASSED`` is ``"ok"`` under ``require_proven``) degrades safely if upstream
adds a new ``CIStatus`` member.
"""

from typing import Literal

from mcp_coder.checks.branch_status import CIStatus


def assess_ci(
    status: CIStatus, *, require_proven: bool
) -> Literal["ok", "failed", "undeterminable"]:
    """Map a CI status to a verdict.

    Args:
        status: The observed CI pipeline status.
        require_proven: When True, only ``PASSED`` counts as ``"ok"`` (proven
            green); the soft states become ``"undeterminable"``. When False,
            the soft states are treated as ``"ok"`` (not obviously red).

    Returns:
        ``"ok"`` if the status is acceptable, ``"failed"`` if the CI is
        determined to have failed, ``"undeterminable"`` if the truth cannot be
        established (or, under ``require_proven``, is not proven green).
    """
    if status is CIStatus.PASSED:
        return "ok"
    if status is CIStatus.FAILED:
        return "failed"
    if status in (CIStatus.UNKNOWN, CIStatus.UNAVAILABLE):
        return "undeterminable"
    # PENDING, NOT_CONFIGURED, and any future member.
    return "undeterminable" if require_proven else "ok"

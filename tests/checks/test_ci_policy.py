"""Tests for the assess_ci CI-status -> verdict policy.

Pure function; no mocking. Parametrize all six CIStatus members across both
require_proven modes. See pr_info/steps/step_1.md.
"""

import pytest

from mcp_coder.checks.branch_status import CIStatus
from mcp_coder.checks.ci_policy import assess_ci


class TestAssessCi:
    """The status -> verdict mapping under both require_proven modes."""

    @pytest.mark.parametrize("require_proven", [False, True])
    def test_passed_is_ok(self, require_proven: bool) -> None:
        assert assess_ci(CIStatus.PASSED, require_proven=require_proven) == "ok"

    @pytest.mark.parametrize("require_proven", [False, True])
    def test_failed_is_failed(self, require_proven: bool) -> None:
        assert assess_ci(CIStatus.FAILED, require_proven=require_proven) == "failed"

    @pytest.mark.parametrize("require_proven", [False, True])
    def test_unknown_is_undeterminable(self, require_proven: bool) -> None:
        assert (
            assess_ci(CIStatus.UNKNOWN, require_proven=require_proven)
            == "undeterminable"
        )

    @pytest.mark.parametrize("require_proven", [False, True])
    def test_unavailable_is_undeterminable(self, require_proven: bool) -> None:
        assert (
            assess_ci(CIStatus.UNAVAILABLE, require_proven=require_proven)
            == "undeterminable"
        )

    @pytest.mark.parametrize("status", [CIStatus.PENDING, CIStatus.NOT_CONFIGURED])
    def test_soft_states_are_ok_when_not_proven(self, status: CIStatus) -> None:
        assert assess_ci(status, require_proven=False) == "ok"

    @pytest.mark.parametrize("status", [CIStatus.PENDING, CIStatus.NOT_CONFIGURED])
    def test_soft_states_undeterminable_when_proven(self, status: CIStatus) -> None:
        assert assess_ci(status, require_proven=True) == "undeterminable"

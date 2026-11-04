"""Tests for _check_alerts() and its place in the check_pr_health chain."""

import logging
from typing import Any
from unittest.mock import MagicMock

import pytest

from mcp_coder.mcp_workspace_github import GitHubRateLimitError
from mcp_coder.utils.log_utils import OUTPUT
from tests.workflows.vscodeclaude._review_comments_helpers import (
    MOCK_REVIEW_LABELS_CONFIG,
    _output_messages,
)
from tests.workflows.vscodeclaude.test_checks import (
    CHECKS,
    _make_pr,
    _make_pr_issue,
    _run,
    _setup,
)

REVIEW_LABEL = "status-91:pr-review-comments"

ALERT: dict[str, Any] = {
    "number": 51,
    "rule_id": "py/sql-injection",
    "rule_description": "SQL injection",
    "message": "This query depends on user input",
    "path": "src/x.py",
    "line": 1,
}
OPEN_ALERTS: dict[str, Any] = {"alerts": [ALERT], "skipped": None, "final": True}


def _setup_alerts(
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[MagicMock, MagicMock]:
    """Patch the environment so that a status-91 escalation can succeed.

    Returns:
        ``(issue_manager, pr_cache)``.
    """
    issue_manager, _, _, pr_cache = _setup(monkeypatch)
    monkeypatch.setattr(
        "mcp_coder.workflow_utils.label_transitions.load_labels_config",
        lambda *a, **k: MOCK_REVIEW_LABELS_CONFIG,
    )
    return issue_manager, pr_cache


class TestCheckAlertsEscalation:
    """Which alerts results move the issue to status-91."""

    def test_open_alerts_escalate(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Alerts with no other feedback and green CI escalate to status-91."""
        issue_manager, pr_cache = _setup_alerts(monkeypatch)
        pr_cache.ci_status.return_value = {
            "run": {"status": "completed", "conclusion": "success"},
            "jobs": [],
        }
        pr_cache.alerts.return_value = OPEN_ALERTS
        issue = _make_pr_issue(20)

        _run(issue)

        pr_cache.alerts.assert_called_once_with(pr_cache.find_pr.return_value, issue)
        issue_manager.transition_issue_label.assert_called_once()
        call_args = issue_manager.transition_issue_label.call_args
        assert call_args[0][0] == 20
        assert call_args[0][1] == REVIEW_LABEL

    def test_alert_hit_skips_review_comments(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """First hit wins: an alert hit never reaches the review-comments check."""
        issue_manager, pr_cache = _setup_alerts(monkeypatch)
        pr_cache.alerts.return_value = OPEN_ALERTS

        _run(_make_pr_issue(20))

        issue_manager.transition_issue_label.assert_called_once()
        pr_cache.feedback.assert_not_called()

    def test_not_final_does_not_escalate(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Alerts from a head whose CI is not final are ignored until a later poll."""
        issue_manager, pr_cache = _setup_alerts(monkeypatch)
        pr_cache.alerts.return_value = {
            "alerts": [ALERT],
            "skipped": None,
            "final": False,
        }

        _run(_make_pr_issue(20))

        issue_manager.transition_issue_label.assert_not_called()
        pr_cache.feedback.assert_called_once()

    def test_final_escalates_while_ci_reports_in_progress(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """``final`` decides, not CI: a run concluded skipped reads as in_progress."""
        issue_manager, pr_cache = _setup_alerts(monkeypatch)
        pr_cache.ci_status.return_value = {
            "run": {"status": "in_progress", "conclusion": None},
            "jobs": [],
        }
        pr_cache.alerts.return_value = OPEN_ALERTS

        _run(_make_pr_issue(20))

        issue_manager.transition_issue_label.assert_called_once()
        assert issue_manager.transition_issue_label.call_args[0][1] == REVIEW_LABEL

    @pytest.mark.parametrize("status", [403, 404])
    def test_skipped_is_silent(
        self,
        monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
        status: int,
    ) -> None:
        """A repo without code-scanning access: no escalation, no OUTPUT line."""
        issue_manager, pr_cache = _setup_alerts(monkeypatch)
        pr_cache.alerts.return_value = {
            "alerts": [],
            "skipped": status,
            "final": True,
        }

        with caplog.at_level(OUTPUT, logger=CHECKS):
            _run(_make_pr_issue(20))

        issue_manager.transition_issue_label.assert_not_called()
        assert not _output_messages(caplog)

    def test_untrusted_pr_author_logs_one_line(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        """An untrusted PR author: no fetch, no label, only the reworded line."""
        issue_manager, pr_cache = _setup_alerts(monkeypatch)
        pr_cache.find_pr.return_value = {
            **_make_pr(),
            "user": "stranger",
            "author_association": "NONE",
        }
        pr_cache.alerts.return_value = OPEN_ALERTS

        with caplog.at_level(OUTPUT, logger=CHECKS):
            _run(_make_pr_issue(20))

        pr_cache.alerts.assert_not_called()
        issue_manager.transition_issue_label.assert_not_called()
        assert _output_messages(caplog) == [
            "PR-health: test-repo #20: untrusted PR author @stranger"
            " — review comments and alerts not checked"
        ]


class TestCheckAlertsErrors:
    """Only a rate limit escapes _check_alerts."""

    @pytest.mark.parametrize(
        "error",
        [
            pytest.param(RuntimeError("boom"), id="api-failure"),
            pytest.param(AttributeError("alerts"), id="old-mcp-workspace"),
        ],
    )
    def test_error_warns_and_review_comments_still_run(
        self,
        monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
        error: Exception,
    ) -> None:
        """Any other failure is a warning; the next check still runs."""
        issue_manager, pr_cache = _setup_alerts(monkeypatch)
        pr_cache.alerts.side_effect = error

        with caplog.at_level(logging.WARNING, logger=CHECKS):
            _run(_make_pr_issue(20))

        assert any(
            r.levelno == logging.WARNING
            and "Failed to check alerts for issue #20" in r.getMessage()
            for r in caplog.records
        )
        pr_cache.feedback.assert_called_once()
        issue_manager.transition_issue_label.assert_not_called()

    def test_rate_limit_propagates(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A rate limit stops the run instead of being swallowed."""
        _, pr_cache = _setup_alerts(monkeypatch)
        pr_cache.alerts.side_effect = GitHubRateLimitError("limited")

        with pytest.raises(GitHubRateLimitError):
            _run(_make_pr_issue(20))

        pr_cache.feedback.assert_not_called()


class TestCheckAlertsChainPosition:
    """Conflict and failing CI win over alerts; alerts need an open PR."""

    def test_merge_conflict_wins(self, monkeypatch: pytest.MonkeyPatch) -> None:
        issue_manager, _, _, pr_cache = _setup(monkeypatch)
        pr_cache.mergeable_state.return_value = "dirty"
        pr_cache.alerts.return_value = OPEN_ALERTS

        _run(_make_pr_issue(20))

        pr_cache.alerts.assert_not_called()
        call_args = issue_manager.transition_issue_label.call_args
        assert call_args[0][1] == "status-71:merge-conflict"

    def test_failing_ci_wins(self, monkeypatch: pytest.MonkeyPatch) -> None:
        issue_manager, _, _, pr_cache = _setup(monkeypatch)
        pr_cache.ci_status.return_value = {
            "run": {"status": "completed", "conclusion": "failure"},
            "jobs": [],
        }
        pr_cache.alerts.return_value = OPEN_ALERTS

        _run(_make_pr_issue(20))

        pr_cache.alerts.assert_not_called()
        call_args = issue_manager.transition_issue_label.call_args
        assert call_args[0][1] == "status-81:failing-ci"

    def test_no_open_pr_skips_alerts(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _, _, _, pr_cache = _setup(monkeypatch)
        pr_cache.find_pr.return_value = None

        _run(_make_pr_issue(20))

        pr_cache.alerts.assert_not_called()

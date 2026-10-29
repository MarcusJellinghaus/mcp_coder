"""check_pr_health routes every PR query through one run-scoped PullRequestCache."""

from unittest.mock import MagicMock, Mock

import pytest

from mcp_coder.mcp_workspace_github import (
    BranchLookup,
    BranchLookupError,
    GitHubRateLimitError,
)
from mcp_coder.workflows.vscodeclaude.checks import check_pr_health
from tests.workflows.vscodeclaude._review_comments_helpers import _comment
from tests.workflows.vscodeclaude.test_checks import (
    CHECKS,
    REPO_CONFIG,
    _empty_feedback,
    _make_pr,
    _make_pr_issue,
    _setup,
)


class TestPullRequestCacheRouting:
    """Each PR query goes to the cache with ``(pr, issue)``."""

    def test_cache_loaded_once_with_repo_url_manager(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _setup(monkeypatch)
        pr_manager = MagicMock()
        pr_manager_cls = MagicMock(return_value=pr_manager)
        cache_cls = MagicMock()
        monkeypatch.setattr(f"{CHECKS}.PullRequestManager", pr_manager_cls)
        monkeypatch.setattr(f"{CHECKS}.PullRequestCache", cache_cls)

        check_pr_health(
            "test-repo", REPO_CONFIG, [_make_pr_issue(1), _make_pr_issue(2)]
        )

        pr_manager_cls.assert_called_once_with(repo_url="https://github.com/owner/repo")
        cache_cls.load.assert_called_once_with(pr_manager)

    def test_all_five_queries_go_to_cache(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _, _, ci_manager, pr_cache = _setup(monkeypatch)
        pr = _make_pr(7)
        pr_cache.find_pr.return_value = pr
        pr_cache.feedback.return_value = {
            **_empty_feedback(),
            "conversation_comments": [_comment("2024-07-01T00:00:00+00:00")],
        }
        issue = _make_pr_issue(1)

        check_pr_health("test-repo", REPO_CONFIG, [issue])

        pr_cache.find_pr.assert_called_once_with("999-fix")
        pr_cache.mergeable_state.assert_called_once_with(pr, issue)
        pr_cache.ci_status.assert_called_once_with(pr, issue)
        pr_cache.feedback.assert_called_once_with(pr, issue)
        pr_cache.label_events.assert_called_once_with(pr, issue)
        ci_manager.get_latest_ci_status.assert_not_called()

    def test_label_events_skipped_without_feedback_items(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _, _, _, pr_cache = _setup(monkeypatch)

        check_pr_health("test-repo", REPO_CONFIG, [_make_pr_issue(1)])

        pr_cache.feedback.assert_called_once()
        pr_cache.label_events.assert_not_called()

    def test_find_pr_error_degrades_to_ci_only_and_continues(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _, _, ci_manager, pr_cache = _setup(monkeypatch)
        pr = _make_pr(2)
        pr_cache.find_pr.side_effect = [RuntimeError("boom"), pr]
        second = _make_pr_issue(2)

        check_pr_health("test-repo", REPO_CONFIG, [_make_pr_issue(1), second])

        ci_manager.get_latest_ci_status.assert_called_once_with("999-fix")
        pr_cache.mergeable_state.assert_called_once_with(pr, second)
        pr_cache.ci_status.assert_called_once_with(pr, second)
        pr_cache.feedback.assert_called_once_with(pr, second)


class TestPullRequestCacheSave:
    """``save()`` runs once after the loop, also when a rate limit ends it."""

    def test_saved_once_after_loop(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _, _, _, pr_cache = _setup(monkeypatch)

        check_pr_health(
            "test-repo", REPO_CONFIG, [_make_pr_issue(1), _make_pr_issue(2)]
        )

        pr_cache.save.assert_called_once_with()
        assert pr_cache.feedback.call_count == 2

    def test_rate_limit_outside_cache_still_saves(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _, branch_cache, _, pr_cache = _setup(monkeypatch)
        pr_cache.mergeable_state.return_value = "dirty"
        monkeypatch.setattr(
            f"{CHECKS}.update_workflow_label",
            Mock(side_effect=GitHubRateLimitError("limited")),
        )

        with pytest.raises(GitHubRateLimitError):
            check_pr_health(
                "test-repo", REPO_CONFIG, [_make_pr_issue(1), _make_pr_issue(2)]
            )

        assert branch_cache.lookup.call_count == 1
        pr_cache.save.assert_called_once_with()
        branch_cache.save.assert_called_once_with()

    def test_rate_limit_from_find_pr_propagates(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _, branch_cache, ci_manager, pr_cache = _setup(monkeypatch)
        pr_cache.find_pr.side_effect = GitHubRateLimitError("limited")

        with pytest.raises(GitHubRateLimitError):
            check_pr_health(
                "test-repo", REPO_CONFIG, [_make_pr_issue(1), _make_pr_issue(2)]
            )

        assert branch_cache.lookup.call_count == 1
        ci_manager.get_latest_ci_status.assert_not_called()
        pr_cache.save.assert_called_once_with()
        branch_cache.save.assert_called_once_with()

    def test_setup_failure_does_not_save(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _, branch_cache, _, pr_cache = _setup(monkeypatch)
        monkeypatch.setattr(
            f"{CHECKS}.get_github_username", Mock(side_effect=RuntimeError("no token"))
        )

        check_pr_health("test-repo", REPO_CONFIG, [_make_pr_issue(1)])

        pr_cache.save.assert_not_called()
        branch_cache.save.assert_not_called()


class TestBranchLookupCacheInCheckPrHealth:
    """Branch lookups go through one run-scoped ``BranchLookupCache``."""

    def test_cache_loaded_once_and_saved_once(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _, branch_cache, _, _ = _setup(monkeypatch)
        branch_manager = MagicMock()
        branch_manager_cls = MagicMock(return_value=branch_manager)
        cache_cls = MagicMock()
        cache_cls.load.return_value = branch_cache
        monkeypatch.setattr(f"{CHECKS}.IssueBranchManager", branch_manager_cls)
        monkeypatch.setattr(f"{CHECKS}.BranchLookupCache", cache_cls)

        check_pr_health(
            "test-repo", REPO_CONFIG, [_make_pr_issue(1), _make_pr_issue(2)]
        )

        branch_manager_cls.assert_called_once_with(
            repo_url="https://github.com/owner/repo"
        )
        cache_cls.load.assert_called_once_with(branch_manager)
        assert branch_cache.lookup.call_count == 2
        branch_cache.save.assert_called_once_with()

    def test_lookup_error_skips_issue_and_continues(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _, branch_cache, _, pr_cache = _setup(monkeypatch)
        branch_cache.lookup.side_effect = [
            BranchLookupError("boom"),
            BranchLookup("found", "2-fix"),
        ]

        check_pr_health(
            "test-repo", REPO_CONFIG, [_make_pr_issue(1), _make_pr_issue(2)]
        )

        pr_cache.find_pr.assert_called_once_with("2-fix")

    def test_rate_limit_from_lookup_propagates_and_saves_both(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _, branch_cache, _, pr_cache = _setup(monkeypatch)
        branch_cache.lookup.side_effect = GitHubRateLimitError("limited")

        with pytest.raises(GitHubRateLimitError):
            check_pr_health(
                "test-repo", REPO_CONFIG, [_make_pr_issue(1), _make_pr_issue(2)]
            )

        assert branch_cache.lookup.call_count == 1
        pr_cache.find_pr.assert_not_called()
        pr_cache.save.assert_called_once_with()
        branch_cache.save.assert_called_once_with()

    def test_branch_save_runs_when_pr_save_raises(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _, branch_cache, _, pr_cache = _setup(monkeypatch)
        pr_cache.save.side_effect = OSError("disk full")

        with pytest.raises(OSError):
            check_pr_health("test-repo", REPO_CONFIG, [_make_pr_issue(1)])

        branch_cache.save.assert_called_once_with()

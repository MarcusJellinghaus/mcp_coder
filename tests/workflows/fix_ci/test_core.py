"""Tests for the fix_ci workflow (Jenkins-side CI auto-fix loop)."""

from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.llm.interface import LLMTimeoutError
from mcp_coder.llm.providers.claude.claude_code_cli import McpServersUnavailableError
from mcp_coder.workflow_steps import commit
from mcp_coder.workflows.fix_ci import run_fix_ci_workflow
from tests.ci_fix_drive import patch_ci_fix_externals

MODULE = "mcp_coder.workflows.fix_ci.core"
PROJECT_DIR = Path("/fake/project")
BRANCH_NAME = "123-fix-something"
BRANCH_HEAD = "mcp_coder.workflow_utils.failure_handling._branch_head"


@dataclass
class _RefreshMocks:
    sha: MagicMock
    refresh: MagicMock


@pytest.fixture(autouse=True)
def refresh_mocks() -> Iterator[_RefreshMocks]:
    """Keep HEAD unchanged and the PR description refresh mocked by default."""
    with (
        patch(f"{MODULE}.get_latest_commit_sha", return_value="same") as sha,
        patch(f"{MODULE}.refresh_pr_description", return_value=True) as refresh,
    ):
        yield _RefreshMocks(sha=sha, refresh=refresh)


def test_ci_passes_transitions_to_pr_created() -> None:
    with (
        patch(f"{MODULE}.get_current_branch_name", return_value=BRANCH_NAME),
        patch(f"{MODULE}.check_and_fix_ci", return_value=True),
        patch(f"{MODULE}.apply_final_label", return_value=0) as mock_update,
    ):
        result = run_fix_ci_workflow(PROJECT_DIR, "claude", update_issue_labels=True)

    assert result == 0
    mock_update.assert_called_once_with(PROJECT_DIR, "fixing_ci", "pr_created")


def test_final_label_failure_returns_1_without_net() -> None:
    with (
        patch(f"{MODULE}.get_current_branch_name", return_value=BRANCH_NAME),
        patch(f"{MODULE}.check_and_fix_ci", return_value=True),
        patch(f"{MODULE}.apply_final_label", return_value=1),
        patch(
            "mcp_coder.workflow_utils.failure_handling.handle_workflow_failure"
        ) as mock_net,
    ):
        result = run_fix_ci_workflow(PROJECT_DIR, "claude", update_issue_labels=True)

    assert result == 1
    mock_net.assert_not_called()


def test_ci_passes_no_label_update_when_disabled() -> None:
    with (
        patch(f"{MODULE}.get_current_branch_name", return_value=BRANCH_NAME),
        patch(f"{MODULE}.check_and_fix_ci", return_value=True),
        patch(f"{MODULE}.apply_final_label") as mock_update,
    ):
        result = run_fix_ci_workflow(PROJECT_DIR, "claude", update_issue_labels=False)

    assert result == 0
    mock_update.assert_not_called()


def test_ci_exhausted_posts_comment_and_sets_label(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("BUILD_URL", raising=False)
    with (
        patch(f"{MODULE}.get_current_branch_name", return_value=BRANCH_NAME),
        patch(f"{MODULE}.check_and_fix_ci", return_value=False),
        patch(f"{MODULE}.handle_workflow_failure") as mock_handle,
        patch(BRANCH_HEAD, return_value=("feat", "abc1234")),
    ):
        result = run_fix_ci_workflow(
            PROJECT_DIR,
            "claude",
            update_issue_labels=True,
            post_issue_comments=True,
        )

    assert result == 1
    mock_handle.assert_called_once()
    failure = mock_handle.call_args[0][0]
    comment = mock_handle.call_args[0][1]
    assert failure.category == "pr_ci_failed"
    lines = comment.splitlines()
    assert lines[0] == "## ❌ CI Fix Failed"
    assert "**Category:** Ci Fix Exhausted" in lines
    assert "**Stage:** CI pipeline fix" in lines
    assert "**Error:** CI check failed after maximum fix attempts" in lines
    assert "**Branch:** feat @ abc1234" in lines
    assert "**Build:**" not in comment


def test_ci_exhausted_comment_includes_build_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("BUILD_URL", "https://ci.example/job/1/")
    with (
        patch(f"{MODULE}.get_current_branch_name", return_value=BRANCH_NAME),
        patch(f"{MODULE}.check_and_fix_ci", return_value=False),
        patch(f"{MODULE}.handle_workflow_failure") as mock_handle,
        patch(BRANCH_HEAD, return_value=("feat", "abc1234")),
    ):
        run_fix_ci_workflow(PROJECT_DIR, "claude", post_issue_comments=True)

    comment = mock_handle.call_args[0][1]
    assert comment.splitlines()[-1] == "**Build:** https://ci.example/job/1/"


def test_llm_timeout_posts_comment_and_sets_label() -> None:
    with (
        patch(f"{MODULE}.get_current_branch_name", return_value=BRANCH_NAME),
        patch(
            f"{MODULE}.check_and_fix_ci",
            side_effect=LLMTimeoutError("timed out"),
        ),
        patch(f"{MODULE}.handle_workflow_failure") as mock_handle,
        patch(BRANCH_HEAD, return_value=("feat", "abc1234")),
    ):
        result = run_fix_ci_workflow(
            PROJECT_DIR,
            "claude",
            update_issue_labels=True,
            post_issue_comments=True,
        )

    assert result == 1
    failure = mock_handle.call_args[0][0]
    comment = mock_handle.call_args[0][1]
    assert failure.category == "pr_ci_failed"
    lines = comment.splitlines()
    assert lines[0] == "## ❌ CI Fix Failed"
    assert "**Category:** Llm Timeout" in lines
    assert "**Stage:** CI pipeline analysis" in lines
    assert "**Error:** timed out" in lines


def test_mcp_unavailable_posts_comment_and_sets_label() -> None:
    with (
        patch(f"{MODULE}.get_current_branch_name", return_value=BRANCH_NAME),
        patch(
            f"{MODULE}.check_and_fix_ci",
            side_effect=McpServersUnavailableError("unavailable"),
        ),
        patch(f"{MODULE}.handle_workflow_failure") as mock_handle,
        patch(BRANCH_HEAD, return_value=("feat", "abc1234")),
    ):
        result = run_fix_ci_workflow(
            PROJECT_DIR,
            "claude",
            update_issue_labels=True,
            post_issue_comments=True,
        )

    assert result == 1
    failure = mock_handle.call_args[0][0]
    comment = mock_handle.call_args[0][1]
    assert failure.category == "pr_ci_failed"
    assert "**Category:** Mcp Unavailable" in comment.splitlines()


def test_no_current_branch_returns_one() -> None:
    with (
        patch(f"{MODULE}.get_current_branch_name", return_value=None),
        patch(f"{MODULE}.check_and_fix_ci") as mock_check,
    ):
        result = run_fix_ci_workflow(PROJECT_DIR, "claude")

    assert result == 1
    mock_check.assert_not_called()


def test_unexpected_exception_netted_by_run_guarded() -> None:
    with (
        patch(f"{MODULE}.get_current_branch_name", return_value=BRANCH_NAME),
        patch(
            f"{MODULE}.check_and_fix_ci",
            side_effect=RuntimeError("boom"),
        ),
        patch(
            "mcp_coder.workflow_utils.failure_handling.handle_workflow_failure"
        ) as mock_handle,
        patch(
            "mcp_coder.workflow_utils.failure_handling._branch_head",
            return_value=("feat", "abc1234"),
        ),
    ):
        result = run_fix_ci_workflow(
            PROJECT_DIR,
            "claude",
            update_issue_labels=True,
            post_issue_comments=True,
        )

    assert result == 1
    mock_handle.assert_called_once()
    failure = mock_handle.call_args[0][0]
    assert failure.category == "ci_fix_failed"
    comment = mock_handle.call_args[0][1]
    assert comment.splitlines()[0] == "## ❌ CI Fix Crashed"


def test_formatter_config_error_fails_before_ci_fix() -> None:
    """Unresolvable formatter → ``Formatter configuration`` failure; no CI fix."""
    with (
        patch(
            f"{MODULE}.check_formatter_config",
            return_value="No formatter declared: X",
        ) as mock_check_formatter,
        patch(f"{MODULE}.get_current_branch_name", return_value=BRANCH_NAME),
        patch(f"{MODULE}.check_and_fix_ci") as mock_check,
        patch(f"{MODULE}.handle_workflow_failure") as mock_handle,
        patch(BRANCH_HEAD, return_value=("feat", "abc1234")),
    ):
        result = run_fix_ci_workflow(
            PROJECT_DIR,
            "claude",
            update_issue_labels=True,
            post_issue_comments=True,
        )

    assert result == 1
    mock_check_formatter.assert_called_once_with(PROJECT_DIR, warn_legacy_key=True)
    mock_check.assert_not_called()
    mock_handle.assert_called_once()
    failure = mock_handle.call_args[0][0]
    comment = mock_handle.call_args[0][1]
    assert failure.stage == "Formatter configuration"
    assert failure.message == "No formatter declared: X"
    lines = comment.splitlines()
    assert lines[0] == "## ❌ CI Fix Failed"
    assert "**Category:** General" in lines
    assert "**Stage:** Formatter configuration" in lines
    assert "**Error:** No formatter declared: X" in lines


def test_format_code_false_skips_formatter(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """``format_code = false`` → the CI fix commits without calling the formatter."""
    (tmp_path / "pyproject.toml").write_text(
        "[tool.mcp-coder]\nformat_code = false\n", encoding="utf-8"
    )
    commit_changes = patch_ci_fix_externals(monkeypatch)
    wrapper = MagicMock(return_value={})
    monkeypatch.setattr(commit, "run_format_code", wrapper)

    with patch(f"{MODULE}.get_current_branch_name", return_value=BRANCH_NAME):
        result = run_fix_ci_workflow(tmp_path, "claude")

    assert result == 0
    commit_changes.assert_called_once()
    wrapper.assert_not_called()


class TestRefreshPrDescription:
    """fix-ci refreshes the PR description when check_and_fix_ci pushed."""

    @staticmethod
    def _run(
        refresh_mocks: _RefreshMocks, check_kwargs: dict[str, Any]
    ) -> tuple[int, MagicMock]:
        manager = MagicMock()
        manager.attach_mock(refresh_mocks.refresh, "refresh")
        with (
            patch(f"{MODULE}.get_current_branch_name", return_value=BRANCH_NAME),
            patch(f"{MODULE}.check_and_fix_ci", **check_kwargs),
            patch(f"{MODULE}.apply_final_label", return_value=0) as mock_update,
            patch(f"{MODULE}.handle_workflow_failure") as mock_handle,
            patch(BRANCH_HEAD, return_value=("feat", "abc1234")),
        ):
            manager.attach_mock(mock_update, "update_label")
            manager.attach_mock(mock_handle, "handle_failure")
            result = run_fix_ci_workflow(
                PROJECT_DIR,
                "claude",
                "mcp.json",
                "settings.json",
                update_issue_labels=True,
                post_issue_comments=True,
            )
        return result, manager

    @staticmethod
    def _names(manager: MagicMock) -> list[str]:
        return [c[0] for c in manager.mock_calls]

    def test_green_refreshes_before_label_update(
        self, refresh_mocks: _RefreshMocks
    ) -> None:
        refresh_mocks.sha.side_effect = ["before", "after"]

        result, manager = self._run(refresh_mocks, {"return_value": True})

        assert result == 0
        refresh_mocks.refresh.assert_called_once_with(
            PROJECT_DIR, BRANCH_NAME, "claude", "mcp.json", "settings.json"
        )
        assert self._names(manager) == ["refresh", "update_label"]
        assert manager.update_label.call_args[0][1:] == ("fixing_ci", "pr_created")

    def test_exhausted_refreshes_before_fail(
        self, refresh_mocks: _RefreshMocks
    ) -> None:
        refresh_mocks.sha.side_effect = ["before", "after"]

        result, manager = self._run(refresh_mocks, {"return_value": False})

        assert result == 1
        assert self._names(manager) == ["refresh", "handle_failure"]
        failure = manager.handle_failure.call_args[0][0]
        assert failure.category == "pr_ci_failed"
        assert failure.stage == "CI pipeline fix"

    def test_llm_timeout_refreshes_before_fail(
        self, refresh_mocks: _RefreshMocks
    ) -> None:
        refresh_mocks.sha.side_effect = ["before", "after"]

        result, manager = self._run(
            refresh_mocks, {"side_effect": LLMTimeoutError("timed out")}
        )

        assert result == 1
        assert self._names(manager) == ["refresh", "handle_failure"]
        failure = manager.handle_failure.call_args[0][0]
        assert failure.category == "pr_ci_failed"
        assert failure.stage == "CI pipeline analysis"

    @pytest.mark.parametrize(
        "check_kwargs",
        [
            {"return_value": True},
            {"return_value": False},
            {"side_effect": LLMTimeoutError("timed out")},
        ],
    )
    def test_head_unchanged_skips_refresh(
        self, refresh_mocks: _RefreshMocks, check_kwargs: dict[str, Any]
    ) -> None:
        self._run(refresh_mocks, check_kwargs)

        refresh_mocks.refresh.assert_not_called()

    def test_unexpected_exception_skips_refresh(
        self, refresh_mocks: _RefreshMocks
    ) -> None:
        refresh_mocks.sha.side_effect = ["before", "after"]
        with (
            patch(f"{MODULE}.get_current_branch_name", return_value=BRANCH_NAME),
            patch(f"{MODULE}.check_and_fix_ci", side_effect=RuntimeError("boom")),
            patch("mcp_coder.workflow_utils.failure_handling.handle_workflow_failure"),
            patch(BRANCH_HEAD, return_value=("feat", "abc1234")),
        ):
            result = run_fix_ci_workflow(
                PROJECT_DIR, "claude", update_issue_labels=True
            )

        assert result == 1
        refresh_mocks.refresh.assert_not_called()

    def test_system_exit_skips_refresh_and_propagates(
        self, refresh_mocks: _RefreshMocks
    ) -> None:
        refresh_mocks.sha.side_effect = ["before", "after"]
        with (
            patch(f"{MODULE}.get_current_branch_name", return_value=BRANCH_NAME),
            patch(f"{MODULE}.check_and_fix_ci", side_effect=SystemExit(143)),
            patch("mcp_coder.workflow_utils.failure_handling.handle_workflow_failure"),
            patch(BRANCH_HEAD, return_value=("feat", "abc1234")),
        ):
            with pytest.raises(SystemExit):
                run_fix_ci_workflow(PROJECT_DIR, "claude", update_issue_labels=True)

        refresh_mocks.refresh.assert_not_called()

"""Tests for create_pr issue labels: linkage, fallback and phase B outcome."""

import logging
from collections.abc import Iterator
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.workflows.create_pr.core import run_create_pr_workflow


@pytest.fixture(autouse=True)
def mock_post_creation() -> Iterator[MagicMock]:
    """Phase B never polls GitHub in these tests."""
    with patch(
        "mcp_coder.workflows.create_pr.core.run_post_creation",
        return_value="pr_created",
    ) as mock:
        yield mock


class TestIssueLabelLinkage:
    """Issue linkage, closing-references fallback and the final label."""

    @patch("mcp_coder.workflows.create_pr.core.update_workflow_label")
    @patch("mcp_coder.workflows.create_pr.core.validate_branch_issue_linkage")
    @patch("mcp_coder.workflows.create_pr.core.check_prerequisites")
    @patch("mcp_coder.workflows.create_pr.core.generate_pr_summary")
    @patch("mcp_coder.workflows.create_pr.core.git_push")
    @patch("mcp_coder.workflows.create_pr.core.create_pull_request")
    @patch("mcp_coder.workflows.create_pr.core.cleanup_repository")
    @patch("mcp_coder.workflows.create_pr.core.is_working_directory_clean")
    @patch("mcp_coder.workflows.create_pr.core.commit_all_changes")
    @patch("mcp_coder.workflows.create_pr.core.IssueManager")
    @patch("mcp_coder.workflows.create_pr.core.get_current_branch_name")
    @patch("mcp_coder.workflows.create_pr.core.detect_base_branch")
    @patch("mcp_coder.workflows.create_pr.core._rebase_if_needed")
    def test_workflow_caches_issue_number_before_pr_creation(
        self,
        _mock_rebase: MagicMock,
        mock_detect_base: MagicMock,
        mock_get_branch: MagicMock,
        mock_issue_manager_class: MagicMock,
        mock_commit: MagicMock,
        mock_clean: MagicMock,
        mock_cleanup: MagicMock,
        mock_create_pr: MagicMock,
        mock_push: MagicMock,
        mock_generate: MagicMock,
        mock_prereqs: MagicMock,
        mock_validate: MagicMock,
        mock_update_label: MagicMock,
    ) -> None:
        """Tests that workflow caches issue number before PR creation."""
        # Setup: Mock validate_branch_issue_linkage to return 123
        mock_validate.return_value = 123
        mock_prereqs.return_value = True
        mock_generate.return_value = ("Test Title", "Test Body")
        mock_push.return_value = {"success": True}
        mock_create_pr.return_value = (
            {"number": 42, "url": "https://github.com/test/repo/pull/42"},
            None,
        )
        mock_cleanup.return_value = True
        mock_clean.return_value = True  # Clean directory, no commit needed
        mock_get_branch.return_value = "feature-branch"
        mock_detect_base.return_value = "main"

        # Setup IssueManager mock
        mock_issue_manager = MagicMock()
        mock_issue_manager_class.return_value = mock_issue_manager
        mock_update_label.return_value = True

        # Call: run_create_pr_workflow(..., update_issue_labels=True)
        result = run_create_pr_workflow(
            Path("/test"), "claude", update_issue_labels=True
        )

        # Assert: update_workflow_label called with validated_issue_number=123
        assert result == 0
        mock_validate.assert_called_once_with(Path("/test"))
        mock_update_label.assert_called_once_with(
            mock_issue_manager,
            from_label_id="pr_creating",
            to_label_id="pr_created",
            validated_issue_number=123,
        )

    @patch("mcp_coder.workflows.create_pr.core.PullRequestManager")
    @patch("mcp_coder.workflows.create_pr.core.validate_branch_issue_linkage")
    @patch("mcp_coder.workflows.create_pr.core.check_prerequisites")
    @patch("mcp_coder.workflows.create_pr.core.generate_pr_summary")
    @patch("mcp_coder.workflows.create_pr.core.git_push")
    @patch("mcp_coder.workflows.create_pr.core.create_pull_request")
    @patch("mcp_coder.workflows.create_pr.core.cleanup_repository")
    @patch("mcp_coder.workflows.create_pr.core.is_working_directory_clean")
    @patch("mcp_coder.workflows.create_pr.core.commit_all_changes")
    @patch("mcp_coder.workflows.create_pr.core.IssueManager")
    @patch("mcp_coder.workflows.create_pr.core.get_current_branch_name")
    @patch("mcp_coder.workflows.create_pr.core.detect_base_branch")
    @patch("mcp_coder.workflows.create_pr.core._rebase_if_needed")
    def test_workflow_skips_label_update_when_not_linked(
        self,
        _mock_rebase: MagicMock,
        mock_detect_base: MagicMock,
        mock_get_branch: MagicMock,
        mock_issue_manager_class: MagicMock,
        mock_commit: MagicMock,
        mock_clean: MagicMock,
        mock_cleanup: MagicMock,
        mock_create_pr: MagicMock,
        mock_push: MagicMock,
        mock_generate: MagicMock,
        mock_prereqs: MagicMock,
        mock_validate: MagicMock,
        mock_pr_manager_class: MagicMock,
    ) -> None:
        """Tests that workflow skips label update when branch not linked."""
        # Setup: Mock validate_branch_issue_linkage to return None
        mock_validate.return_value = None
        # Setup: Mock PullRequestManager fallback to return no closing issues
        mock_pr_mgr = MagicMock()
        mock_pr_manager_class.return_value = mock_pr_mgr
        mock_pr_mgr.get_closing_issue_numbers.return_value = []
        mock_prereqs.return_value = True
        mock_generate.return_value = ("Test Title", "Test Body")
        mock_push.return_value = {"success": True}
        mock_create_pr.return_value = (
            {"number": 42, "url": "https://github.com/test/repo/pull/42"},
            None,
        )
        mock_cleanup.return_value = True
        mock_clean.return_value = True  # Clean directory, no commit needed
        mock_get_branch.return_value = "feature-branch"
        mock_detect_base.return_value = "main"

        # Setup IssueManager mock
        mock_issue_manager = MagicMock()
        mock_issue_manager_class.return_value = mock_issue_manager

        # Call: run_create_pr_workflow(..., update_issue_labels=True)
        result = run_create_pr_workflow(
            Path("/test"), "claude", update_issue_labels=True
        )

        # Assert: update_workflow_label NOT called
        assert result == 0
        mock_validate.assert_called_once_with(Path("/test"))
        mock_issue_manager.update_workflow_label.assert_not_called()

    @patch("mcp_coder.workflows.create_pr.core.update_workflow_label")
    @patch("mcp_coder.workflows.create_pr.core.PullRequestManager")
    @patch("mcp_coder.workflows.create_pr.core.validate_branch_issue_linkage")
    @patch("mcp_coder.workflows.create_pr.core.check_prerequisites")
    @patch("mcp_coder.workflows.create_pr.core.generate_pr_summary")
    @patch("mcp_coder.workflows.create_pr.core.git_push")
    @patch("mcp_coder.workflows.create_pr.core.create_pull_request")
    @patch("mcp_coder.workflows.create_pr.core.cleanup_repository")
    @patch("mcp_coder.workflows.create_pr.core.is_working_directory_clean")
    @patch("mcp_coder.workflows.create_pr.core.IssueManager")
    @patch("mcp_coder.workflows.create_pr.core.get_current_branch_name")
    @patch("mcp_coder.workflows.create_pr.core.detect_base_branch")
    @patch("mcp_coder.workflows.create_pr.core._rebase_if_needed")
    def test_workflow_fallback_finds_issue_via_closing_references(
        self,
        _mock_rebase: MagicMock,
        mock_detect_base: MagicMock,
        mock_get_branch: MagicMock,
        mock_issue_manager_class: MagicMock,
        mock_clean: MagicMock,
        mock_cleanup: MagicMock,
        mock_create_pr: MagicMock,
        mock_push: MagicMock,
        mock_generate: MagicMock,
        mock_prereqs: MagicMock,
        mock_validate: MagicMock,
        mock_pr_manager_class: MagicMock,
        mock_update_label: MagicMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Tests fallback queries closingIssuesReferences and finds issue."""
        mock_validate.return_value = None
        mock_prereqs.return_value = True
        mock_generate.return_value = ("Test Title", "Test Body")
        mock_push.return_value = {"success": True}
        mock_create_pr.return_value = (
            {"number": 42, "url": "https://github.com/test/repo/pull/42"},
            None,
        )
        mock_cleanup.return_value = True
        mock_clean.return_value = True
        mock_get_branch.return_value = "feature-branch"
        mock_detect_base.return_value = "main"

        mock_pr_mgr = MagicMock()
        mock_pr_manager_class.return_value = mock_pr_mgr
        mock_pr_mgr.get_closing_issue_numbers.return_value = [92]

        mock_issue_manager = MagicMock()
        mock_issue_manager_class.return_value = mock_issue_manager
        mock_update_label.return_value = True

        with caplog.at_level(logging.DEBUG):
            result = run_create_pr_workflow(
                Path("/test"), "claude", update_issue_labels=True
            )

        assert result == 0
        mock_pr_mgr.get_closing_issue_numbers.assert_called_once_with(42)
        mock_update_label.assert_called_once_with(
            mock_issue_manager,
            from_label_id="pr_creating",
            to_label_id="pr_created",
            validated_issue_number=92,
        )
        assert "completed successfully!" in caplog.text

    @patch("mcp_coder.workflows.create_pr.core.update_workflow_label")
    @patch("mcp_coder.workflows.create_pr.core.PullRequestManager")
    @patch("mcp_coder.workflows.create_pr.core.validate_branch_issue_linkage")
    @patch("mcp_coder.workflows.create_pr.core.check_prerequisites")
    @patch("mcp_coder.workflows.create_pr.core.generate_pr_summary")
    @patch("mcp_coder.workflows.create_pr.core.git_push")
    @patch("mcp_coder.workflows.create_pr.core.create_pull_request")
    @patch("mcp_coder.workflows.create_pr.core.cleanup_repository")
    @patch("mcp_coder.workflows.create_pr.core.is_working_directory_clean")
    @patch("mcp_coder.workflows.create_pr.core.IssueManager")
    @patch("mcp_coder.workflows.create_pr.core.get_current_branch_name")
    @patch("mcp_coder.workflows.create_pr.core.detect_base_branch")
    @patch("mcp_coder.workflows.create_pr.core._rebase_if_needed")
    def test_workflow_fallback_multiple_closing_issues_uses_first(
        self,
        _mock_rebase: MagicMock,
        mock_detect_base: MagicMock,
        mock_get_branch: MagicMock,
        mock_issue_manager_class: MagicMock,
        mock_clean: MagicMock,
        mock_cleanup: MagicMock,
        mock_create_pr: MagicMock,
        mock_push: MagicMock,
        mock_generate: MagicMock,
        mock_prereqs: MagicMock,
        mock_validate: MagicMock,
        mock_pr_manager_class: MagicMock,
        mock_update_label: MagicMock,
    ) -> None:
        """Tests fallback with multiple closing issues uses first."""
        mock_validate.return_value = None
        mock_prereqs.return_value = True
        mock_generate.return_value = ("Test Title", "Test Body")
        mock_push.return_value = {"success": True}
        mock_create_pr.return_value = (
            {"number": 42, "url": "https://github.com/test/repo/pull/42"},
            None,
        )
        mock_cleanup.return_value = True
        mock_clean.return_value = True
        mock_get_branch.return_value = "feature-branch"
        mock_detect_base.return_value = "main"

        mock_pr_mgr = MagicMock()
        mock_pr_manager_class.return_value = mock_pr_mgr
        mock_pr_mgr.get_closing_issue_numbers.return_value = [92, 55]

        mock_issue_manager = MagicMock()
        mock_issue_manager_class.return_value = mock_issue_manager
        mock_update_label.return_value = True

        result = run_create_pr_workflow(
            Path("/test"), "claude", update_issue_labels=True
        )

        assert result == 0
        mock_update_label.assert_called_once_with(
            mock_issue_manager,
            from_label_id="pr_creating",
            to_label_id="pr_created",
            validated_issue_number=92,
        )

    @patch("mcp_coder.workflows.create_pr.core.PullRequestManager")
    @patch("mcp_coder.workflows.create_pr.core.validate_branch_issue_linkage")
    @patch("mcp_coder.workflows.create_pr.core.check_prerequisites")
    @patch("mcp_coder.workflows.create_pr.core.generate_pr_summary")
    @patch("mcp_coder.workflows.create_pr.core.git_push")
    @patch("mcp_coder.workflows.create_pr.core.create_pull_request")
    @patch("mcp_coder.workflows.create_pr.core.cleanup_repository")
    @patch("mcp_coder.workflows.create_pr.core.is_working_directory_clean")
    @patch("mcp_coder.workflows.create_pr.core.get_current_branch_name")
    @patch("mcp_coder.workflows.create_pr.core.detect_base_branch")
    @patch("mcp_coder.workflows.create_pr.core._rebase_if_needed")
    def test_workflow_fallback_no_closing_issues_skips_labels(
        self,
        _mock_rebase: MagicMock,
        mock_detect_base: MagicMock,
        mock_get_branch: MagicMock,
        mock_clean: MagicMock,
        mock_cleanup: MagicMock,
        mock_create_pr: MagicMock,
        mock_push: MagicMock,
        mock_generate: MagicMock,
        mock_prereqs: MagicMock,
        mock_validate: MagicMock,
        mock_pr_manager_class: MagicMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Tests fallback with no closing issues skips label update."""
        mock_validate.return_value = None
        mock_prereqs.return_value = True
        mock_generate.return_value = ("Test Title", "Test Body")
        mock_push.return_value = {"success": True}
        mock_create_pr.return_value = (
            {"number": 42, "url": "https://github.com/test/repo/pull/42"},
            None,
        )
        mock_cleanup.return_value = True
        mock_clean.return_value = True
        mock_get_branch.return_value = "feature-branch"
        mock_detect_base.return_value = "main"

        mock_pr_mgr = MagicMock()
        mock_pr_manager_class.return_value = mock_pr_mgr
        mock_pr_mgr.get_closing_issue_numbers.return_value = []

        with caplog.at_level(logging.DEBUG):
            result = run_create_pr_workflow(
                Path("/test"), "claude", update_issue_labels=True
            )

        assert result == 0
        assert "completed with warnings" in caplog.text

    @patch("mcp_coder.workflows.create_pr.core.PullRequestManager")
    @patch("mcp_coder.workflows.create_pr.core.validate_branch_issue_linkage")
    @patch("mcp_coder.workflows.create_pr.core.check_prerequisites")
    @patch("mcp_coder.workflows.create_pr.core.generate_pr_summary")
    @patch("mcp_coder.workflows.create_pr.core.git_push")
    @patch("mcp_coder.workflows.create_pr.core.create_pull_request")
    @patch("mcp_coder.workflows.create_pr.core.cleanup_repository")
    @patch("mcp_coder.workflows.create_pr.core.is_working_directory_clean")
    @patch("mcp_coder.workflows.create_pr.core.get_current_branch_name")
    @patch("mcp_coder.workflows.create_pr.core.detect_base_branch")
    @patch("mcp_coder.workflows.create_pr.core._rebase_if_needed")
    def test_workflow_completed_with_warnings_when_no_issue_found(
        self,
        _mock_rebase: MagicMock,
        mock_detect_base: MagicMock,
        mock_get_branch: MagicMock,
        mock_clean: MagicMock,
        mock_cleanup: MagicMock,
        mock_create_pr: MagicMock,
        mock_push: MagicMock,
        mock_generate: MagicMock,
        mock_prereqs: MagicMock,
        mock_validate: MagicMock,
        mock_pr_manager_class: MagicMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Tests completion message is 'with warnings' when no issue found."""
        mock_validate.return_value = None
        mock_prereqs.return_value = True
        mock_generate.return_value = ("Test Title", "Test Body")
        mock_push.return_value = {"success": True}
        mock_create_pr.return_value = (
            {"number": 42, "url": "https://github.com/test/repo/pull/42"},
            None,
        )
        mock_cleanup.return_value = True
        mock_clean.return_value = True
        mock_get_branch.return_value = "feature-branch"
        mock_detect_base.return_value = "main"

        mock_pr_mgr = MagicMock()
        mock_pr_manager_class.return_value = mock_pr_mgr
        mock_pr_mgr.get_closing_issue_numbers.return_value = []

        with caplog.at_level(logging.DEBUG):
            result = run_create_pr_workflow(
                Path("/test"), "claude", update_issue_labels=True
            )

        assert result == 0
        assert "completed with warnings" in caplog.text
        assert "completed successfully!" not in caplog.text

    @patch("mcp_coder.workflows.create_pr.core.PullRequestManager")
    @patch("mcp_coder.workflows.create_pr.core.validate_branch_issue_linkage")
    @patch("mcp_coder.workflows.create_pr.core.check_prerequisites")
    @patch("mcp_coder.workflows.create_pr.core.generate_pr_summary")
    @patch("mcp_coder.workflows.create_pr.core.git_push")
    @patch("mcp_coder.workflows.create_pr.core.create_pull_request")
    @patch("mcp_coder.workflows.create_pr.core.cleanup_repository")
    @patch("mcp_coder.workflows.create_pr.core.is_working_directory_clean")
    @patch("mcp_coder.workflows.create_pr.core.IssueManager")
    @patch("mcp_coder.workflows.create_pr.core.get_current_branch_name")
    @patch("mcp_coder.workflows.create_pr.core.detect_base_branch")
    @patch("mcp_coder.workflows.create_pr.core._rebase_if_needed")
    def test_workflow_skips_fallback_when_issue_already_found(
        self,
        _mock_rebase: MagicMock,
        mock_detect_base: MagicMock,
        mock_get_branch: MagicMock,
        mock_issue_manager_class: MagicMock,
        mock_clean: MagicMock,
        mock_cleanup: MagicMock,
        mock_create_pr: MagicMock,
        mock_push: MagicMock,
        mock_generate: MagicMock,
        mock_prereqs: MagicMock,
        mock_validate: MagicMock,
        mock_pr_manager_class: MagicMock,
    ) -> None:
        """Tests that fallback is skipped when issue already found from branch."""
        mock_validate.return_value = 123
        mock_issue_manager = MagicMock()
        mock_issue_manager_class.return_value = mock_issue_manager
        mock_issue_manager.update_workflow_label.return_value = True
        mock_prereqs.return_value = True
        mock_generate.return_value = ("Test Title", "Test Body")
        mock_push.return_value = {"success": True}
        mock_create_pr.return_value = (
            {"number": 42, "url": "https://github.com/test/repo/pull/42"},
            None,
        )
        mock_cleanup.return_value = True
        mock_clean.return_value = True
        mock_get_branch.return_value = "123-feature-branch"
        mock_detect_base.return_value = "main"

        result = run_create_pr_workflow(
            Path("/test"), "claude", update_issue_labels=True
        )

        assert result == 0
        mock_pr_manager_class.return_value.get_closing_issue_numbers.assert_not_called()


_CORE = "mcp_coder.workflows.create_pr.core"


@pytest.fixture
def phase_a_ok() -> Iterator[dict[str, MagicMock]]:
    """Patch phase A so it opens PR #42 on 'feature-branch' without I/O."""
    targets = {
        "validate": ("validate_branch_issue_linkage", 123),
        "prereqs": ("check_prerequisites", True),
        "rebase": ("_rebase_if_needed", None),
        "generate": ("generate_pr_summary", ("Title", "Body")),
        "cleanup": ("cleanup_repository", True),
        "clean": ("is_working_directory_clean", True),
        "push": ("git_push", {"success": True}),
        "create_pr": (
            "create_pull_request",
            ({"number": 42, "url": "https://github.com/test/repo/pull/42"}, None),
        ),
        "branch": ("get_current_branch_name", "feature-branch"),
        "base": ("detect_base_branch", "main"),
        "assignee": ("_add_pr_assignee_best_effort", None),
        "pr_manager": ("PullRequestManager", None),
        "issue_manager": ("IssueManager", None),
        "update_label": ("update_workflow_label", True),
    }
    patchers = {
        key: patch(f"{_CORE}.{name}", return_value=value)
        for key, (name, value) in targets.items()
    }
    mocks = {key: p.start() for key, p in patchers.items()}
    try:
        yield mocks
    finally:
        for p in patchers.values():
            p.stop()


class TestPhaseB:
    """Phase B: post-creation checks and the final label."""

    @pytest.mark.parametrize("label", ["pr_created", "pr_merge_conflict", "failing_ci"])
    def test_final_label_from_post_creation(
        self,
        label: str,
        phase_a_ok: dict[str, MagicMock],
        mock_post_creation: MagicMock,
    ) -> None:
        """The outcome of run_post_creation becomes the final label; exit 0."""
        mock_post_creation.return_value = label

        result = run_create_pr_workflow(
            Path("/test"), "claude", update_issue_labels=True
        )

        assert result == 0
        mock_post_creation.assert_called_once_with(Path("/test"), "feature-branch")
        phase_a_ok["update_label"].assert_called_once_with(
            phase_a_ok["issue_manager"].return_value,
            from_label_id="pr_creating",
            to_label_id=label,
            validated_issue_number=123,
        )

    def test_labels_off_still_runs_phase_b(
        self,
        phase_a_ok: dict[str, MagicMock],
        mock_post_creation: MagicMock,
    ) -> None:
        """Phase B runs with update_issue_labels=False, but sets no label."""
        mock_post_creation.return_value = "failing_ci"

        result = run_create_pr_workflow(Path("/test"), "claude")

        assert result == 0
        mock_post_creation.assert_called_once()
        phase_a_ok["update_label"].assert_not_called()

    def test_label_update_failure_is_non_blocking(
        self,
        phase_a_ok: dict[str, MagicMock],
        mock_post_creation: MagicMock,
    ) -> None:
        """A failing label update is logged and the workflow still exits 0."""
        phase_a_ok["update_label"].side_effect = RuntimeError("API down")

        result = run_create_pr_workflow(
            Path("/test"), "claude", update_issue_labels=True
        )

        assert result == 0
        mock_post_creation.assert_called_once()

    @patch(f"{_CORE}._handle_create_pr_failure")
    def test_phase_a_failure_skips_phase_b(
        self,
        _mock_handle_failure: MagicMock,
        phase_a_ok: dict[str, MagicMock],
        mock_post_creation: MagicMock,
    ) -> None:
        """A handled phase A failure ends the workflow with exit 1."""
        phase_a_ok["prereqs"].return_value = False

        result = run_create_pr_workflow(
            Path("/test"), "claude", update_issue_labels=True
        )

        assert result == 1
        mock_post_creation.assert_not_called()
        phase_a_ok["update_label"].assert_not_called()

    @patch(
        "mcp_coder.workflow_utils.failure_handling._branch_head",
        return_value=("feat", "abc1234"),
    )
    @patch("mcp_coder.workflow_utils.failure_handling.handle_workflow_failure")
    def test_phase_a_crash_uses_pr_creating_failed(
        self,
        mock_workflow_failure: MagicMock,
        _mock_branch_head: MagicMock,
        phase_a_ok: dict[str, MagicMock],
        mock_post_creation: MagicMock,
    ) -> None:
        """A phase A escape is netted as pr_creating_failed; phase B not run."""
        phase_a_ok["cleanup"].side_effect = RuntimeError("boom")

        result = run_create_pr_workflow(
            Path("/test"), "claude", update_issue_labels=True
        )

        assert result == 1
        mock_post_creation.assert_not_called()
        mock_workflow_failure.assert_called_once()
        assert mock_workflow_failure.call_args.args[0].category == "pr_creating_failed"

    @patch(
        "mcp_coder.workflow_utils.failure_handling._branch_head",
        return_value=("feat", "abc1234"),
    )
    @patch("mcp_coder.workflow_utils.failure_handling.handle_workflow_failure")
    def test_phase_b_crash_uses_pr_created(
        self,
        mock_workflow_failure: MagicMock,
        _mock_branch_head: MagicMock,
        phase_a_ok: dict[str, MagicMock],
        mock_post_creation: MagicMock,
    ) -> None:
        """A phase B escape is netted as pr_created with a crash comment."""
        mock_post_creation.side_effect = RuntimeError("poll exploded")

        result = run_create_pr_workflow(
            Path("/test"), "claude", update_issue_labels=True, post_issue_comments=True
        )

        assert result == 1
        phase_a_ok["update_label"].assert_not_called()
        mock_workflow_failure.assert_called_once()
        failure = mock_workflow_failure.call_args.args[0]
        assert failure.category == "pr_created"
        comment = mock_workflow_failure.call_args.args[1]
        assert comment.splitlines()[0] == "## ❌ PR Creation Crashed"
        assert mock_workflow_failure.call_args.kwargs["from_label_id"] == "pr_creating"
        assert mock_workflow_failure.call_args.kwargs["issue_number"] == 123

    @patch(
        "mcp_coder.workflow_utils.failure_handling._branch_head",
        return_value=("feat", "abc1234"),
    )
    @patch("mcp_coder.workflow_utils.failure_handling.handle_workflow_failure")
    def test_issue_from_closing_refs_used_by_phase_b(
        self,
        mock_workflow_failure: MagicMock,
        _mock_branch_head: MagicMock,
        phase_a_ok: dict[str, MagicMock],
        mock_post_creation: MagicMock,
    ) -> None:
        """An issue found by the fallback in phase A reaches phase B."""
        phase_a_ok["validate"].return_value = None
        with patch(f"{_CORE}._resolve_issue_from_pr", return_value=9):
            result = run_create_pr_workflow(
                Path("/test"), "claude", update_issue_labels=True
            )
            assert result == 0
            assert (
                phase_a_ok["update_label"].call_args.kwargs["validated_issue_number"]
                == 9
            )

            mock_post_creation.side_effect = RuntimeError("poll exploded")
            result = run_create_pr_workflow(
                Path("/test"), "claude", update_issue_labels=True
            )

        assert result == 1
        assert mock_workflow_failure.call_args.args[0].category == "pr_created"
        assert mock_workflow_failure.call_args.kwargs["issue_number"] == 9

    def test_no_branch_skips_checks_and_sets_pr_created(
        self,
        phase_a_ok: dict[str, MagicMock],
        mock_post_creation: MagicMock,
    ) -> None:
        """Without a current branch, phase B skips the checks and sets pr_created."""
        phase_a_ok["branch"].return_value = None

        result = run_create_pr_workflow(
            Path("/test"), "claude", update_issue_labels=True
        )

        assert result == 0
        mock_post_creation.assert_not_called()
        assert phase_a_ok["update_label"].call_args.kwargs["to_label_id"] == (
            "pr_created"
        )

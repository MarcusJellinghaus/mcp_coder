import argparse
import logging
from collections.abc import Iterator
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from mcp_coder.cli.commands.commit import _push_after_commit, execute_commit_auto

MODULE = "mcp_coder.cli.commands.commit"


@pytest.fixture(autouse=True)
def _feature_branch() -> Iterator[None]:
    """Run every test on a feature branch unless the test patches otherwise."""
    with (
        patch(f"{MODULE}.get_current_branch_name", return_value="feature/x"),
        patch(f"{MODULE}.get_default_branch_name", return_value="main"),
    ):
        yield


class TestPushAfterCommit:
    """Tests for _push_after_commit helper function."""

    @patch(f"{MODULE}.get_current_branch_name", return_value="feature/foo")
    @patch(f"{MODULE}.get_default_branch_name", return_value="main")
    @patch(f"{MODULE}.has_remote_tracking_branch", return_value=True)
    @patch(f"{MODULE}.git_push", return_value={"success": True})
    def test_push_success_with_tracking_branch(
        self,
        mock_git_push: Mock,
        mock_has_tracking: Mock,
        mock_default: Mock,
        mock_current: Mock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Push succeeds when tracking branch exists and git_push succeeds."""
        with caplog.at_level(logging.INFO):
            result = _push_after_commit(Path("/test/repo"))

        assert result == 0
        assert "Pushed to origin/" in caplog.text
        mock_git_push.assert_called_once_with(Path("/test/repo"))

    @patch(f"{MODULE}.get_current_branch_name", return_value="feature/bar")
    @patch(f"{MODULE}.get_default_branch_name", return_value="main")
    @patch(f"{MODULE}.has_remote_tracking_branch", return_value=False)
    @patch(f"{MODULE}.push_branch", return_value=True)
    def test_push_success_new_branch(
        self,
        mock_push_branch: Mock,
        mock_has_tracking: Mock,
        mock_default: Mock,
        mock_current: Mock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Push succeeds for new branch without tracking, sets upstream."""
        with caplog.at_level(logging.INFO):
            result = _push_after_commit(Path("/test/repo"))

        assert result == 0
        mock_push_branch.assert_called_once_with(
            "feature/bar", Path("/test/repo"), set_upstream=True
        )
        assert "Pushed to origin/" in caplog.text
        mock_current.assert_called_once()

    @patch(f"{MODULE}.get_current_branch_name", return_value="main")
    @patch(f"{MODULE}.get_default_branch_name", return_value="main")
    def test_push_refused_on_default_branch(
        self,
        mock_default: Mock,
        mock_current: Mock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Push is refused when on the default branch."""
        with caplog.at_level(logging.ERROR):
            result = _push_after_commit(Path("/test/repo"))

        assert result == 2
        assert "protected branch" in caplog.text

    @patch(f"{MODULE}.get_current_branch_name", return_value="main")
    @patch(f"{MODULE}.get_default_branch_name", return_value=None)
    def test_push_refused_fallback_main(
        self,
        mock_default: Mock,
        mock_current: Mock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Push is refused on 'main' when default branch detection returns None."""
        with caplog.at_level(logging.ERROR):
            result = _push_after_commit(Path("/test/repo"))

        assert result == 2

    @patch(f"{MODULE}.get_current_branch_name", return_value="master")
    @patch(f"{MODULE}.get_default_branch_name", return_value=None)
    def test_push_refused_fallback_master(
        self,
        mock_default: Mock,
        mock_current: Mock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Push is refused on 'master' when default branch detection returns None."""
        with caplog.at_level(logging.ERROR):
            result = _push_after_commit(Path("/test/repo"))

        assert result == 2

    @patch(f"{MODULE}.get_current_branch_name", return_value="master")
    @patch(f"{MODULE}.get_default_branch_name", return_value="main")
    def test_push_refused_on_master_when_default_main(
        self,
        mock_default: Mock,
        mock_current: Mock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Push is refused on 'master' even when the detected default is 'main'."""
        with caplog.at_level(logging.ERROR):
            result = _push_after_commit(Path("/test/repo"))

        assert result == 2
        assert "protected branch" in caplog.text

    @patch(f"{MODULE}.get_current_branch_name", return_value="feature/foo")
    @patch(f"{MODULE}.get_default_branch_name", return_value="main")
    @patch(f"{MODULE}.has_remote_tracking_branch", return_value=True)
    @patch(
        f"{MODULE}.git_push",
        return_value={"success": False, "error": "rejected"},
    )
    def test_push_failure_with_tracking(
        self,
        mock_git_push: Mock,
        mock_has_tracking: Mock,
        mock_default: Mock,
        mock_current: Mock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Push fails when git_push returns failure."""
        with caplog.at_level(logging.ERROR):
            result = _push_after_commit(Path("/test/repo"))

        assert result == 2
        assert "Failed to push" in caplog.text

    @patch(f"{MODULE}.get_current_branch_name", return_value="feature/bar")
    @patch(f"{MODULE}.get_default_branch_name", return_value="main")
    @patch(f"{MODULE}.has_remote_tracking_branch", return_value=False)
    @patch(f"{MODULE}.push_branch", return_value=False)
    def test_push_failure_new_branch(
        self,
        mock_push_branch: Mock,
        mock_has_tracking: Mock,
        mock_default: Mock,
        mock_current: Mock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Push fails when push_branch returns False."""
        with caplog.at_level(logging.ERROR):
            result = _push_after_commit(Path("/test/repo"))

        assert result == 2
        assert "Failed to push" in caplog.text

    @patch(f"{MODULE}.get_current_branch_name", return_value=None)
    def test_push_refused_on_detached_head(
        self,
        mock_current: Mock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Push is refused when not on a branch (detached HEAD)."""
        with caplog.at_level(logging.ERROR):
            result = _push_after_commit(Path("/test/repo"))

        assert result == 2
        assert "not on a branch" in caplog.text


class TestCommitAutoPush:
    """Tests for --push integration in execute_commit_auto."""

    @patch(f"{MODULE}.validate_git_repository", return_value=(True, None))
    @patch(f"{MODULE}.resolve_llm_method", return_value=("claude", "cli"))
    @patch(f"{MODULE}.parse_llm_method_from_args", return_value="claude")
    @patch(
        f"{MODULE}.generate_commit_message_with_llm",
        return_value=(True, "feat: test", None),
    )
    @patch(
        f"{MODULE}.commit_staged_files",
        return_value={"success": True, "commit_hash": "abc123", "error": None},
    )
    @patch(f"{MODULE}._push_after_commit", return_value=0)
    def test_commit_auto_push_called_on_success(
        self,
        mock_push: Mock,
        mock_commit: Mock,
        mock_generate: Mock,
        mock_parse: Mock,
        mock_resolve: Mock,
        mock_validate: Mock,
    ) -> None:
        """Push is called after successful commit when --push is set."""
        # "/repo" need not exist: resolve_claude_cwd does not validate it
        args = argparse.Namespace(
            preview=False, llm_method="claude", project_dir="/repo", push=True
        )
        result = execute_commit_auto(args)

        assert result == 0
        # resolve_claude_cwd resolves project_dir before the push
        mock_push.assert_called_once_with(Path("/repo").resolve())

    @patch(f"{MODULE}.validate_git_repository", return_value=(True, None))
    @patch(f"{MODULE}.resolve_llm_method", return_value=("claude", "cli"))
    @patch(f"{MODULE}.parse_llm_method_from_args", return_value="claude")
    @patch(
        f"{MODULE}.generate_commit_message_with_llm",
        return_value=(True, "feat: test", None),
    )
    @patch(
        f"{MODULE}.commit_staged_files",
        return_value={"success": True, "commit_hash": "abc123", "error": None},
    )
    @patch(f"{MODULE}._push_after_commit", return_value=2)
    def test_commit_auto_push_failure_returns_2(
        self,
        mock_push: Mock,
        mock_commit: Mock,
        mock_generate: Mock,
        mock_parse: Mock,
        mock_resolve: Mock,
        mock_validate: Mock,
    ) -> None:
        """Push failure propagates its exit code."""
        # "/repo" need not exist: resolve_claude_cwd does not validate it
        args = argparse.Namespace(
            preview=False, llm_method="claude", project_dir="/repo", push=True
        )
        result = execute_commit_auto(args)

        assert result == 2

    @patch(f"{MODULE}.validate_git_repository", return_value=(True, None))
    @patch(f"{MODULE}.resolve_llm_method", return_value=("claude", "cli"))
    @patch(f"{MODULE}.parse_llm_method_from_args", return_value="claude")
    @patch(
        f"{MODULE}.generate_commit_message_with_llm",
        return_value=(True, "feat: test", None),
    )
    @patch(
        f"{MODULE}.commit_staged_files",
        return_value={"success": True, "commit_hash": "abc123", "error": None},
    )
    @patch(f"{MODULE}._push_after_commit")
    def test_commit_auto_no_push_flag(
        self,
        mock_push: Mock,
        mock_commit: Mock,
        mock_generate: Mock,
        mock_parse: Mock,
        mock_resolve: Mock,
        mock_validate: Mock,
    ) -> None:
        """Push is NOT called when --push is False."""
        # "/repo" need not exist: resolve_claude_cwd does not validate it
        args = argparse.Namespace(
            preview=False, llm_method="claude", project_dir="/repo", push=False
        )
        result = execute_commit_auto(args)

        assert result == 0
        mock_push.assert_not_called()

    @patch(f"{MODULE}.validate_git_repository", return_value=(True, None))
    @patch(f"{MODULE}.resolve_llm_method", return_value=("claude", "cli"))
    @patch(f"{MODULE}.parse_llm_method_from_args", return_value="claude")
    @patch(
        f"{MODULE}.generate_commit_message_with_llm",
        return_value=(False, "", "LLM error"),
    )
    @patch(f"{MODULE}._push_after_commit")
    def test_commit_auto_push_not_called_on_commit_failure(
        self,
        mock_push: Mock,
        mock_generate: Mock,
        mock_parse: Mock,
        mock_resolve: Mock,
        mock_validate: Mock,
    ) -> None:
        """Push is NOT called when commit generation fails."""
        # "/repo" need not exist: resolve_claude_cwd does not validate it
        args = argparse.Namespace(
            preview=False, llm_method="claude", project_dir="/repo", push=True
        )
        result = execute_commit_auto(args)

        assert result == 2
        mock_push.assert_not_called()


class TestCommitBranchGuard:
    """Tests for the pre-commit branch refusal in execute_commit_auto."""

    @pytest.mark.parametrize("push", [True, False])
    @pytest.mark.parametrize(
        ("current", "default"),
        [
            ("main", "main"),
            ("master", "main"),
            ("develop", "develop"),
            (None, "main"),
        ],
    )
    def test_commit_refused_before_llm_and_preview(
        self,
        current: str | None,
        default: str,
        push: bool,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Commit is refused (exit 1) before the LLM call, preview and push."""
        args = argparse.Namespace(
            preview=True, llm_method="claude", project_dir="/repo", push=push
        )
        with (
            patch(f"{MODULE}.get_current_branch_name", return_value=current),
            patch(
                f"{MODULE}.get_default_branch_name", return_value=default
            ) as mock_default,
            patch(f"{MODULE}.validate_git_repository", return_value=(True, None)),
            patch(f"{MODULE}.generate_commit_message_with_llm") as mock_generate,
            patch(f"{MODULE}.commit_staged_files") as mock_commit,
            patch(f"{MODULE}._push_after_commit") as mock_push,
            patch("builtins.input") as mock_input,
            caplog.at_level(logging.ERROR),
        ):
            result = execute_commit_auto(args)

        assert result == 1
        mock_generate.assert_not_called()
        mock_commit.assert_not_called()
        mock_input.assert_not_called()
        mock_push.assert_not_called()
        if current is not None:
            assert "protected branch" in caplog.text
        else:
            assert "cannot determine current branch" in caplog.text
            mock_default.assert_not_called()

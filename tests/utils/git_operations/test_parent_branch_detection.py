"""Tests for corrected merge-base parent branch detection (#803).

These tests validate the CORRECTED algorithm that measures distance as
merge_base → current_HEAD (not merge_base → candidate_HEAD). Tests are
written TDD-style and will fail against the current buggy code.
"""

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

from mcp_coder.utils.git_operations.parent_branch_detection import (
    MERGE_BASE_DISTANCE_THRESHOLD,
    detect_parent_branch_via_merge_base,
)

MODULE = "mcp_coder.utils.git_operations.parent_branch_detection"


def _make_branch(name: str, hexsha: str = "") -> MagicMock:
    """Create a mock branch with name and commit."""
    branch = MagicMock()
    branch.name = name
    branch.commit = MagicMock()
    branch.commit.hexsha = hexsha or f"{name}_sha"
    return branch


def _make_merge_base(hexsha: str) -> MagicMock:
    """Create a mock merge-base commit."""
    mb = MagicMock()
    mb.hexsha = hexsha
    return mb


def _make_heads(
    branches: dict[str, MagicMock],
) -> MagicMock:
    """Create a mock heads object that supports iteration and getitem."""
    heads = MagicMock()
    branch_list = list(branches.values())
    heads.__iter__ = MagicMock(return_value=iter(branch_list))
    heads.__getitem__ = MagicMock(side_effect=lambda key: branches[key])
    return heads


def _setup_repo(
    branches: dict[str, MagicMock],
    mock_ctx: MagicMock,
    *,
    has_remotes: bool = False,
) -> MagicMock:
    """Create and wire up a mock repo with branches."""
    repo = MagicMock()
    repo.heads = _make_heads(branches)
    if not has_remotes:
        repo.remotes = []
    mock_ctx.return_value.__enter__ = MagicMock(return_value=repo)
    mock_ctx.return_value.__exit__ = MagicMock(return_value=False)
    return repo


@patch(f"{MODULE}.get_default_branch_name", create=True, return_value="main")
@patch(f"{MODULE}._safe_repo_context")
@patch(f"{MODULE}.is_git_repository", return_value=True)
class TestMergeBaseDirectionFix:
    """Core bug fix: distance must be merge_base → current_HEAD."""

    def test_selects_main_over_dormant_feature_branch(
        self,
        _mock_is_git: MagicMock,
        mock_ctx: MagicMock,
        _mock_default: MagicMock,
    ) -> None:
        """Main has many commits since divergence but merge-base is recent.

        Scenario from issue #803:
        - current branch created from main
        - dormant feature branch diverged long ago, few commits on candidate
        - With OLD (buggy) algo: dormant wins (small candidate-HEAD distance)
        - With NEW (fixed) algo: main wins (small current-HEAD distance)
        """
        current = _make_branch("my-feature", "current_sha")
        main = _make_branch("main", "main_sha")
        dormant = _make_branch("old-feature", "dormant_sha")

        mb_main = _make_merge_base("mb_main_sha")
        mb_dormant = _make_merge_base("mb_dormant_sha")

        repo = _setup_repo(
            {"my-feature": current, "main": main, "old-feature": dormant},
            mock_ctx,
        )

        def merge_base_side_effect(*args: Any) -> list[MagicMock]:
            candidate_commit = args[1]
            if candidate_commit is main.commit:
                return [mb_main]
            if candidate_commit is dormant.commit:
                return [mb_dormant]
            return []

        repo.merge_base.side_effect = merge_base_side_effect

        def iter_commits_side_effect(rev_range: str) -> list[MagicMock]:
            # NEW direction: merge_base → current_HEAD
            if rev_range == f"{mb_main.hexsha}..{current.commit.hexsha}":
                return [MagicMock()] * 3  # 3 commits: close
            if rev_range == f"{mb_dormant.hexsha}..{current.commit.hexsha}":
                return [MagicMock()] * 15  # 15 commits: far
            # OLD direction (should NOT be used by fixed code):
            if rev_range == f"{mb_main.hexsha}..{main.commit.hexsha}":
                return [MagicMock()] * 10  # many commits on main
            if rev_range == f"{mb_dormant.hexsha}..{dormant.commit.hexsha}":
                return [MagicMock()] * 1  # few commits on dormant
            return []

        repo.iter_commits.side_effect = iter_commits_side_effect

        result = detect_parent_branch_via_merge_base(Path("/repo"), "my-feature")

        assert result == "main"

    def test_selects_feature_branch_for_stacked_pr(
        self,
        _mock_is_git: MagicMock,
        mock_ctx: MagicMock,
        _mock_default: MagicMock,
    ) -> None:
        """Stacked PR: branch created from feature branch, not main.

        Feature branch has closer merge-base to current HEAD than main.
        """
        current = _make_branch("stacked-feature", "current_sha")
        main = _make_branch("main", "main_sha")
        feature = _make_branch("base-feature", "feature_sha")

        mb_main = _make_merge_base("mb_main_sha")
        mb_feature = _make_merge_base("mb_feature_sha")

        repo = _setup_repo(
            {"stacked-feature": current, "main": main, "base-feature": feature},
            mock_ctx,
        )

        def merge_base_side_effect(*args: Any) -> list[MagicMock]:
            candidate_commit = args[1]
            if candidate_commit is main.commit:
                return [mb_main]
            if candidate_commit is feature.commit:
                return [mb_feature]
            return []

        repo.merge_base.side_effect = merge_base_side_effect

        def iter_commits_side_effect(rev_range: str) -> list[MagicMock]:
            if rev_range == f"{mb_main.hexsha}..{current.commit.hexsha}":
                return [MagicMock()] * 12  # far from main
            if rev_range == f"{mb_feature.hexsha}..{current.commit.hexsha}":
                return [MagicMock()] * 2  # close to feature branch
            return []

        repo.iter_commits.side_effect = iter_commits_side_effect

        result = detect_parent_branch_via_merge_base(Path("/repo"), "stacked-feature")

        assert result == "base-feature"


@patch(f"{MODULE}.get_default_branch_name", create=True, return_value="main")
@patch(f"{MODULE}._safe_repo_context")
@patch(f"{MODULE}.is_git_repository", return_value=True)
class TestDefaultBranchTiebreaker:
    """Default branch wins when distances are equal."""

    def test_prefers_default_branch_on_equal_distance(
        self,
        _mock_is_git: MagicMock,
        mock_ctx: MagicMock,
        _mock_default: MagicMock,
    ) -> None:
        """Two candidates with equal distance — default branch wins."""
        current = _make_branch("my-feature", "current_sha")
        main = _make_branch("main", "main_sha")
        develop = _make_branch("develop", "develop_sha")

        mb_main = _make_merge_base("mb_main_sha")
        mb_develop = _make_merge_base("mb_develop_sha")

        repo = _setup_repo(
            {"my-feature": current, "main": main, "develop": develop},
            mock_ctx,
        )

        def merge_base_side_effect(*args: Any) -> list[MagicMock]:
            candidate_commit = args[1]
            if candidate_commit is main.commit:
                return [mb_main]
            if candidate_commit is develop.commit:
                return [mb_develop]
            return []

        repo.merge_base.side_effect = merge_base_side_effect

        def iter_commits_side_effect(rev_range: str) -> list[MagicMock]:
            if rev_range == f"{mb_main.hexsha}..{current.commit.hexsha}":
                return [MagicMock()] * 5
            if rev_range == f"{mb_develop.hexsha}..{current.commit.hexsha}":
                return [MagicMock()] * 5  # same distance
            return []

        repo.iter_commits.side_effect = iter_commits_side_effect

        result = detect_parent_branch_via_merge_base(Path("/repo"), "my-feature")

        assert result == "main"


@patch(f"{MODULE}.get_default_branch_name", create=True, return_value="main")
@patch(f"{MODULE}._safe_repo_context")
@patch(f"{MODULE}.is_git_repository", return_value=True)
class TestThresholdFiltering:
    """Threshold-based candidate filtering."""

    def test_excludes_candidates_beyond_threshold(
        self,
        _mock_is_git: MagicMock,
        mock_ctx: MagicMock,
        _mock_default: MagicMock,
    ) -> None:
        """Candidate with distance > threshold is excluded."""
        current = _make_branch("my-feature", "current_sha")
        main = _make_branch("main", "main_sha")

        mb_main = _make_merge_base("mb_main_sha")

        repo = _setup_repo(
            {"my-feature": current, "main": main},
            mock_ctx,
        )

        repo.merge_base.return_value = [mb_main]

        def iter_commits_side_effect(rev_range: str) -> list[MagicMock]:
            if rev_range == f"{mb_main.hexsha}..{current.commit.hexsha}":
                return [MagicMock()] * (MERGE_BASE_DISTANCE_THRESHOLD + 1)
            return []

        repo.iter_commits.side_effect = iter_commits_side_effect

        result = detect_parent_branch_via_merge_base(Path("/repo"), "my-feature")

        assert result is None

    def test_includes_candidate_at_threshold(
        self,
        _mock_is_git: MagicMock,
        mock_ctx: MagicMock,
        _mock_default: MagicMock,
    ) -> None:
        """Candidate with distance == threshold is included."""
        current = _make_branch("my-feature", "current_sha")
        main = _make_branch("main", "main_sha")

        mb_main = _make_merge_base("mb_main_sha")

        repo = _setup_repo(
            {"my-feature": current, "main": main},
            mock_ctx,
        )

        repo.merge_base.return_value = [mb_main]

        def iter_commits_side_effect(rev_range: str) -> list[MagicMock]:
            if rev_range == f"{mb_main.hexsha}..{current.commit.hexsha}":
                return [MagicMock()] * MERGE_BASE_DISTANCE_THRESHOLD
            return []

        repo.iter_commits.side_effect = iter_commits_side_effect

        result = detect_parent_branch_via_merge_base(Path("/repo"), "my-feature")

        assert result == "main"


@patch(f"{MODULE}.get_default_branch_name", create=True, return_value="main")
@patch(f"{MODULE}._safe_repo_context")
@patch(f"{MODULE}.is_git_repository")
class TestEdgeCases:
    """Edge cases and boundary conditions."""

    def test_returns_none_for_non_git_repo(
        self,
        mock_is_git: MagicMock,
        _mock_ctx: MagicMock,
        _mock_default: MagicMock,
    ) -> None:
        """Non-git directory returns None."""
        mock_is_git.return_value = False

        result = detect_parent_branch_via_merge_base(Path("/not-a-repo"), "main")

        assert result is None

    def test_returns_none_when_no_candidates_pass(
        self,
        mock_is_git: MagicMock,
        mock_ctx: MagicMock,
        _mock_default: MagicMock,
    ) -> None:
        """All candidates exceed threshold — returns None."""
        mock_is_git.return_value = True

        current = _make_branch("my-feature", "current_sha")
        branch_a = _make_branch("branch-a", "a_sha")
        branch_b = _make_branch("branch-b", "b_sha")

        mb = _make_merge_base("mb_sha")

        repo = _setup_repo(
            {"my-feature": current, "branch-a": branch_a, "branch-b": branch_b},
            mock_ctx,
        )

        repo.merge_base.return_value = [mb]

        def iter_commits_side_effect(rev_range: str) -> list[MagicMock]:
            return [MagicMock()] * (MERGE_BASE_DISTANCE_THRESHOLD + 5)

        repo.iter_commits.side_effect = iter_commits_side_effect

        result = detect_parent_branch_via_merge_base(Path("/repo"), "my-feature")

        assert result is None

    def test_skips_current_branch(
        self,
        mock_is_git: MagicMock,
        mock_ctx: MagicMock,
        _mock_default: MagicMock,
    ) -> None:
        """Current branch is not considered as a candidate."""
        mock_is_git.return_value = True

        current = _make_branch("my-feature", "current_sha")
        main = _make_branch("main", "main_sha")

        mb_main = _make_merge_base("mb_main_sha")

        repo = _setup_repo(
            {"my-feature": current, "main": main},
            mock_ctx,
        )

        repo.merge_base.return_value = [mb_main]

        def iter_commits_side_effect(rev_range: str) -> list[MagicMock]:
            if rev_range == f"{mb_main.hexsha}..{current.commit.hexsha}":
                return [MagicMock()] * 2
            return []

        repo.iter_commits.side_effect = iter_commits_side_effect

        result = detect_parent_branch_via_merge_base(Path("/repo"), "my-feature")

        assert result == "main"
        # Verify merge_base was NOT called with current branch's own commit
        # as both arguments
        for call in repo.merge_base.call_args_list:
            call_args = call[0]
            assert not (
                call_args[0] is current.commit and call_args[1] is current.commit
            )

    def test_distance_zero_collects_all_candidates(
        self,
        mock_is_git: MagicMock,
        mock_ctx: MagicMock,
        _mock_default: MagicMock,
    ) -> None:
        """Two candidates at distance=0 — default branch wins (no early exit)."""
        mock_is_git.return_value = True

        current = _make_branch("my-feature", "current_sha")
        main = _make_branch("main", "main_sha")
        develop = _make_branch("develop", "develop_sha")

        mb_main = _make_merge_base("mb_main_sha")
        mb_develop = _make_merge_base("mb_develop_sha")

        repo = _setup_repo(
            {"my-feature": current, "main": main, "develop": develop},
            mock_ctx,
        )

        def merge_base_side_effect(*args: Any) -> list[MagicMock]:
            candidate_commit = args[1]
            if candidate_commit is main.commit:
                return [mb_main]
            if candidate_commit is develop.commit:
                return [mb_develop]
            return []

        repo.merge_base.side_effect = merge_base_side_effect

        def iter_commits_side_effect(rev_range: str) -> list[MagicMock]:
            # Both at distance 0
            if rev_range == f"{mb_main.hexsha}..{current.commit.hexsha}":
                return []
            if rev_range == f"{mb_develop.hexsha}..{current.commit.hexsha}":
                return []
            return []

        repo.iter_commits.side_effect = iter_commits_side_effect

        result = detect_parent_branch_via_merge_base(Path("/repo"), "my-feature")

        # Default branch should win the tiebreaker, not just first-found
        assert result == "main"

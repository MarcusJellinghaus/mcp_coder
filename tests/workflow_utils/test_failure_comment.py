"""Tests for the shared failure comment builder in failure_handling."""

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from mcp_coder.workflow_utils.failure_handling import (
    FIELD_ORDER,
    _branch_head,
    build_failure_comment,
)

MODULE = "mcp_coder.workflow_utils.failure_handling"
PROJECT_DIR = Path("/fake/project")
BUILD_URL = "https://jenkins.example/job/1/"


def _labels(comment: str) -> list[str]:
    """Return the field labels in render order."""
    return [
        line[2:].split(":**", 1)[0]
        for line in comment.splitlines()
        if line.startswith("**")
    ]


def _build(**kwargs: object) -> str:
    """Build a comment with branch lookup patched to ``("feat", "abc1234")``."""
    with patch(f"{MODULE}._branch_head", return_value=("feat", "abc1234")):
        return build_failure_comment(PROJECT_DIR, **kwargs)  # type: ignore[arg-type]


class TestBuildFailureComment:
    """Tests for build_failure_comment."""

    def test_heading(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            comment = _build(title="CI Fix", kind="Crashed")
        assert comment.splitlines()[0] == "## ❌ CI Fix Crashed"

    @pytest.mark.parametrize("label", FIELD_ORDER)
    def test_field_order(self, label: str) -> None:
        builder_owned = {"Branch", "Elapsed", "Build"}
        fields = [
            (lbl, "x") for lbl in reversed(FIELD_ORDER) if lbl not in builder_owned
        ]
        with patch.dict(os.environ, {"BUILD_URL": BUILD_URL}, clear=True):
            comment = _build(title="T", kind="Failed", fields=fields, elapsed=5.0)
        labels = _labels(comment)
        assert labels == list(FIELD_ORDER)
        idx = labels.index(label)
        if idx > 0:
            assert labels[idx - 1] == FIELD_ORDER[FIELD_ORDER.index(label) - 1]
        if idx < len(labels) - 1:
            assert labels[idx + 1] == FIELD_ORDER[FIELD_ORDER.index(label) + 1]

    def test_none_values_skipped(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            comment = _build(
                title="T",
                kind="Failed",
                fields=[("Category", "c"), ("Stage", None), ("Error", "e")],
            )
        assert "**Stage:**" not in comment
        assert _labels(comment) == ["Category", "Error", "Branch"]

    def test_unknown_label_before_next_step(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            comment = _build(
                title="T",
                kind="Failed",
                fields=[("Next step", "n"), ("Foo", "f"), ("Verdict", "v")],
            )
        assert _labels(comment) == ["Branch", "Verdict", "Foo", "Next step"]

    @pytest.mark.parametrize(
        ("head", "expected"),
        [
            (("feat", "abc1234"), "**Branch:** feat @ abc1234"),
            (("feat", None), "**Branch:** feat"),
            ((None, None), None),
        ],
    )
    def test_branch_line(
        self, head: tuple[str | None, str | None], expected: str | None
    ) -> None:
        with (
            patch.dict(os.environ, {}, clear=True),
            patch(f"{MODULE}._branch_head", return_value=head),
        ):
            comment = build_failure_comment(PROJECT_DIR, title="T", kind="Failed")
        if expected is None:
            assert "**Branch:**" not in comment
        else:
            assert expected in comment.splitlines()

    def test_build_url_set_is_last_field(self) -> None:
        with patch.dict(os.environ, {"BUILD_URL": BUILD_URL}, clear=True):
            comment = _build(
                title="T", kind="Failed", fields=[("Next step", "n")], elapsed=1.0
            )
        assert comment.splitlines()[-1] == f"**Build:** {BUILD_URL}"

    def test_build_url_cleared_no_build_line(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            comment = _build(title="T", kind="Failed")
        assert "**Build:**" not in comment

    def test_elapsed_formatted(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            comment = _build(title="T", kind="Failed", elapsed=754.0)
        assert "**Elapsed:** 12m 34s" in comment.splitlines()

    def test_extra_section_after_blank_line(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            comment = _build(
                title="T",
                kind="Failed",
                fields=[("Category", "c")],
                extra_section="### Details\nmore",
            )
        assert comment.endswith("**Branch:** feat @ abc1234\n\n### Details\nmore")


class TestBranchHead:
    """Tests for _branch_head."""

    def test_branch_lookup_raises(self) -> None:
        with (
            patch(
                f"{MODULE}.get_current_branch_name", side_effect=RuntimeError("boom")
            ),
            patch(f"{MODULE}.get_latest_commit_sha", return_value="abc1234def"),
        ):
            assert _branch_head(PROJECT_DIR) == (None, None)

    def test_no_branch(self) -> None:
        with (
            patch(f"{MODULE}.get_current_branch_name", return_value=None),
            patch(f"{MODULE}.get_latest_commit_sha", return_value="abc1234def"),
        ):
            assert _branch_head(PROJECT_DIR) == (None, None)

    def test_sha_lookup_raises(self) -> None:
        with (
            patch(f"{MODULE}.get_current_branch_name", return_value="feat"),
            patch(f"{MODULE}.get_latest_commit_sha", side_effect=RuntimeError("boom")),
        ):
            assert _branch_head(PROJECT_DIR) == ("feat", None)

    def test_sha_truncated(self) -> None:
        with (
            patch(f"{MODULE}.get_current_branch_name", return_value="feat"),
            patch(
                f"{MODULE}.get_latest_commit_sha",
                return_value="abc1234def5678",
            ),
        ):
            assert _branch_head(PROJECT_DIR) == ("feat", "abc1234")

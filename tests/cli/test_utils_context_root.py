"""Tests for the Claude context-root finder and reporter in cli/utils.py.

A separate module from test_utils.py, which would otherwise cross the repo's
750-line guidance.
"""

import logging
import warnings
from pathlib import Path
from unittest.mock import patch

import pytest

from mcp_coder.cli.utils import (
    find_context_claude_md,
    is_outside_project_dir,
    report_context_root,
)
from mcp_coder.utils.log_utils import OUTPUT


class TestContextRootReporting:
    """Test cases for the CLAUDE.md context-root finder and reporter."""

    # --- find_context_claude_md -------------------------------------------

    def test_finds_root_level_claude_md(self, tmp_path: Path) -> None:
        """A root-level CLAUDE.md in the start directory is found."""
        expected = tmp_path / "CLAUDE.md"
        expected.write_text("rules", encoding="utf-8")

        assert find_context_claude_md(tmp_path) == [expected.resolve()]

    def test_finds_dot_claude_claude_md(self, tmp_path: Path) -> None:
        """A .claude/CLAUDE.md in the start directory is found."""
        (tmp_path / ".claude").mkdir()
        expected = tmp_path / ".claude" / "CLAUDE.md"
        expected.write_text("rules", encoding="utf-8")

        assert find_context_claude_md(tmp_path) == [expected.resolve()]

    def test_returns_every_hit_at_the_nearest_level(self, tmp_path: Path) -> None:
        """Both candidates at one level are returned - order is not precedence."""
        root_level = tmp_path / "CLAUDE.md"
        root_level.write_text("rules", encoding="utf-8")
        (tmp_path / ".claude").mkdir()
        dot_claude = tmp_path / ".claude" / "CLAUDE.md"
        dot_claude.write_text("more rules", encoding="utf-8")

        result = find_context_claude_md(tmp_path)

        assert len(result) == 2
        assert set(result) == {root_level.resolve(), dot_claude.resolve()}

    def test_nearest_level_wins(self, tmp_path: Path) -> None:
        """A child's CLAUDE.md shadows the parent's - the walk stops at the first hit."""
        (tmp_path / "CLAUDE.md").write_text("parent", encoding="utf-8")
        child = tmp_path / "child"
        child.mkdir()
        child_file = child / "CLAUDE.md"
        child_file.write_text("child", encoding="utf-8")

        assert find_context_claude_md(child) == [child_file.resolve()]

    def test_finds_claude_md_in_ancestor(self, tmp_path: Path) -> None:
        """The walk climbs to an ancestor when the start directory has none."""
        ancestor = tmp_path / "a"
        ancestor.mkdir()
        start = ancestor / "b"
        start.mkdir()
        expected = ancestor / "CLAUDE.md"
        expected.write_text("rules", encoding="utf-8")

        result = find_context_claude_md(start, stop_at=tmp_path)

        assert result == [expected.resolve()]

    def test_returns_empty_when_nothing_found(self, tmp_path: Path) -> None:
        """No CLAUDE.md up to the boundary yields [].

        stop_at is what makes this assertion a statement about the code rather
        than about the machine: without it the walk runs to the filesystem root,
        through real ancestors of tmp_path that no test controls.
        """
        start = tmp_path / "a" / "b"
        start.mkdir(parents=True)

        assert find_context_claude_md(start, stop_at=tmp_path) == []

    def test_boundary_is_inclusive(self, tmp_path: Path) -> None:
        """A CLAUDE.md in stop_at itself is still found."""
        start = tmp_path / "a" / "b"
        start.mkdir(parents=True)
        expected = tmp_path / "CLAUDE.md"
        expected.write_text("rules", encoding="utf-8")

        result = find_context_claude_md(start, stop_at=tmp_path)

        assert result == [expected.resolve()]

    # --- is_outside_project_dir -------------------------------------------

    @pytest.mark.parametrize(
        ("hit_subpath", "project_subpath", "expected"),
        [
            ("repo/CLAUDE.md", "repo", False),
            ("tool_env/CLAUDE.md", "repo", True),
            ("tool_env/CLAUDE.md", None, False),
        ],
    )
    def test_is_outside_project_dir(
        self,
        tmp_path: Path,
        hit_subpath: str,
        project_subpath: str | None,
        expected: bool,
    ) -> None:
        """Outside means not inside project_dir; a None project_dir is never outside."""
        hit = tmp_path / hit_subpath
        project_dir = None if project_subpath is None else tmp_path / project_subpath

        assert is_outside_project_dir(hit, project_dir) is expected

    # --- report_context_root ----------------------------------------------

    def test_report_logs_working_directory(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """The Claude working directory is named at OUTPUT level."""
        with caplog.at_level(OUTPUT, logger="mcp_coder.cli.utils"):
            report_context_root(tmp_path, tmp_path)

        assert "Claude working directory" in caplog.text
        assert str(tmp_path) in caplog.text

    def test_report_logs_every_hit(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Both files at the nearest level are named, not one picked by precedence."""
        root_level = tmp_path / "CLAUDE.md"
        root_level.write_text("rules", encoding="utf-8")
        (tmp_path / ".claude").mkdir()
        dot_claude = tmp_path / ".claude" / "CLAUDE.md"
        dot_claude.write_text("more rules", encoding="utf-8")

        with caplog.at_level(OUTPUT, logger="mcp_coder.cli.utils"):
            report_context_root(tmp_path, tmp_path)

        assert str(root_level.resolve()) in caplog.text
        assert str(dot_claude.resolve()) in caplog.text

    def test_report_says_none_found(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """An explicit "none found" is logged when the walk finds nothing.

        The finder is patched because report_context_root deliberately has no
        stop_at boundary - the real walk would run past tmp_path into
        directories no test controls. The walk itself is covered above.
        """
        with patch("mcp_coder.cli.utils.find_context_claude_md", return_value=[]):
            with caplog.at_level(OUTPUT, logger="mcp_coder.cli.utils"):
                report_context_root(tmp_path, tmp_path)

        assert "none found" in caplog.text

    def test_report_warns_when_hit_is_outside_project_dir(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """The December Jenkins scenario: rules live outside the driven project."""
        tool_env = tmp_path / "tool_env"
        tool_env.mkdir()
        stale = tool_env / "CLAUDE.md"
        stale.write_text("call mcp__filesystem__*", encoding="utf-8")
        repo = tmp_path / "repo"
        repo.mkdir()

        with caplog.at_level(OUTPUT, logger="mcp_coder.cli.utils"):
            report_context_root(tool_env, repo)

        warnings_logged = [r for r in caplog.records if r.levelno >= logging.WARNING]
        assert len(warnings_logged) == 1
        assert str(stale.resolve()) in warnings_logged[0].getMessage()

    def test_report_does_not_warn_when_hit_is_inside_project_dir(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """A CLAUDE.md inside project_dir is the expected case - no warning."""
        repo = tmp_path / "repo"
        repo.mkdir()
        (repo / "CLAUDE.md").write_text("rules", encoding="utf-8")

        with caplog.at_level(OUTPUT, logger="mcp_coder.cli.utils"):
            report_context_root(repo, repo)

        assert [r for r in caplog.records if r.levelno >= logging.WARNING] == []

    def test_report_does_not_warn_without_project_dir(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """With no project_dir there is no anchor to be outside of."""
        tool_env = tmp_path / "tool_env"
        tool_env.mkdir()
        (tool_env / "CLAUDE.md").write_text("rules", encoding="utf-8")

        with caplog.at_level(OUTPUT, logger="mcp_coder.cli.utils"):
            report_context_root(tool_env, None)

        assert [r for r in caplog.records if r.levelno >= logging.WARNING] == []

    # --- wiring into resolve_execution_dir --------------------------------

    def test_resolver_reports_on_default_branch(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """The project_dir default reports the context root."""
        from mcp_coder.cli.utils import resolve_execution_dir

        with caplog.at_level(OUTPUT, logger="mcp_coder.cli.utils"):
            resolve_execution_dir(None, project_dir=tmp_path)

        assert "Claude working directory" in caplog.text

    def test_resolver_reports_on_explicit_branch(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """An explicit --execution-dir reports the context root too."""
        from mcp_coder.cli.utils import resolve_execution_dir

        with caplog.at_level(OUTPUT, logger="mcp_coder.cli.utils"):
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", DeprecationWarning)
                resolve_execution_dir(str(tmp_path))

        assert "Claude working directory" in caplog.text

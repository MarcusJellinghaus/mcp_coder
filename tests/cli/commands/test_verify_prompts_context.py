"""Tests for the project-instructions rows in the verify PROMPTS section.

A separate module from ``test_verify.py``, which is already at 727 lines —
six more tests there would cross the repo's 750-line file-size guidance
(``mcp-coder check file-size --max-lines 750``).

Fixture setup and the ``execute_verify`` invocation pattern follow the
PROMPTS test class in ``test_verify.py``.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from mcp_coder.cli.commands.verify import execute_verify
from mcp_coder.cli.commands.verify_formatting import STATUS_SYMBOLS
from mcp_coder.utils.pyproject_config import PromptsConfig

from .conftest import _make_args, _make_verify_mocks

_VERIFY = "mcp_coder.cli.commands.verify"


def _prompts_section(output: str) -> list[str]:
    """Return the PROMPTS section lines, section header excluded."""
    lines = output.splitlines()
    start = next(i for i, line in enumerate(lines) if line.startswith("=== PROMPTS "))
    section: list[str] = []
    for line in lines[start + 1 :]:
        if line.startswith("=== "):
            break
        section.append(line)
    return section


def _run_verify(project_dir: Path, capsys: pytest.CaptureFixture[str]) -> list[str]:
    """Run ``execute_verify`` against *project_dir* and return its PROMPTS lines."""
    with _make_verify_mocks():
        execute_verify(_make_args(project_dir=str(project_dir)))
    return _prompts_section(capsys.readouterr().out)


def _row(section: list[str], label: str) -> str:
    """Return the single row whose label field is *label*."""
    matches = [line for line in section if line.strip().startswith(label)]
    assert len(matches) == 1, f"expected exactly one {label!r} row, got {matches!r}"
    return matches[0]


class TestVerifyReportsClaudeCwd:
    """The Claude working directory is named before the run, not after."""

    def test_claude_cwd_row_names_project_dir(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        section = _run_verify(tmp_path, capsys)

        row = _row(section, "Claude cwd")
        assert str(tmp_path.resolve()) in row
        assert STATUS_SYMBOLS["success"] in row


class TestVerifyReportsProjectInstructions:
    """Every CLAUDE.md at the nearest ancestor level is named."""

    def test_project_claude_md_reported(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        (tmp_path / "CLAUDE.md").write_text("rules", encoding="utf-8")

        section = _run_verify(tmp_path, capsys)

        row = _row(section, "Project instructions")
        assert str((tmp_path / "CLAUDE.md").resolve()) in row
        assert STATUS_SYMBOLS["success"] in row

    def test_both_candidates_at_the_same_level_reported(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        (tmp_path / "CLAUDE.md").write_text("rules", encoding="utf-8")
        (tmp_path / ".claude").mkdir()
        (tmp_path / ".claude" / "CLAUDE.md").write_text("more", encoding="utf-8")

        section = _run_verify(tmp_path, capsys)

        rendered = "\n".join(section)
        assert str((tmp_path / "CLAUDE.md").resolve()) in rendered
        assert str((tmp_path / ".claude" / "CLAUDE.md").resolve()) in rendered
        # Continuation rows carry an empty label, so only the first is labelled.
        labelled = [
            line for line in section if line.strip().startswith("Project instructions")
        ]
        assert len(labelled) == 1

    def test_none_found_uses_success_marker(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        # Patched rather than arranged on disk: verify walks without a stop_at
        # boundary, so a CLAUDE.md in any real ancestor of tmp_path would
        # falsify the assertion. The walk itself is covered by the
        # find_context_claude_md tests, which do pass stop_at; what this test
        # owns is the rendering of the empty result.
        with patch(f"{_VERIFY}.find_context_claude_md", return_value=[]):
            section = _run_verify(tmp_path, capsys)

        row = _row(section, "Project instructions")
        assert "none found" in row
        # A project may legitimately have no CLAUDE.md - not a warning.
        assert STATUS_SYMBOLS["success"] in row
        assert STATUS_SYMBOLS["warning"] not in row

    def test_hit_outside_project_dir_warns(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        (tmp_path / "CLAUDE.md").write_text("stale rules", encoding="utf-8")
        project_dir = tmp_path / "repo"
        project_dir.mkdir()

        section = _run_verify(project_dir, capsys)

        row = _row(section, "Project instructions")
        assert str((tmp_path / "CLAUDE.md").resolve()) in row
        assert STATUS_SYMBOLS["warning"] in row
        assert "outside project directory" in row

    def test_own_claude_md_does_not_mask_a_stale_ancestor(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Claude loads the whole chain, so verify reports the whole chain.

        Were the walk to stop at the nearest level, a project holding its own
        CLAUDE.md would silence the outside-project_dir warning entirely - the
        common case, and the drift this report exists to catch.
        """
        stale = tmp_path / "CLAUDE.md"
        stale.write_text("call mcp__filesystem__*", encoding="utf-8")
        project_dir = tmp_path / "repo"
        project_dir.mkdir()
        own = project_dir / "CLAUDE.md"
        own.write_text("project rules", encoding="utf-8")

        section = _run_verify(project_dir, capsys)

        labelled = _row(section, "Project instructions")
        assert str(own.resolve()) in labelled
        assert STATUS_SYMBOLS["warning"] not in labelled

        stale_row = next(line for line in section if str(stale.resolve()) in line)
        assert STATUS_SYMBOLS["warning"] in stale_row
        assert "outside project directory" in stale_row


class TestVerifyRedundancyRowUnmoved:
    """Regression guard on the insertion point of the new rows."""

    @patch(f"{_VERIFY}.is_claude_md", return_value=True)
    @patch(f"{_VERIFY}.get_project_prompt_path", return_value="some/path")
    @patch(
        f"{_VERIFY}.load_prompts",
        return_value=(
            "sys content",
            "proj content",
            PromptsConfig(
                system_prompt=None,
                project_prompt=".claude/CLAUDE.md",
                claude_system_prompt_mode="append",
            ),
        ),
    )
    def test_redundancy_row_still_last_in_section(
        self,
        _mock_load: object,
        _mock_path: object,
        _mock_is_claude: object,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        (tmp_path / "CLAUDE.md").write_text("rules", encoding="utf-8")

        section = _run_verify(tmp_path, capsys)

        def index_of(label: str) -> int:
            return section.index(_row(section, label))

        assert (
            index_of("Claude mode")
            < index_of("Claude cwd")
            < index_of("Project instructions")
            < index_of("Redundancy")
        )

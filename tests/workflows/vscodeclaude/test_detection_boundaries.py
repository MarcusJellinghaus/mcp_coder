"""Tests for name-boundary matching in window titles and cmdlines.

Covers ``_contains_bounded`` and its two callers, ``_title_binds`` and
``_cmdline_scan``: a name only matches when it is not continued by a name
character, so ``mcp_coder`` does not bind ``mcp_coder_utils`` and issue
``#134`` does not bind ``#1342``.
"""

import pytest

from mcp_coder.workflows.vscodeclaude.detection import (
    _cmdline_scan,
    _contains_bounded,
    _title_binds,
)
from tests.workflows.vscodeclaude._detection_helpers import _force_windows, _snapshot

TITLE_1407 = "[#1407 new] vscodeclaude: stale VSCode mai... - mcp_coder"
TITLE_1394 = "[#1394 new] docs: fine-grained PAT list in... - mcp_coder"
TITLE_283 = "[#283 new] Configure the mcp-coder toolki... - mcp-tools-py"
TITLE_60 = "[#60 new] Truncation logic - mcp-tools-py"

CMDLINE_1342 = (
    '"C:\\Users\\Marcus\\AppData\\Local\\Programs\\Microsoft VS Code\\Code.exe" '
    "C:\\Users\\Marcus\\Documents\\VSCC\\mcp_coder_1342.code-workspace "
    "C:\\Users\\Marcus\\Documents\\VSCC\\mcp_coder_1342\\.vscodeclaude_status.txt"
).lower()
CMDLINE_1342_NO_WORKSPACE = (
    '"C:\\Users\\Marcus\\AppData\\Local\\Programs\\Microsoft VS Code\\Code.exe" '
    "C:\\Users\\Marcus\\Documents\\VSCC\\mcp_coder_1342\\.vscodeclaude_status.txt"
).lower()


class TestContainsBounded:
    """Negative-boundary substring match shared by title and cmdline checks."""

    @pytest.mark.parametrize(
        "haystack",
        [
            "mcp_coder",
            "mcp_coder at start",
            "ends with mcp_coder",
            '"mcp_coder"',
            "x mcp_coder y",
            "mcp_coder.code-workspace",
            "c:\\vscc\\mcp_coder\\file",
            "c:/vscc/mcp_coder/file",
        ],
    )
    def test_accepted_neighbours(self, haystack: str) -> None:
        """Start/end of string, quotes, spaces, '.', '\\' and '/' are boundaries."""
        assert _contains_bounded(haystack, "mcp_coder") is True

    @pytest.mark.parametrize(
        "haystack",
        [
            "mcp_coder_utils",
            "x_mcp_coder",
            "mcp_coder-x",
            "-mcp_coder",
            "mcp_codera",
            "amcp_coder",
            "mcp_coder1",
            "1mcp_coder",
        ],
    )
    def test_rejected_neighbours(self, haystack: str) -> None:
        """'_', '-', letters and digits continue the name and reject the match."""
        assert _contains_bounded(haystack, "mcp_coder") is False

    def test_any_occurrence_counts(self) -> None:
        """A bounded occurrence after an unbounded one still matches."""
        assert _contains_bounded("mcp_coder_utils - mcp_coder", "mcp_coder") is True


class TestTitleBindsBoundaries:
    """`_title_binds` matches issue number and repo name on name boundaries."""

    @pytest.mark.parametrize(
        ("title", "issue_number", "repo", "binds"),
        [
            ("[#1342 new] x - mcp_coder", 134, "o/mcp_coder", False),
            ("[#134 impl] x - mcp_coder", 134, "o/mcp_coder", True),
            ("[#134] x - mcp_coder", 134, "o/mcp_coder", True),
            (TITLE_1407, 1407, "o/mcp_coder", True),
            ("[#5 new] x - mcp_coder_utils", 5, "o/mcp_coder", False),
            ("[#5 new] fix mcp_coder_utils import - mcp_coder", 5, "o/mcp_coder", True),
            (TITLE_60, 60, "o/mcp-tools-py", True),
            (TITLE_60, 60, "o/mcp-tools", False),
        ],
    )
    def test_title_binds(
        self,
        monkeypatch: pytest.MonkeyPatch,
        title: str,
        issue_number: int,
        repo: str,
        binds: bool,
    ) -> None:
        """Only an exact issue number and an unextended repo name bind."""
        _force_windows(monkeypatch)
        snapshot = _snapshot(window_titles=((100, title),))

        assert _title_binds(snapshot, issue_number, repo) is binds

    def test_real_titles_bind_only_their_own_session(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Of the real open windows, only the #1407 title binds #1407/mcp_coder."""
        _force_windows(monkeypatch)
        others = _snapshot(
            window_titles=((1, TITLE_1394), (2, TITLE_283), (3, TITLE_60)),
        )
        everything = _snapshot(
            window_titles=(
                (1, TITLE_1394),
                (2, TITLE_283),
                (3, TITLE_60),
                (4, TITLE_1407),
            ),
        )

        assert _title_binds(others, 1407, "o/mcp_coder") is False
        assert _title_binds(everything, 1407, "o/mcp_coder") is True


class TestCmdlineScanBoundaries:
    """`_cmdline_scan` matches the folder name / path on name boundaries."""

    @pytest.mark.parametrize(
        ("cmdline", "folder_name", "matches"),
        [
            (CMDLINE_1342, "mcp_coder_134", False),
            ("code.exe c:\\vscc\\mcp_coder_1342-folder2 --x", "mcp_coder_134", False),
            ("code.exe c:\\vscc\\mcp_coder_1342-folder2 --x", "mcp_coder_1342", False),
            (CMDLINE_1342, "mcp_coder_1342", True),
            (CMDLINE_1342_NO_WORKSPACE, "mcp_coder_1342", True),
            ('code.exe "c:\\vscc\\mcp_coder_1342"', "mcp_coder_1342", True),
            ("code.exe c:\\vscc\\mcp_coder_1342", "mcp_coder_1342", True),
        ],
    )
    def test_folder_name(self, cmdline: str, folder_name: str, matches: bool) -> None:
        """The folder name matches only when it is not continued by a name char."""
        snapshot = _snapshot(processes=({"pid": 100, "cmdline_lower": cmdline},))

        matched, pid = _cmdline_scan(snapshot, f"c:/x/{folder_name}")

        assert matched is matches
        assert pid == (100 if matches else None)

    @pytest.mark.parametrize(
        ("cmdline", "matches"),
        [
            ('code.exe "c:/other/mcp_coder_1342"', True),
            ("code.exe c:/other/mcp_coder_1342", True),
            ("code.exe c:/other/mcp_coder_1342.code-workspace", True),
            ("code.exe c:/other/mcp_coder_13420", False),
        ],
    )
    def test_full_path(self, cmdline: str, matches: bool) -> None:
        """The full forward-slash path matches verbatim on name boundaries."""
        snapshot = _snapshot(processes=({"pid": 7, "cmdline_lower": cmdline},))

        matched, _pid = _cmdline_scan(snapshot, "C:/other/mcp_coder_1342")

        assert matched is matches

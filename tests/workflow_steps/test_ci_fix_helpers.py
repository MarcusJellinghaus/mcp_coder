"""Tests for the no-change check in ``workflow_steps/ci_fix_helpers.py``."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from mcp_coder.workflow_steps import ci_fix_helpers
from mcp_coder.workflow_steps.ci_fix_helpers import discard_if_no_change, read_head
from mcp_coder.workflow_steps.constants import COMMIT_MESSAGE_FILE

_HEAD = "a" * 40
_REAL_FILE = "src/mcp_coder/module.py"


def _status(
    *,
    success: bool = True,
    staged: list[str] | None = None,
    modified: list[str] | None = None,
    untracked: list[str] | None = None,
) -> dict[str, object]:
    """Build a ``get_working_tree_status`` result."""
    return {
        "success": success,
        "staged": staged or [],
        "modified": modified or [],
        "untracked": untracked or [],
    }


@pytest.fixture(name="read_sha")
def fixture_read_sha(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    """Patch the helpers' HEAD read; it returns ``_HEAD`` unless told otherwise."""
    read_sha = MagicMock(return_value=_HEAD)
    monkeypatch.setattr(ci_fix_helpers, "get_latest_commit_sha", read_sha)
    return read_sha


@pytest.fixture(name="read_status")
def fixture_read_status(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    """Patch the helpers' status read; the tree is clean unless told otherwise."""
    read_status = MagicMock(return_value=_status())
    monkeypatch.setattr(ci_fix_helpers, "get_working_tree_status", read_status)
    return read_status


def _write_message_file(project_dir: Path) -> Path:
    """Create a real commit message file under ``project_dir``."""
    message_file = project_dir / COMMIT_MESSAGE_FILE
    message_file.parent.mkdir(parents=True)
    message_file.write_text("fix: something\n", encoding="utf-8")
    return message_file


class TestReadHead:
    """``read_head`` returns the SHA, or None on any failure."""

    def test_returns_sha(self, read_sha: MagicMock, tmp_path: Path) -> None:
        """The SHA comes from the git read."""
        assert read_head(tmp_path) == _HEAD
        read_sha.assert_called_once_with(tmp_path)

    def test_returns_none_when_read_raises(
        self, read_sha: MagicMock, tmp_path: Path
    ) -> None:
        """A raising read does not escape."""
        read_sha.side_effect = RuntimeError("boom")

        assert read_head(tmp_path) is None


@pytest.mark.usefixtures("read_sha")
class TestNoChange:
    """Attempts that changed nothing."""

    def test_same_head_and_clean_tree(
        self, read_status: MagicMock, tmp_path: Path
    ) -> None:
        """An unchanged HEAD and a clean tree count as no change."""
        assert discard_if_no_change(tmp_path, _HEAD) is True
        read_status.assert_called_once_with(tmp_path)

    def test_only_message_file_is_removed(
        self, read_status: MagicMock, tmp_path: Path
    ) -> None:
        """The unused message file is ignored, then deleted."""
        message_file = _write_message_file(tmp_path)
        read_status.return_value = _status(untracked=[COMMIT_MESSAGE_FILE])

        assert discard_if_no_change(tmp_path, _HEAD) is True
        assert not message_file.exists()

    def test_only_build_artifact(self, read_status: MagicMock, tmp_path: Path) -> None:
        """A changed ``uv.lock`` is not a change."""
        read_status.return_value = _status(modified=["uv.lock"])

        assert discard_if_no_change(tmp_path, _HEAD) is True


class TestHasChanges:
    """Attempts that changed something, or whose state could not be read."""

    @pytest.mark.usefixtures("read_status")
    def test_changed_head(self, read_sha: MagicMock, tmp_path: Path) -> None:
        """A commit made during the attempt is a change."""
        read_sha.return_value = "b" * 40

        assert discard_if_no_change(tmp_path, _HEAD) is False

    @pytest.mark.usefixtures("read_status")
    @pytest.mark.parametrize("current_head", [_HEAD, None])
    def test_no_baseline(
        self, read_sha: MagicMock, tmp_path: Path, current_head: str | None
    ) -> None:
        """A failed baseline read counts as a change, even if both reads failed."""
        read_sha.return_value = current_head

        assert discard_if_no_change(tmp_path, None) is False

    @pytest.mark.usefixtures("read_status")
    def test_current_head_unreadable(self, read_sha: MagicMock, tmp_path: Path) -> None:
        """A failed read of the current HEAD counts as a change."""
        read_sha.return_value = None

        assert discard_if_no_change(tmp_path, _HEAD) is False

    @pytest.mark.usefixtures("read_sha")
    def test_status_unsuccessful(self, read_status: MagicMock, tmp_path: Path) -> None:
        """``success=False`` from the status read counts as a change."""
        read_status.return_value = _status(success=False)

        assert discard_if_no_change(tmp_path, _HEAD) is False

    @pytest.mark.usefixtures("read_sha")
    def test_status_raises(self, read_status: MagicMock, tmp_path: Path) -> None:
        """A raising status read counts as a change and does not escape."""
        read_status.side_effect = RuntimeError("boom")

        assert discard_if_no_change(tmp_path, _HEAD) is False

    @pytest.mark.usefixtures("read_sha")
    def test_real_change_keeps_message_file(
        self, read_status: MagicMock, tmp_path: Path
    ) -> None:
        """A real change beside the message file leaves it for the commit."""
        message_file = _write_message_file(tmp_path)
        read_status.return_value = _status(
            modified=[_REAL_FILE], untracked=[COMMIT_MESSAGE_FILE]
        )

        assert discard_if_no_change(tmp_path, _HEAD) is False
        assert message_file.exists()

    @pytest.mark.usefixtures("read_sha")
    @pytest.mark.parametrize("bucket", ["staged", "modified", "untracked"])
    def test_real_file_in_each_bucket(
        self, read_status: MagicMock, tmp_path: Path, bucket: str
    ) -> None:
        """A real file counts wherever the status read lists it."""
        read_status.return_value = {**_status(), bucket: [_REAL_FILE]}

        assert discard_if_no_change(tmp_path, _HEAD) is False

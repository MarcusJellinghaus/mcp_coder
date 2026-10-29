"""Tests for apply_final_label (retry once, then exit code 1)."""

import logging
from pathlib import Path
from typing import Iterator
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.mcp_workspace_github import GitHubRateLimitError
from mcp_coder.workflow_utils.label_transitions import apply_final_label

MODULE = "mcp_coder.workflow_utils.label_transitions"


@pytest.fixture
def mocks() -> Iterator[dict[str, MagicMock]]:
    """Patch the label update, the manager and sleep."""
    with (
        patch(f"{MODULE}.update_workflow_label") as mock_update,
        patch(f"{MODULE}.IssueManager") as mock_manager,
        patch(f"{MODULE}.time.sleep") as mock_sleep,
        patch(
            f"{MODULE}.get_current_branch_name", return_value="77-some-feature"
        ) as mock_branch,
    ):
        yield {
            "update": mock_update,
            "manager": mock_manager,
            "sleep": mock_sleep,
            "branch": mock_branch,
        }


def _errors(caplog: pytest.LogCaptureFixture) -> list[logging.LogRecord]:
    return [r for r in caplog.records if r.levelno == logging.ERROR]


def test_success_first_try(mocks: dict[str, MagicMock], tmp_path: Path) -> None:
    mocks["update"].return_value = True
    assert apply_final_label(tmp_path, "implementing", "code_review", 12) == 0
    mocks["sleep"].assert_not_called()
    mocks["manager"].assert_called_once_with(project_dir=tmp_path)
    mocks["update"].assert_called_once_with(
        mocks["manager"].return_value,
        "implementing",
        "code_review",
        validated_issue_number=12,
    )


def test_success_on_retry(mocks: dict[str, MagicMock], tmp_path: Path) -> None:
    mocks["update"].side_effect = [False, True]
    assert apply_final_label(tmp_path, "implementing", "code_review", 12) == 0
    mocks["sleep"].assert_called_once_with(30)
    assert mocks["update"].call_count == 2


def test_both_attempts_fail(
    mocks: dict[str, MagicMock],
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    mocks["update"].return_value = False
    with caplog.at_level(logging.DEBUG):
        assert apply_final_label(tmp_path, "implementing", "code_review", 12) == 1
    mocks["sleep"].assert_called_once_with(30)
    errors = _errors(caplog)
    assert len(errors) == 1
    assert "#12" in errors[0].getMessage()
    assert "code_review" in errors[0].getMessage()


def test_rate_limit_twice(
    mocks: dict[str, MagicMock],
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    mocks["update"].side_effect = GitHubRateLimitError("limited")
    with caplog.at_level(logging.DEBUG):
        assert apply_final_label(tmp_path, "fixing_ci", "pr_created", 12) == 1
    assert mocks["update"].call_count == 2
    assert len(_errors(caplog)) == 1


def test_issue_number_from_branch(
    mocks: dict[str, MagicMock],
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    mocks["update"].return_value = False
    with caplog.at_level(logging.DEBUG):
        assert apply_final_label(tmp_path, "implementing", "code_review") == 1
    mocks["branch"].assert_called_once_with(tmp_path)
    errors = _errors(caplog)
    assert len(errors) == 1
    assert "#77" in errors[0].getMessage()

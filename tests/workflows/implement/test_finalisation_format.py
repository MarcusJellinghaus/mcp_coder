"""Tests for formatting before the finalisation commit."""

import logging
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.workflow_steps import commit
from mcp_coder.workflow_steps.commit import FormatterConfigError
from mcp_coder.workflows.implement import finalisation
from mcp_coder.workflows.implement.finalisation import run_finalisation

FIN = "mcp_coder.workflows.implement.finalisation"

CHANGED: dict[str, list[str]] = {
    "staged": [],
    "modified": ["src/a.py"],
    "untracked": [],
}


def _llm_response(text: str = "done") -> dict[str, Any]:
    return {
        "text": text,
        "session_id": "session-1",
        "version": "1.0",
        "timestamp": "2025-01-01T00:00:00",
        "provider": "claude",
        "raw_response": {},
    }


@dataclass
class FinalisationMocks:
    """Patched collaborators of run_finalisation, attached to one parent."""

    parent: MagicMock
    prompt_llm: MagicMock
    get_full_status: MagicMock
    commit_all_changes: MagicMock
    push_changes: MagicMock


@pytest.fixture
def mocks() -> Iterator[FinalisationMocks]:
    """Incomplete tasks; the LLM answers; the tree has changes; commit and push succeed."""
    parent = MagicMock()
    with (
        patch(f"{FIN}.has_incomplete_work", return_value=True),
        patch(f"{FIN}.prepare_llm_environment", return_value={}),
        patch(f"{FIN}.get_branch_name_for_logging", return_value="branch"),
        patch(f"{FIN}.llm_permissions", return_value=[]),
        patch(f"{FIN}.bash_grants_of", return_value=[]),
        patch(f"{FIN}.get_prompt", return_value="prompt"),
        patch(f"{FIN}.resolve_prompt_slots", return_value={}),
        patch(f"{FIN}.fill_prompt", return_value="prompt"),
        patch(f"{FIN}.prompt_llm", return_value=_llm_response()) as prompt_llm,
        patch(f"{FIN}.store_session"),
        patch(f"{FIN}.get_full_status", return_value=CHANGED) as get_full_status,
        patch(
            f"{FIN}.generate_commit_message_with_llm",
            return_value=(True, "msg", None),
        ),
        patch(
            f"{FIN}.commit_all_changes",
            return_value={"success": True, "commit_hash": "abc123"},
        ) as commit_all_changes,
        patch(f"{FIN}.push_changes", return_value=True) as push_changes,
    ):
        parent.attach_mock(get_full_status, "get_full_status")
        parent.attach_mock(commit_all_changes, "commit_all_changes")
        yield FinalisationMocks(
            parent, prompt_llm, get_full_status, commit_all_changes, push_changes
        )


def _call_names(parent: MagicMock) -> list[str]:
    return [name for name, _args, _kwargs in parent.mock_calls]


class TestFormatBeforeFinalisationCommit:
    """format_best_effort runs before the changes check and the commit."""

    def test_formats_before_status_and_commit(
        self,
        tmp_path: Path,
        mocks: FinalisationMocks,
        formatter_mocks: SimpleNamespace,
    ) -> None:
        mocks.parent.attach_mock(
            formatter_mocks.format_best_effort, "format_best_effort"
        )

        result = run_finalisation(tmp_path, "claude")

        assert result is True
        formatter_mocks.format_best_effort.assert_called_once()
        assert formatter_mocks.format_best_effort.call_args.args[0] == tmp_path
        names = _call_names(mocks.parent)
        assert names.index("format_best_effort") < names.index("get_full_status")
        assert names.index("format_best_effort") < names.index("commit_all_changes")

    def test_empty_response_skips_formatter(
        self,
        tmp_path: Path,
        mocks: FinalisationMocks,
        formatter_mocks: SimpleNamespace,
    ) -> None:
        mocks.prompt_llm.return_value = _llm_response("")

        result = run_finalisation(tmp_path, "claude")

        assert result is False
        formatter_mocks.format_best_effort.assert_not_called()
        mocks.commit_all_changes.assert_not_called()

    @pytest.mark.parametrize(
        "formatter_kwargs",
        [
            {"side_effect": FormatterConfigError("bad toolkit")},
            {"return_value": False},
        ],
        ids=["raises", "returns_false"],
    )
    def test_failed_formatting_warns_and_still_commits(
        self,
        formatter_kwargs: dict[str, object],
        tmp_path: Path,
        mocks: FinalisationMocks,
        monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        run_formatters = MagicMock(**formatter_kwargs)
        monkeypatch.setattr(
            finalisation, "format_best_effort", commit.format_best_effort
        )
        monkeypatch.setattr(commit, "run_formatters", run_formatters)

        with caplog.at_level(logging.WARNING):
            result = run_finalisation(tmp_path, "claude")

        assert result is True
        run_formatters.assert_called_once_with(tmp_path)
        warnings = [
            r
            for r in caplog.records
            if r.levelno == logging.WARNING
            and "Formatting failed before finalisation commit" in r.getMessage()
        ]
        assert len(warnings) == 1
        mocks.commit_all_changes.assert_called_once()
        mocks.push_changes.assert_called_once_with(tmp_path)

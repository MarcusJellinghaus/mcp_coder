"""Formatter switch + pre-flight tests for the review core loop.

The review loop formats only through the real
:func:`mcp_coder.workflow_steps.commit.run_formatters`, so the single
``[tool.mcp-coder] format_code`` gate governs it. The shared ``env`` fixture
mocks ``core.run_formatters``; tests here restore the real one.
"""

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from mcp_coder.workflow_steps import commit
from mcp_coder.workflows.review import core
from tests.workflows.review.conftest import _DISMISS, _TASKS, _resp, _reviewer, _run


def test_format_code_false_skips_formatter_in_tasks_round(
    env: SimpleNamespace, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """``format_code = false`` → a ``tasks`` round never calls the formatter."""
    monkeypatch.setattr(core, "run_formatters", commit.run_formatters)
    (tmp_path / "pyproject.toml").write_text(
        "[tool.mcp-coder]\nformat_code = false\n", encoding="utf-8"
    )
    wrapper = MagicMock(return_value={})
    monkeypatch.setattr(commit, "run_format_code", wrapper)
    env.prompt_llm.side_effect = [
        _reviewer(),
        _resp(_TASKS),
        _reviewer("applied"),
        _reviewer(),
        _resp(_DISMISS),
    ]

    result = _run(tmp_path)

    assert result == 0
    env.commit_changes.assert_called_once()
    wrapper.assert_not_called()

"""Tests for workflow_steps.commit.format_best_effort."""

import logging
from pathlib import Path
from unittest.mock import patch

import pytest

from mcp_coder.workflow_steps.commit import FormatterConfigError, format_best_effort

_RUN = "mcp_coder.workflow_steps.commit.run_formatters"
_CONTEXT = "the plan commit"


def _warnings(caplog: pytest.LogCaptureFixture) -> list[str]:
    return [r.getMessage() for r in caplog.records if r.levelno == logging.WARNING]


def test_success_logs_no_warning(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """A True result is silent."""
    with patch(_RUN, return_value=True) as run, caplog.at_level(logging.WARNING):
        format_best_effort(tmp_path, _CONTEXT)
    run.assert_called_once_with(tmp_path)
    assert not _warnings(caplog)


def test_false_logs_one_warning_with_context(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """A False result logs one WARNING naming the context."""
    with patch(_RUN, return_value=False), caplog.at_level(logging.WARNING):
        format_best_effort(tmp_path, _CONTEXT)
    warnings = _warnings(caplog)
    assert len(warnings) == 1
    assert _CONTEXT in warnings[0]


def test_config_error_logs_warning_and_does_not_raise(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """A FormatterConfigError is logged with its message, not raised."""
    with (
        patch(_RUN, side_effect=FormatterConfigError("bad toolkit")),
        caplog.at_level(logging.WARNING),
    ):
        format_best_effort(tmp_path, _CONTEXT)
    warnings = _warnings(caplog)
    assert len(warnings) == 1
    assert _CONTEXT in warnings[0]
    assert "bad toolkit" in warnings[0]


def test_runtime_error_logs_warning_and_does_not_raise(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """Any other exception is logged, not raised."""
    with (
        patch(_RUN, side_effect=RuntimeError("boom")),
        caplog.at_level(logging.WARNING),
    ):
        format_best_effort(tmp_path, _CONTEXT)
    warnings = _warnings(caplog)
    assert len(warnings) == 1
    assert _CONTEXT in warnings[0]
    assert "boom" in warnings[0]

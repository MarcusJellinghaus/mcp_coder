"""Tests for the autouse formatter_mocks fixture in tests/conftest.py."""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from mcp_coder.workflow_steps import ci, commit
from mcp_coder.workflows.implement import core as implement_core


def test_implement_core_is_patched(formatter_mocks: SimpleNamespace) -> None:
    """An importing workflow module sees the shared mock."""
    assert vars(implement_core)["run_formatters"] is formatter_mocks.run_formatters


def test_ci_is_patched(formatter_mocks: SimpleNamespace) -> None:
    """An importing workflow_steps module sees the shared mock."""
    assert vars(ci)["run_formatters"] is formatter_mocks.run_formatters


def test_commit_module_keeps_real_functions() -> None:
    """The defining module is never patched."""
    for func, name in (
        (commit.run_formatters, "run_formatters"),
        (commit.format_best_effort, "format_best_effort"),
    ):
        assert not isinstance(func, MagicMock)
        assert func.__module__ == "mcp_coder.workflow_steps.commit"
        assert func.__name__ == name


@pytest.mark.real_formatters
def test_real_formatters_marker_opts_out() -> None:
    """The marker leaves importing modules with the real function."""
    real = vars(implement_core)["run_formatters"]
    assert not isinstance(real, MagicMock)
    assert real is commit.run_formatters

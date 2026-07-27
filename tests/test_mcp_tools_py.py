"""Unit tests for the mcp_tools_py wrapper module.

Verifies that the thin wrappers forward project defaults to the external
mcp_tools_py library without overriding them, and return library results
unchanged. No subprocesses, no git - plain fast unit tests.
"""

import sys
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from mcp_coder.mcp_tools_py import PylintResult, run_pylint_check, run_pytest_check


class TestRunPytestCheck:
    """Unit tests for the run_pytest_check wrapper."""

    def test_forwards_project_dir_and_python_executable(self, tmp_path: Path) -> None:
        """Wrapper passes project_dir as str and sys.executable, nothing else."""
        expected: dict[str, Any] = {
            "success": True,
            "summary": {"passed": 1, "failed": 0},
            "summary_text": "1 passed",
            "failed_tests_prompt": None,
            "test_results": object(),
            "error_info": None,
        }
        with patch(
            "mcp_coder.mcp_tools_py._check_code_with_pytest", return_value=expected
        ) as mock_check:
            result = run_pytest_check(tmp_path)

        assert result is expected
        mock_check.assert_called_once_with(
            project_dir=str(tmp_path),
            python_executable=sys.executable,
        )

    def test_library_defaults_not_overridden(self, tmp_path: Path) -> None:
        """No markers, timeout_seconds, or extra_args kwargs are passed."""
        with patch(
            "mcp_coder.mcp_tools_py._check_code_with_pytest", return_value={}
        ) as mock_check:
            run_pytest_check(tmp_path)

        _, kwargs = mock_check.call_args
        for forbidden in ("markers", "timeout_seconds", "extra_args"):
            assert forbidden not in kwargs

    def test_accepts_str_project_dir(self, tmp_path: Path) -> None:
        """A str project_dir is forwarded as str unchanged."""
        with patch(
            "mcp_coder.mcp_tools_py._check_code_with_pytest", return_value={}
        ) as mock_check:
            run_pytest_check(str(tmp_path))

        _, kwargs = mock_check.call_args
        assert kwargs["project_dir"] == str(tmp_path)

    def test_crash_dict_returned_unchanged(self, tmp_path: Path) -> None:
        """The crash-path dict (success=False, error only) passes through as-is."""
        crash: dict[str, Any] = {"success": False, "error": "Test run timed out"}
        with patch(
            "mcp_coder.mcp_tools_py._check_code_with_pytest", return_value=crash
        ):
            result = run_pytest_check(tmp_path)

        assert result is crash


class TestRunPylintCheck:
    """Unit tests for the run_pylint_check wrapper."""

    def test_forwards_resolved_target_directories(self, tmp_path: Path) -> None:
        """Resolved target directories are forwarded to get_pylint_results."""
        pylint_result = PylintResult(return_code=0, messages=[])
        with (
            patch(
                "mcp_tools_py.utils.project_config.resolve_target_directories",
                return_value=["src", "tests"],
            ) as mock_resolve,
            patch(
                "mcp_coder.mcp_tools_py._get_pylint_results",
                return_value=pylint_result,
            ) as mock_pylint,
        ):
            result = run_pylint_check(tmp_path)

        assert result is pylint_result
        mock_resolve.assert_called_once_with(str(tmp_path), None)
        mock_pylint.assert_called_once_with(
            project_dir=str(tmp_path),
            python_executable=sys.executable,
            target_directories=["src", "tests"],
        )

    def test_raises_runtime_error_when_resolution_fails(self, tmp_path: Path) -> None:
        """A str return from resolve_target_directories raises RuntimeError."""
        with (
            patch(
                "mcp_tools_py.utils.project_config.resolve_target_directories",
                return_value="No pyproject.toml found",
            ),
            patch("mcp_coder.mcp_tools_py._get_pylint_results") as mock_pylint,
        ):
            with pytest.raises(RuntimeError, match="No pyproject.toml found"):
                run_pylint_check(tmp_path)

        mock_pylint.assert_not_called()

    def test_result_returned_unchanged(self, tmp_path: Path) -> None:
        """The PylintResult from the library passes through as-is."""
        pylint_result = PylintResult(
            return_code=1, messages=[], error=None, raw_output="[]"
        )
        with (
            patch(
                "mcp_tools_py.utils.project_config.resolve_target_directories",
                return_value=["src"],
            ),
            patch(
                "mcp_coder.mcp_tools_py._get_pylint_results",
                return_value=pylint_result,
            ),
        ):
            result = run_pylint_check(tmp_path)

        assert result is pylint_result

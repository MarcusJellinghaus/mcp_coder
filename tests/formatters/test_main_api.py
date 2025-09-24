"""Tests for combined API implementation using TDD approach.

Tests the main API functions including format_code() combined functionality,
re-exports, and line-length conflict warning integration.
"""

import tempfile
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import Mock, patch

import pytest

from mcp_coder.formatters import FormatterResult


@pytest.mark.formatter_integration
class TestCombinedAPICoreFunctionality:
    """Test combined API core functionality (3 tests)."""

    @patch("mcp_coder.formatters.format_with_black")
    @patch("mcp_coder.formatters.format_with_isort")
    def test_format_code_runs_both_formatters_sequentially(
        self, mock_isort: Mock, mock_black: Mock
    ) -> None:
        """Test format_code() running Black + isort sequentially."""
        # Setup
        mock_black.return_value = FormatterResult(
            success=True,
            files_changed=["src/test.py"],
            formatter_name="black",
        )
        mock_isort.return_value = FormatterResult(
            success=True,
            files_changed=["src/imports.py"],
            formatter_name="isort",
        )

        # Import here to ensure we test the actual implementation
        from mcp_coder.formatters import format_code

        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)

            # Execute
            result = format_code(project_root)

            # Verify both formatters called
            mock_black.assert_called_once_with(project_root, None)
            mock_isort.assert_called_once_with(project_root, None)

            # Verify combined results
            assert isinstance(result, dict)
            assert "black" in result
            assert "isort" in result
            assert result["black"].formatter_name == "black"
            assert result["isort"].formatter_name == "isort"
            assert result["black"].files_changed == ["src/test.py"]
            assert result["isort"].files_changed == ["src/imports.py"]

    @patch("mcp_coder.formatters.format_with_black")
    @patch("mcp_coder.formatters.format_with_isort")
    def test_format_code_with_individual_formatter_selection(
        self, mock_isort: Mock, mock_black: Mock
    ) -> None:
        """Test format_code(formatters=["black"]) runs only Black."""
        # Setup
        mock_black.return_value = FormatterResult(
            success=True,
            files_changed=["src/test.py"],
            formatter_name="black",
        )

        # Import here to ensure we test the actual implementation
        from mcp_coder.formatters import format_code

        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)

            # Execute - only Black requested
            result = format_code(project_root, formatters=["black"])

            # Verify only Black called
            mock_black.assert_called_once_with(project_root, None)
            mock_isort.assert_not_called()

            # Verify results contain only Black
            assert isinstance(result, dict)
            assert "black" in result
            assert "isort" not in result
            assert result["black"].formatter_name == "black"

    @patch("mcp_coder.formatters.format_with_black")
    @patch("mcp_coder.formatters.format_with_isort")
    def test_format_code_error_handling_one_formatter_fails(
        self, mock_isort: Mock, mock_black: Mock
    ) -> None:
        """Test when one formatter fails, other still runs."""
        # Setup - Black fails, isort succeeds
        mock_black.return_value = FormatterResult(
            success=False,
            files_changed=[],
            formatter_name="black",
            error_message="Black failed",
        )
        mock_isort.return_value = FormatterResult(
            success=True,
            files_changed=["src/imports.py"],
            formatter_name="isort",
        )

        # Import here to ensure we test the actual implementation
        from mcp_coder.formatters import format_code

        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)

            # Execute
            result = format_code(project_root)

            # Verify both formatters called despite Black failure
            mock_black.assert_called_once_with(project_root, None)
            mock_isort.assert_called_once_with(project_root, None)

            # Verify combined results include both success and failure
            assert isinstance(result, dict)
            assert "black" in result
            assert "isort" in result
            assert result["black"].success is False
            assert result["black"].error_message == "Black failed"
            assert result["isort"].success is True
            assert result["isort"].files_changed == ["src/imports.py"]


@pytest.mark.formatter_integration
class TestAPIExportsAndImports:
    """Test API exports and imports (2 tests)."""

    @patch("mcp_coder.formatters.black_formatter.format_with_black")
    @patch("mcp_coder.formatters.isort_formatter.format_with_isort")
    def test_re_exports_work_from_init(
        self, mock_isort_module: Mock, mock_black_module: Mock
    ) -> None:
        """Verify format_with_black() and format_with_isort() work from __init__.py."""
        # Setup mock returns
        mock_black_module.return_value = FormatterResult(
            success=True, files_changed=[], formatter_name="black"
        )
        mock_isort_module.return_value = FormatterResult(
            success=True, files_changed=[], formatter_name="isort"
        )

        # Import re-exported functions from __init__.py
        from mcp_coder.formatters import format_with_black, format_with_isort

        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)

            # Test Black re-export
            black_result = format_with_black(project_root)
            assert isinstance(black_result, FormatterResult)
            assert black_result.formatter_name == "black"

            # Test isort re-export
            isort_result = format_with_isort(project_root)
            assert isinstance(isort_result, FormatterResult)
            assert isort_result.formatter_name == "isort"

    def test_public_api_imports(self) -> None:
        """Test all expected functions/classes are importable."""
        # Test all expected imports work
        from mcp_coder.formatters import (
            FormatterResult,
            format_code,
            format_with_black,
            format_with_isort,
        )

        # Verify types
        assert FormatterResult is not None
        assert callable(format_code)
        assert callable(format_with_black)
        assert callable(format_with_isort)


@pytest.mark.formatter_integration
class TestLineLengthConflictIntegration:
    """Test line-length conflict integration (1 test)."""

    @patch("builtins.print")
    def test_format_code_shows_line_length_conflict_warning(
        self, mock_print: Mock
    ) -> None:
        """Test that format_code() shows warning when Black/isort line lengths differ."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)

            # Create pyproject.toml with conflicting line lengths
            pyproject_content = """
[tool.black]
line-length = 100

[tool.isort]
line_length = 88
"""
            (project_root / "pyproject.toml").write_text(pyproject_content)

            # Mock the formatter functions to avoid actual formatting
            with patch("mcp_coder.formatters.format_with_black") as mock_black:
                with patch("mcp_coder.formatters.format_with_isort") as mock_isort:
                    mock_black.return_value = FormatterResult(
                        success=True, files_changed=[], formatter_name="black"
                    )
                    mock_isort.return_value = FormatterResult(
                        success=True, files_changed=[], formatter_name="isort"
                    )

                    # Import and call format_code
                    from mcp_coder.formatters import format_code

                    format_code(project_root)

                    # Verify warning was printed
                    warning_calls = [
                        call
                        for call in mock_print.call_args_list
                        if "Line length mismatch" in str(call)
                    ]
                    assert len(warning_calls) > 0

                    # Check specific warning content
                    warning_text = str(mock_print.call_args_list)
                    assert "Black=100" in warning_text
                    assert "isort=88" in warning_text

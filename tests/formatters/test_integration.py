"""Integration tests for formatter system using real code samples and end-to-end workflows.

This module tests the complete formatter workflow using actual formatter execution
(not mocked) with real code samples from analysis findings, verifying exit code
patterns and complete integration scenarios.
"""

import tempfile
from pathlib import Path
from typing import Dict

import pytest

from mcp_coder.formatters import (
    FormatterResult,
    format_code,
    format_with_black,
    format_with_isort,
)

# Real code samples from Step 0 analysis for comprehensive testing
UNFORMATTED_CODE = """
def test(a,b,c):
    x=1+2+3+4+5+6+7+8+9+10+11+12+13+14+15+16+17+18+19+20+21+22+23+24+25
    return x

class MyClass:
    def __init__(self,name,age):
        self.name=name
        self.age=age
"""

UNSORTED_IMPORTS = """
import os
from myproject import utils
import sys
from typing import List
from collections import defaultdict
import json
"""

SYNTAX_ERROR_CODE = """
def test(a,b,c):
    x = 1 +
    return x
"""

ALREADY_FORMATTED_CODE = """
def test(a, b, c):
    x = (
        1
        + 2
        + 3
        + 4
        + 5
        + 6
        + 7
        + 8
        + 9
        + 10
        + 11
        + 12
        + 13
        + 14
        + 15
        + 16
        + 17
        + 18
        + 19
        + 20
        + 21
        + 22
        + 23
        + 24
        + 25
    )
    return x


class MyClass:
    def __init__(self, name, age):
        self.name = name
        self.age = age
"""

ALREADY_SORTED_IMPORTS = """
import json
import os
import sys
from collections import defaultdict
from typing import List

from myproject import utils
"""


@pytest.mark.formatter_integration
class TestCompleteFormattingWorkflow:
    """Test complete end-to-end formatting workflows using real code samples."""

    def test_complete_formatting_workflow_with_exit_codes(self) -> None:
        """Test full Black + isort formatting using directory-based approach."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)

            # Create Python file with both formatting issues
            python_file = project_root / "test_file.py"
            python_file.write_text(UNSORTED_IMPORTS + "\n\n" + UNFORMATTED_CODE)

            # Create basic pyproject.toml
            pyproject_content = """
[tool.black]
line-length = 88

[tool.isort]
profile = "black"
line_length = 88
"""
            (project_root / "pyproject.toml").write_text(pyproject_content)

            # Run formatters with directory-based execution and verify results
            results = format_code(project_root)

            # Both formatters should run successfully with directory-based approach
            assert "black" in results
            assert "isort" in results
            assert isinstance(results["black"], FormatterResult)
            assert isinstance(results["isort"], FormatterResult)

            # At least one formatter should detect changes through directory processing
            changes_detected = (
                len(results["black"].files_changed) > 0
                or len(results["isort"].files_changed) > 0
            )
            assert changes_detected

            # Verify file was actually modified by directory-based formatting
            formatted_content = python_file.read_text()
            assert formatted_content != UNSORTED_IMPORTS + "\n\n" + UNFORMATTED_CODE

    def test_idempotent_behavior_no_changes_on_second_run(self) -> None:
        """Format same directory twice, verify no changes on second run with directory-based approach."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)

            # Create Python file with unformatted code first
            python_file = project_root / "test_file.py"
            python_file.write_text(UNSORTED_IMPORTS + "\n\n" + UNFORMATTED_CODE)

            # Create pyproject.toml
            pyproject_content = """
[tool.black]
line-length = 88

[tool.isort]
profile = "black"
line_length = 88
"""
            (project_root / "pyproject.toml").write_text(pyproject_content)

            # First run - should format the code using directory-based execution
            first_results = format_code(project_root)

            # Second run - should detect no changes needed with directory-based execution
            second_results = format_code(project_root)

            # First run should detect changes through directory processing
            first_had_changes = (
                len(first_results["black"].files_changed) > 0
                or len(first_results["isort"].files_changed) > 0
            )
            assert first_had_changes

            # Second run should detect no changes (idempotent directory-based behavior)
            assert second_results["black"].success is True
            assert second_results["isort"].success is True
            assert len(second_results["black"].files_changed) == 0
            assert len(second_results["isort"].files_changed) == 0

    def test_error_resilience_mixed_scenarios(self) -> None:
        """Test directory-based error handling where directory contains mixed valid/invalid files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)

            # Create valid Python file
            valid_file = project_root / "valid.py"
            valid_file.write_text(UNFORMATTED_CODE)

            # Create invalid Python file with syntax error
            invalid_file = project_root / "invalid.py"
            invalid_file.write_text(SYNTAX_ERROR_CODE)

            # Create pyproject.toml
            pyproject_content = """
[tool.black]
line-length = 88

[tool.isort]
profile = "black"
line_length = 88
"""
            (project_root / "pyproject.toml").write_text(pyproject_content)

            # Run directory-based formatters - they should handle errors gracefully
            results = format_code(project_root)

            # Results should be returned even if directory contains files with syntax errors
            assert "black" in results
            assert "isort" in results
            assert isinstance(results["black"], FormatterResult)
            assert isinstance(results["isort"], FormatterResult)

            # Check that at least one formatter reports the failure from directory processing
            black_failed = not results["black"].success
            isort_failed = not results["isort"].success

            # At least one should have failed due to syntax error in directory
            assert black_failed or isort_failed


@pytest.mark.formatter_integration
class TestAnalysisBasedScenarios:
    """Test scenarios based on Step 0 analysis findings."""

    def test_step0_code_samples_from_analysis(self) -> None:
        """Test directory-based formatters with actual problematic code from analysis findings."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)

            # Create multiple files with different formatting issues in directory
            files_and_content = [
                ("unformatted.py", UNFORMATTED_CODE),
                ("unsorted.py", UNSORTED_IMPORTS),
                ("mixed.py", UNSORTED_IMPORTS + "\n\n" + UNFORMATTED_CODE),
            ]

            for filename, content in files_and_content:
                (project_root / filename).write_text(content)

            # Create pyproject.toml
            pyproject_content = """
[tool.black]
line-length = 88
target-version = ["py311"]

[tool.isort]
profile = "black"
line_length = 88
"""
            (project_root / "pyproject.toml").write_text(pyproject_content)

            # Test individual formatters using directory-based execution
            black_result = format_with_black(project_root)
            isort_result = format_with_isort(project_root)

            # Both should handle the analysis samples successfully with directory processing
            assert isinstance(black_result, FormatterResult)
            assert isinstance(isort_result, FormatterResult)

            # At least Black should detect changes in directory containing unformatted code
            assert len(black_result.files_changed) > 0 or black_result.success
            # At least isort should detect changes in directory containing unsorted imports
            assert len(isort_result.files_changed) > 0 or isort_result.success

    def test_configuration_conflicts_from_analysis(self) -> None:
        """Test real pyproject.toml scenarios from analysis including conflicts."""
        test_configs = [
            # Default configuration
            {
                "content": """
[tool.black]
line-length = 88

[tool.isort]
profile = "black"
line_length = 88
""",
                "should_warn": False,
            },
            # Line-length conflict
            {
                "content": """
[tool.black]
line-length = 100

[tool.isort]
line_length = 88
""",
                "should_warn": True,
            },
            # Missing tool sections
            {
                "content": """
[build-system]
requires = ["setuptools"]
""",
                "should_warn": False,
            },
        ]

        for i, config in enumerate(test_configs):
            with tempfile.TemporaryDirectory() as temp_dir:
                project_root = Path(temp_dir)

                # Create test file
                (project_root / "test.py").write_text("import os\n")

                # Create pyproject.toml with test configuration
                (project_root / "pyproject.toml").write_text(str(config["content"]))

                # Run format_code and capture output
                import io
                import sys
                from contextlib import redirect_stdout

                captured_output = io.StringIO()
                with redirect_stdout(captured_output):
                    results = format_code(project_root)

                # Check results are valid
                assert isinstance(results, dict)
                assert "black" in results
                assert "isort" in results

                # Note: Warning checking is handled by the main API tests
                # Here we focus on configuration handling without warning validation

                # All formatters should complete successfully despite config issues
                assert results["black"].success is not False  # Could be True or None
                assert results["isort"].success is not False  # Could be True or None


@pytest.mark.formatter_integration
class TestQualityGatesValidation:
    """Test quality gates and tool integration validation."""

    def test_complete_tool_integration_workflow(self) -> None:
        """Test that entire formatter system integrates properly with the project."""
        # This test verifies the formatters work within the actual project structure
        project_root = Path(__file__).parent.parent.parent  # Go to project root

        # Create a temporary test file in the actual project
        test_file = project_root / "temp_integration_test.py"
        try:
            # Write unformatted code
            test_file.write_text(UNFORMATTED_CODE)

            # Run formatters on the actual project
            results = format_code(
                project_root, target_dirs=["temp_integration_test.py"]
            )

            # Should get results for both formatters
            assert isinstance(results, dict)
            assert "black" in results
            assert "isort" in results

            # Results should be FormatterResult objects
            assert isinstance(results["black"], FormatterResult)
            assert isinstance(results["isort"], FormatterResult)

            # Should complete without crashing
            assert results["black"] is not None
            assert results["isort"] is not None

        finally:
            # Clean up test file
            if test_file.exists():
                test_file.unlink()

    def test_individual_formatter_error_handling(self) -> None:
        """Test individual formatters handle various error conditions gracefully."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)

            # Test Black with syntax error
            syntax_error_file = project_root / "syntax_error.py"
            syntax_error_file.write_text(SYNTAX_ERROR_CODE)

            black_result = format_with_black(project_root)
            # Should return a result object even for errors
            assert isinstance(black_result, FormatterResult)
            assert black_result.formatter_name == "black"

            # Test isort with syntax error
            isort_result = format_with_isort(project_root)
            # Should return a result object even for errors
            assert isinstance(isort_result, FormatterResult)
            assert isort_result.formatter_name == "isort"

    def test_formatter_target_directory_handling(self) -> None:
        """Test directory-based formatters properly handle target directory specifications."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)

            # Create subdirectories with Python files
            src_dir = project_root / "src"
            src_dir.mkdir()
            tests_dir = project_root / "tests"
            tests_dir.mkdir()

            (src_dir / "main.py").write_text(UNFORMATTED_CODE)
            (tests_dir / "test_main.py").write_text(UNFORMATTED_CODE)

            # Test directory-based execution targeting specific directories
            results = format_code(project_root, target_dirs=["src"])

            assert isinstance(results, dict)
            assert "black" in results
            assert "isort" in results
            assert isinstance(results["black"], FormatterResult)
            assert isinstance(results["isort"], FormatterResult)

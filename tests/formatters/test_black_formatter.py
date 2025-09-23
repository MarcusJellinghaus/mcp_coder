"""Tests for Black formatter implementation using TDD approach.

Based on Step 2 requirements: 6 comprehensive tests covering core formatting,
configuration integration, and real-world analysis scenarios.
"""

import tempfile
from pathlib import Path
from typing import Any, Dict, Generator

import pytest

from mcp_coder.formatters import FormatterResult


# Test fixtures and utilities
@pytest.fixture
def temp_project_dir() -> Generator[Path, None, None]:
    """Create a temporary project directory for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        project_path = Path(temp_dir)
        yield project_path


@pytest.fixture
def unformatted_python_code() -> str:
    """Sample Python code that needs Black formatting."""
    return """def hello(name,age):
    if name=="Alice":
        print(f"Hello {name}, you are {age} years old")
    else:
        print("Hello stranger")
"""


@pytest.fixture
def formatted_python_code() -> str:
    """Sample Python code that is already properly formatted."""
    return """def hello(name: str, age: int) -> None:
    if name == "Alice":
        print(f"Hello {name}, you are {age} years old")
    else:
        print("Hello stranger")
"""


@pytest.fixture
def syntax_error_code() -> str:
    """Python code with syntax errors."""
    return """def broken_function(
    print("This has syntax errors"
    invalid syntax here
"""


@pytest.fixture
def pyproject_toml_with_black_config() -> str:
    """pyproject.toml content with Black configuration."""
    return """[tool.black]
line-length = 100
target-version = ["py311"]
"""


class TestBlackFormatterCore:
    """Core formatting scenarios - 3 tests."""

    def test_format_unformatted_code(
        self, temp_project_dir: Path, unformatted_python_code: str
    ) -> None:
        """Test format_with_black() on code needing formatting (exit 1 → success)."""
        # This test will fail until we implement the Black formatter
        from mcp_coder.formatters.black_formatter import format_with_black

        # Create a Python file that needs formatting
        test_file = temp_project_dir / "test_module.py"
        test_file.write_text(unformatted_python_code)

        # Format the code
        result = format_with_black(temp_project_dir)

        # Should succeed and report the file as changed
        assert result.success is True
        assert result.formatter_name == "black"
        assert str(test_file) in result.files_changed
        assert result.error_message is None

        # Verify the file was actually formatted
        formatted_content = test_file.read_text()
        assert formatted_content != unformatted_python_code
        # Should have proper spacing around operators
        assert "name == " in formatted_content

    def test_format_already_formatted_code(
        self, temp_project_dir: Path, formatted_python_code: str
    ) -> None:
        """Test on properly formatted code (exit 0 → no changes)."""
        from mcp_coder.formatters.black_formatter import format_with_black

        # Create a Python file that is already formatted
        test_file = temp_project_dir / "test_module.py"
        test_file.write_text(formatted_python_code)
        original_content = formatted_python_code

        # Format the code
        result = format_with_black(temp_project_dir)

        # Should succeed but report no changes
        assert result.success is True
        assert result.formatter_name == "black"
        assert len(result.files_changed) == 0
        assert result.error_message is None

        # Verify the file content unchanged
        assert test_file.read_text() == original_content

    def test_format_syntax_error_code(
        self, temp_project_dir: Path, syntax_error_code: str
    ) -> None:
        """Test error handling with malformed code (exit 123 → error)."""
        from mcp_coder.formatters.black_formatter import format_with_black

        # Create a Python file with syntax errors
        test_file = temp_project_dir / "broken_module.py"
        test_file.write_text(syntax_error_code)

        # Attempt to format the code
        result = format_with_black(temp_project_dir)

        # Should fail due to syntax errors
        assert result.success is False
        assert result.formatter_name == "black"
        assert len(result.files_changed) == 0
        assert result.error_message is not None
        assert (
            "syntax" in result.error_message.lower()
            or "error" in result.error_message.lower()
        )


class TestBlackFormatterConfiguration:
    """Configuration integration - 2 tests."""

    def test_default_config_missing_pyproject(
        self, temp_project_dir: Path, unformatted_python_code: str
    ) -> None:
        """Test with missing pyproject.toml (use Black defaults)."""
        from mcp_coder.formatters.black_formatter import (
            _get_black_config,
            format_with_black,
        )

        # No pyproject.toml file - should use defaults
        config = _get_black_config(temp_project_dir)

        # Should return default Black configuration
        assert config["line-length"] == 88  # Black default
        assert config["target-version"] == ["py311"]  # Default for current Python

        # Create and format a file to verify it works with defaults
        test_file = temp_project_dir / "test_module.py"
        test_file.write_text(unformatted_python_code)

        result = format_with_black(temp_project_dir)
        assert result.success is True
        assert str(test_file) in result.files_changed

    def test_custom_config_from_pyproject(
        self,
        temp_project_dir: Path,
        unformatted_python_code: str,
        pyproject_toml_with_black_config: str,
    ) -> None:
        """Test with custom line-length and target-version from pyproject.toml."""
        from mcp_coder.formatters.black_formatter import (
            _get_black_config,
            format_with_black,
        )

        # Create pyproject.toml with custom Black config
        pyproject_file = temp_project_dir / "pyproject.toml"
        pyproject_file.write_text(pyproject_toml_with_black_config)

        # Should read custom configuration
        config = _get_black_config(temp_project_dir)
        assert config["line-length"] == 100  # Custom value
        assert config["target-version"] == ["py311"]  # Custom value

        # Create and format a file to verify it works with custom config
        test_file = temp_project_dir / "test_module.py"
        test_file.write_text(unformatted_python_code)

        result = format_with_black(temp_project_dir)
        assert result.success is True
        assert str(test_file) in result.files_changed


class TestBlackFormatterRealWorld:
    """Real-world analysis scenario - 1 test."""

    def test_analysis_code_sample(self, temp_project_dir: Path) -> None:
        """Use actual unformatted code from Step 0 findings to verify patterns."""
        from mcp_coder.formatters.black_formatter import format_with_black

        # Real unformatted code sample similar to what might be analyzed
        analysis_code = """#!/usr/bin/env python3
import subprocess,sys,json
from pathlib import Path

def run_black_check(files):
    cmd=['black','--check']+files
    result=subprocess.run(cmd,capture_output=True,text=True)
    if result.returncode==0:
        return {"status":"no_changes","files":[]}
    elif result.returncode==1:
        return {"status":"changes_needed","files":files}
    else:
        return {"status":"error","message":result.stderr}

def main():
    if len(sys.argv)<2:
        print("Usage: script.py <files>")
        sys.exit(1)
    files=sys.argv[1:]
    result=run_black_check(files)
    print(json.dumps(result,indent=2))

if __name__=="__main__":
    main()
"""

        # Create the analysis code file
        test_file = temp_project_dir / "analysis_script.py"
        test_file.write_text(analysis_code)

        # Format using our Black formatter
        result = format_with_black(temp_project_dir)

        # Should successfully format the code
        assert result.success is True
        assert result.formatter_name == "black"
        assert str(test_file) in result.files_changed
        assert result.error_message is None

        # Verify the code was properly formatted
        formatted_content = test_file.read_text()
        assert formatted_content != analysis_code

        # Check for specific formatting improvements
        assert (
            "import subprocess, sys, json" in formatted_content
        )  # Proper import spacing
        assert "cmd = [" in formatted_content  # Proper assignment spacing
        assert (
            "result.returncode == 0" in formatted_content
        )  # Proper comparison spacing
        assert "if len(sys.argv) < 2:" in formatted_content  # Proper comparison spacing


class TestBlackFormatterUtilities:
    """Test utility functions."""

    def test_get_black_config_function(self, temp_project_dir: Path) -> None:
        """Test the _get_black_config function directly."""
        from mcp_coder.formatters.black_formatter import _get_black_config

        # Test with no config file
        config = _get_black_config(temp_project_dir)
        assert isinstance(config, dict)
        assert "line-length" in config
        assert "target-version" in config

    def test_check_black_changes_function(
        self, temp_project_dir: Path, unformatted_python_code: str
    ) -> None:
        """Test the _check_black_changes function directly."""
        from mcp_coder.formatters.black_formatter import _check_black_changes

        # Create a file that needs formatting
        test_file = temp_project_dir / "test_module.py"
        test_file.write_text(unformatted_python_code)

        # Should detect that changes are needed
        config = {"line-length": 88, "target-version": ["py311"]}
        needs_formatting = _check_black_changes(str(test_file), config)
        assert needs_formatting is True

    def test_apply_black_formatting_function(
        self, temp_project_dir: Path, unformatted_python_code: str
    ) -> None:
        """Test the _apply_black_formatting function directly."""
        from mcp_coder.formatters.black_formatter import _apply_black_formatting

        # Create a file that needs formatting
        test_file = temp_project_dir / "test_module.py"
        test_file.write_text(unformatted_python_code)

        # Apply formatting
        config = {"line-length": 88, "target-version": ["py311"]}
        success = _apply_black_formatting(str(test_file), config)
        assert success is True

        # Verify file was changed
        formatted_content = test_file.read_text()
        assert formatted_content != unformatted_python_code

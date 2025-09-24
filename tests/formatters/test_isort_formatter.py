"""Tests for isort formatter implementation using directory-based TDD approach.

Based on Step 2 requirements: Tests updated to expect directory-based formatting calls,
following the same pattern as the Black formatter refactor.
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
def unsorted_imports_code() -> str:
    """Sample Python code with unsorted imports that needs isort formatting."""
    return """import sys
import os
from pathlib import Path
import json
from typing import Dict, List
import subprocess
from collections import defaultdict
import argparse

def main():
    print("Hello world")
"""


@pytest.fixture
def sorted_imports_code() -> str:
    """Sample Python code with properly sorted imports."""
    return """import argparse
import json
import os
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List


def main():
    print("Hello world")
"""


@pytest.fixture
def import_error_code() -> str:
    """Python code with malformed import syntax that will cause isort to fail."""
    return """import [
from pathlib import
from typing import Dict List syntax error
import sys os invalid
from collections import defaultdict (
"""


@pytest.fixture
def pyproject_toml_with_isort_config() -> str:
    """pyproject.toml content with isort configuration."""
    return """[tool.isort]
profile = "black"
line_length = 100
float_to_top = true
"""


class TestIsortFormatterCore:
    """Core import sorting scenarios - 3 tests."""

    def test_format_unsorted_imports_directory_based(
        self, temp_project_dir: Path, unsorted_imports_code: str, monkeypatch
    ) -> None:
        """Test directory-based isort formatting on imports needing sorting."""
        from mcp_coder.formatters.isort_formatter import format_with_isort
        from mcp_coder.utils.subprocess_runner import CommandResult

        # Create a Python file that needs import sorting
        test_file = temp_project_dir / "test_module.py"
        test_file.write_text(unsorted_imports_code)

        # Mock execute_command to simulate isort directory-based execution
        # Exit code 0 means success, stdout contains "Fixing" messages when changes made
        mock_result = CommandResult(
            return_code=0, stdout=f"Fixing {test_file}\n", stderr="", timed_out=False
        )
        monkeypatch.setattr(
            "mcp_coder.formatters.isort_formatter.execute_command",
            lambda cmd: mock_result,
        )

        # Format the imports using directory-based approach
        result = format_with_isort(temp_project_dir)

        # Should succeed and report the file as changed
        assert result.success is True
        assert result.formatter_name == "isort"
        assert str(test_file) in result.files_changed
        assert result.error_message is None

        # Verify directory-based formatting approach was used
        # (We can't easily verify the exact command with monkeypatch,
        #  but the mock result simulates directory-based execution)

    def test_format_already_sorted_imports_directory_based(
        self, temp_project_dir: Path, sorted_imports_code: str, monkeypatch
    ) -> None:
        """Test directory-based isort on properly sorted imports (exit 0 → no changes)."""
        from mcp_coder.formatters.isort_formatter import format_with_isort
        from mcp_coder.utils.subprocess_runner import CommandResult

        # Create a Python file that is already import-sorted
        test_file = temp_project_dir / "test_module.py"
        test_file.write_text(sorted_imports_code)

        # Mock execute_command to simulate no changes needed
        # Exit code 0 means success with no changes, empty stdout
        mock_result = CommandResult(
            return_code=0, stdout="", stderr="", timed_out=False
        )
        monkeypatch.setattr(
            "mcp_coder.formatters.isort_formatter.execute_command",
            lambda cmd: mock_result,
        )

        # Format the imports using directory-based approach
        result = format_with_isort(temp_project_dir)

        # Should succeed but report no changes
        assert result.success is True
        assert result.formatter_name == "isort"
        assert len(result.files_changed) == 0
        assert result.error_message is None

        # Verify directory-based formatting approach was used
        # (Mock simulates no changes scenario)

    def test_format_error_handling_directory_based(
        self, temp_project_dir: Path, import_error_code: str, monkeypatch
    ) -> None:
        """Test directory-based isort error handling for syntax errors."""
        from mcp_coder.formatters.isort_formatter import format_with_isort
        from mcp_coder.utils.subprocess_runner import CommandResult

        # Create a Python file with problematic import syntax
        test_file = temp_project_dir / "edge_case.py"
        test_file.write_text(import_error_code)

        # Mock execute_command to simulate isort syntax error
        # Exit code 123+ means error, stderr contains error message
        mock_result = CommandResult(
            return_code=123,
            stdout="",
            stderr="ERROR: Could not parse syntax in edge_case.py",
            timed_out=False,
        )
        monkeypatch.setattr(
            "mcp_coder.formatters.isort_formatter.execute_command",
            lambda cmd: mock_result,
        )

        # Attempt to format the imports
        result = format_with_isort(temp_project_dir)

        # Should handle errors gracefully
        assert result.success is False
        assert result.formatter_name == "isort"
        assert result.error_message is not None
        assert "ERROR: Could not parse syntax" in result.error_message
        assert len(result.files_changed) == 0


class TestIsortFormatterConfiguration:
    """Configuration integration - 2 tests."""

    def test_default_config_missing_pyproject(
        self, temp_project_dir: Path, unsorted_imports_code: str, monkeypatch
    ) -> None:
        """Test directory-based formatting with missing pyproject.toml (use isort defaults)."""
        from mcp_coder.formatters.isort_formatter import (
            _get_isort_config,
            format_with_isort,
        )
        from mcp_coder.utils.subprocess_runner import CommandResult

        # No pyproject.toml file - should use defaults
        config = _get_isort_config(temp_project_dir)

        # Should return default isort configuration
        assert config["profile"] == "black"  # isort default compatibility
        assert config["line_length"] == 88  # Black profile default
        assert config["float_to_top"] is True  # isort default

        # Create and format a file to verify it works with defaults
        test_file = temp_project_dir / "test_module.py"
        test_file.write_text(unsorted_imports_code)

        # Mock execute_command for directory-based execution
        mock_result = CommandResult(
            return_code=0, stdout=f"Fixing {test_file}\n", stderr="", timed_out=False
        )
        monkeypatch.setattr(
            "mcp_coder.formatters.isort_formatter.execute_command",
            lambda cmd: mock_result,
        )

        result = format_with_isort(temp_project_dir)
        assert result.success is True
        assert str(test_file) in result.files_changed

        # Verify directory-based formatting with default config was used
        # (Mock simulates successful execution with default config)

    def test_custom_config_from_pyproject(
        self,
        temp_project_dir: Path,
        unsorted_imports_code: str,
        pyproject_toml_with_isort_config: str,
        monkeypatch,
    ) -> None:
        """Test directory-based formatting with Black compatibility and custom line_length from pyproject.toml."""
        from mcp_coder.formatters.isort_formatter import (
            _get_isort_config,
            format_with_isort,
        )
        from mcp_coder.utils.subprocess_runner import CommandResult

        # Create pyproject.toml with custom isort config
        pyproject_file = temp_project_dir / "pyproject.toml"
        pyproject_file.write_text(pyproject_toml_with_isort_config)

        # Should read custom configuration
        config = _get_isort_config(temp_project_dir)
        assert config["profile"] == "black"  # Custom value
        assert config["line_length"] == 100  # Custom value
        assert config["float_to_top"] is True  # Custom value

        # Create and format a file to verify it works with custom config
        test_file = temp_project_dir / "test_module.py"
        test_file.write_text(unsorted_imports_code)

        # Mock execute_command for directory-based execution
        mock_result = CommandResult(
            return_code=0, stdout=f"Fixing {test_file}\n", stderr="", timed_out=False
        )
        monkeypatch.setattr(
            "mcp_coder.formatters.isort_formatter.execute_command",
            lambda cmd: mock_result,
        )

        result = format_with_isort(temp_project_dir)
        assert result.success is True
        assert str(test_file) in result.files_changed

        # Verify directory-based formatting with custom config was used
        # (Mock simulates successful execution with custom config)


class TestIsortFormatterRealWorld:
    """Real-world analysis scenario - 1 test."""

    def test_analysis_import_sample_directory_based(
        self, temp_project_dir: Path, monkeypatch
    ) -> None:
        """Test directory-based formatting with actual unsorted imports from Step 0 findings."""
        from mcp_coder.formatters.isort_formatter import format_with_isort
        from mcp_coder.utils.subprocess_runner import CommandResult

        # Real unformatted import sample similar to what might be analyzed
        analysis_imports = """#!/usr/bin/env python3
import subprocess,sys,json
from pathlib import Path
import tempfile
import os
from typing import Dict,List,Optional
import logging
from dataclasses import dataclass
import argparse

@dataclass
class AnalysisResult:
    status: str
    files: List[str]

def run_isort_check(files: List[str]) -> Dict[str, any]:
    cmd=['isort','--check-only'] + files
    result=subprocess.run(cmd,capture_output=True,text=True)
    if result.returncode==0:
        return {"status":"no_changes","files":[]}
    elif result.returncode==1:
        return {"status":"changes_needed","files":files}
    else:
        return {"status":"error","message":result.stderr}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("files", nargs="+")
    args = parser.parse_args()
    
    result = run_isort_check(args.files)
    print(json.dumps(result, indent=2))

if __name__=="__main__":
    main()
"""

        # Create the analysis imports file
        test_file = temp_project_dir / "analysis_imports.py"
        test_file.write_text(analysis_imports)

        # Mock execute_command for directory-based execution
        mock_result = CommandResult(
            return_code=0, stdout=f"Fixing {test_file}\n", stderr="", timed_out=False
        )
        monkeypatch.setattr(
            "mcp_coder.formatters.isort_formatter.execute_command",
            lambda cmd: mock_result,
        )

        # Format using directory-based isort formatter
        result = format_with_isort(temp_project_dir)

        # Should successfully format the imports
        assert result.success is True
        assert result.formatter_name == "isort"
        assert str(test_file) in result.files_changed
        assert result.error_message is None

        # Verify directory-based formatting was used successfully
        # (Mock simulates successful directory-based execution)


class TestIsortFormatterUtilities:
    """Test utility functions for directory-based approach."""

    def test_get_isort_config_function(self, temp_project_dir: Path) -> None:
        """Test the _get_isort_config function directly."""
        from mcp_coder.formatters.isort_formatter import _get_isort_config

        # Test with no config file
        config = _get_isort_config(temp_project_dir)
        assert isinstance(config, dict)
        assert "profile" in config
        assert "line_length" in config
        assert "float_to_top" in config

    def test_parse_isort_output_function(self) -> None:
        """Test the _parse_isort_output function with various output formats."""
        from mcp_coder.formatters.isort_formatter import _parse_isort_output

        # Test with no changes (empty output)
        assert _parse_isort_output("") == []
        assert _parse_isort_output("\n") == []

        # Test with single file change
        output_single = "Fixing /path/to/file.py\n"
        result_single = _parse_isort_output(output_single)
        assert result_single == ["/path/to/file.py"]

        # Test with multiple file changes
        output_multiple = """Fixing /path/to/file1.py
Fixing /path/to/file2.py
Fixing /path/with spaces/file3.py
"""
        result_multiple = _parse_isort_output(output_multiple)
        assert result_multiple == [
            "/path/to/file1.py",
            "/path/to/file2.py",
            "/path/with spaces/file3.py",
        ]

        # Test with mixed output (only "Fixing" lines should be parsed)
        output_mixed = """Skipped 1 files
Fixing /path/to/changed.py
Processing file.py
"""
        result_mixed = _parse_isort_output(output_mixed)
        assert result_mixed == ["/path/to/changed.py"]

    def test_format_isort_directory_function(
        self, temp_project_dir: Path, monkeypatch
    ) -> None:
        """Test the _format_isort_directory function directly."""
        from mcp_coder.formatters.isort_formatter import _format_isort_directory
        from mcp_coder.utils.subprocess_runner import CommandResult

        # Create test file
        test_file = temp_project_dir / "test_module.py"
        test_file.write_text("import os\nimport sys\n")

        # Mock execute_command for directory formatting
        mock_result = CommandResult(
            return_code=0, stdout=f"Fixing {test_file}\n", stderr="", timed_out=False
        )
        monkeypatch.setattr(
            "mcp_coder.formatters.isort_formatter.execute_command",
            lambda cmd: mock_result,
        )

        # Test directory formatting
        config = {"profile": "black", "line_length": 88, "float_to_top": True}
        changed_files = _format_isort_directory(temp_project_dir, config)

        # Should return list of changed files from parsed output
        assert changed_files == [str(test_file)]

        # Verify function returned correct list of changed files
        # (Mock simulates directory-based execution)
